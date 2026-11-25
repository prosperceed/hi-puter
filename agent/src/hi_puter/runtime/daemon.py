import logging
import signal
import sys
import time
from threading import Event, Thread

from hi_puter.adapters.factory import get_adapter
from hi_puter.brain.assistant import Assistant
from hi_puter.brain.llm import LOAD_TIMEOUT_SECONDS
from hi_puter.core.config import Config, load_config
from hi_puter.core.errors import ActionError, AudioError, ConfigError, ModelError
from hi_puter.core.logging import configure_logging
from hi_puter.core.paths import get_paths
from hi_puter.runtime.assemble import build_assistant

SPEECH_MISSING = "Speech packages are missing. Install them with: pip install -e '.[audio,speech]'"
MIC_MISSING = "Microphone is unavailable. Check the input device (hi-puter doctor lists them)."


def _warm_model(assistant: Assistant, config: Config, log: logging.Logger) -> None:
    if assistant.model is None:
        log.info("Language model disabled; only simple commands are available.")
        return
    started = time.monotonic()
    try:
        assistant.prime(timeout=LOAD_TIMEOUT_SECONDS)
        log.info(
            "Language model %s is ready (%.0fs).", config.llm.model, time.monotonic() - started
        )
    except ModelError as exc:
        log.warning("%s Simple commands still work.", exc)


def _unload_model(assistant: Assistant, log: logging.Logger) -> None:
    unload = getattr(assistant.model, "unload", None)
    if unload is None:
        return
    try:
        unload()
        log.info("Language model unloaded.")
    except ModelError as exc:
        log.info("Could not unload the language model: %s", exc)


def main() -> None:
    stop = Event()

    def handler(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    paths = get_paths()
    paths.ensure()
    log = configure_logging(paths.log_file, foreground=sys.stderr.isatty())
    try:
        config = load_config(paths.config_file)
        assistant = build_assistant(config, paths, get_adapter())
        Thread(target=_warm_model, args=(assistant, config, log), daemon=True).start()
        try:
            from hi_puter.audio.cue import play_listening_cue
            from hi_puter.audio.listener import MicListener
            from hi_puter.speech.stt import WhisperTranscriber
        except ImportError as exc:
            raise AudioError(SPEECH_MISSING) from exc
        from hi_puter.runtime.voice_loop import VoiceLoop
        from hi_puter.speech.tts import make_synthesizer

        log.info("Loading speech recognition model %s", config.stt.model)
        try:
            stt = WhisperTranscriber(
                config.stt.model, config.stt.compute_type, hint=config.wake.name
            )
        except ImportError as exc:
            raise AudioError(SPEECH_MISSING) from exc
        tts = make_synthesizer(config.tts.engine, config.tts.rate, config.tts.voice)
        try:
            listener = MicListener(
                stop,
                device=config.audio.device,
                vad_aggressiveness=config.audio.vad_aggressiveness,
                end_silence_ms=config.voice.end_silence_ms,
                max_seconds=config.audio.max_command_seconds,
            )
        except ImportError as exc:
            raise AudioError(SPEECH_MISSING) from exc
        except (OSError, RuntimeError) as exc:
            raise AudioError(MIC_MISSING) from exc
        loop = VoiceLoop(
            source=listener,
            stt=stt,
            tts=tts,
            assistant=assistant,
            wake_name=config.wake.name,
            wake_threshold=config.wake.threshold,
            voice=config.voice,
            stop=stop,
            chime=play_listening_cue,
            log_transcripts=config.logging.log_transcripts,
        )
        with listener:
            loop.run()
        tts.close()
        _unload_model(assistant, log)
    except (AudioError, ConfigError, ActionError) as exc:
        log.error("%s", exc)
        print(f"Hi-Puter: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        paths.pid_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
