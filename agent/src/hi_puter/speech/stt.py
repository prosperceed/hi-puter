from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class WhisperTranscriber:
    def __init__(self, model: str = "tiny.en", compute_type: str = "int8") -> None:
        from faster_whisper import WhisperModel
        self._model = WhisperModel(model, device="cpu", compute_type=compute_type)
    def transcribe(self, audio: bytes) -> str:
        segments, _ = self._model.transcribe(audio, language="en", beam_size=1, vad_filter=False)
        return " ".join(segment.text for segment in segments).strip()
