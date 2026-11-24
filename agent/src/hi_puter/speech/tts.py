from typing import Protocol


class Synthesizer(Protocol):
    def speak(self, text: str) -> None: ...
    def close(self) -> None: ...


class PyttsxSynthesizer:
    def __init__(self, rate: int = 175, voice: str | None = None) -> None:
        import pyttsx3
        self._engine = pyttsx3.init(); self._engine.setProperty("rate", rate)
        if voice: self._engine.setProperty("voice", voice)
    def speak(self, text: str) -> None: self._engine.say(text); self._engine.runAndWait()
    def close(self) -> None: self._engine.stop()
