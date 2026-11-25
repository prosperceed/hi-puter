import importlib.util
import shutil
import sys

import typer

from hi_puter.core.config import Config, load_config
from hi_puter.core.paths import get_paths

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def command() -> None:
    """Check the local Hi-Puter installation."""
    paths = get_paths()
    paths.ensure()
    results: list[tuple[str, str, str]] = [
        (PASS if sys.version_info >= (3, 10) else FAIL, "Python", sys.version.split()[0]),
    ]
    config = Config()
    try:
        config = load_config(paths.config_file)
        results.append((PASS, "Config", str(paths.config_file)))
    except Exception as exc:
        results.append((FAIL, "Config", str(exc)))

    missing = [
        name for name in ("sounddevice", "webrtcvad", "faster_whisper", "numpy") if not _has(name)
    ]
    results.append(
        (FAIL, "Speech packages", f"missing {', '.join(missing)}; pip install -e '.[audio,speech]'")
        if missing
        else (PASS, "Speech packages", "sounddevice, webrtcvad, faster-whisper")
    )
    results.append(_microphones())
    results.append(_voice(config))
    results.extend(_model(config))

    for status, label, detail in results:
        typer.echo(f"{status:<5} {label:<16} {detail}")
    if any(status == FAIL for status, _, _ in results):
        raise typer.Exit(1)


def _microphones() -> tuple[str, str, str]:
    if not _has("sounddevice"):
        return (WARN, "Microphone", "sounddevice not installed")
    try:
        from hi_puter.audio.devices import list_input_devices

        devices = list_input_devices()
    except Exception as exc:
        return (FAIL, "Microphone", f"cannot list devices: {exc}")
    if not devices:
        return (FAIL, "Microphone", "no input devices found")
    return (PASS, "Microphone", f"{len(devices)} input device(s), e.g. {devices[0]}")


def _voice(config: Config) -> tuple[str, str, str]:
    if config.tts.engine == "console":
        return (WARN, "Voice", "tts.engine = console (replies are printed, not spoken)")
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return (PASS, "Voice", "espeak-ng")
    if _has("pyttsx3"):
        return (PASS, "Voice", "pyttsx3")
    return (WARN, "Voice", "no speech engine; install espeak-ng or pip install pyttsx3")


def _model(config: Config) -> list[tuple[str, str, str]]:
    if not config.llm.enabled:
        return [(WARN, "Language model", "disabled; only simple commands work")]
    from hi_puter.core.errors import ModelError
    from hi_puter.runtime.assemble import make_model

    model = make_model(config)
    if model is None:
        return [(WARN, "Language model", "disabled")]
    version = model.version()
    if version is None:
        return [
            (
                FAIL,
                "Ollama",
                f"not reachable at {config.llm.host}; install from https://ollama.com and start it",
            )
        ]
    try:
        pulled = model.has_model()
    except ModelError as exc:
        return [(PASS, "Ollama", f"version {version}"), (FAIL, "Language model", str(exc))]
    return [
        (PASS, "Ollama", f"version {version} at {config.llm.host}"),
        (PASS, "Language model", config.llm.model)
        if pulled
        else (
            FAIL,
            "Language model",
            f"{config.llm.model} not downloaded; run: ollama pull {config.llm.model}",
        ),
    ]
