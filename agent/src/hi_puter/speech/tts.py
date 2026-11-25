import logging
import shutil
import subprocess
import sys
from typing import Protocol

log = logging.getLogger("hi_puter")


class Synthesizer(Protocol):
    def speak(self, text: str) -> None: ...
    def close(self) -> None: ...


class EspeakSynthesizer:
    """espeak-ng through its CLI. Text goes over stdin, so it is never parsed as options."""

    def __init__(self, rate: int = 175, voice: str | None = None) -> None:
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        if binary is None:
            raise RuntimeError("espeak-ng is not installed")
        self._argv = [binary, "-s", str(rate)] + (["-v", voice] if voice else [])

    def speak(self, text: str) -> None:
        if text.strip():
            subprocess.run(
                self._argv, input=text, text=True, check=False, timeout=60, capture_output=True
            )

    def close(self) -> None:
        return None


class PyttsxSynthesizer:
    """pyttsx3: SAPI5 on Windows, NSSpeech on macOS, espeak on Linux."""

    def __init__(self, rate: int = 175, voice: str | None = None) -> None:
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        if voice:
            self._engine.setProperty("voice", voice)

    def speak(self, text: str) -> None:
        if text.strip():
            self._engine.say(text)
            self._engine.runAndWait()

    def close(self) -> None:
        self._engine.stop()


class ConsoleSynthesizer:
    """Prints replies instead of speaking them (text mode and missing voices)."""

    def __init__(self, label: str = "Hi-Puter") -> None:
        self._label = label

    def speak(self, text: str) -> None:
        if text.strip():
            print(f"{self._label}: {text}", flush=True)

    def close(self) -> None:
        return None


def make_synthesizer(
    engine: str = "auto", rate: int = 175, voice: str | None = None
) -> Synthesizer:
    order = {
        "auto": ["pyttsx3", "espeak"] if sys.platform == "win32" else ["espeak", "pyttsx3"],
        "espeak": ["espeak"],
        "pyttsx3": ["pyttsx3"],
        "console": [],
    }[engine]
    for choice in order:
        try:
            return (
                EspeakSynthesizer(rate, voice)
                if choice == "espeak"
                else PyttsxSynthesizer(rate, voice)
            )
        except Exception as exc:  # missing package, driver or binary
            log.info("TTS engine %s unavailable: %s", choice, exc)
    if engine != "console":
        log.warning("No speech engine available; replies will be printed instead.")
    return ConsoleSynthesizer()
