import re
from typing import Protocol

# Phrases Whisper tends to invent from background noise.
HALLUCINATIONS = frozenset(
    {"", "you", "thank you", "thanks for watching", "thank you for watching", "bye"}
)


class Transcriber(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class WhisperTranscriber:
    """faster-whisper on the CPU. `audio` is 16 kHz mono signed 16-bit PCM."""

    def __init__(self, model: str = "base.en", compute_type: str = "int8", hint: str = "") -> None:
        from faster_whisper import WhisperModel

        from hi_puter.onboarding.speech_setup import use_plain_downloads

        use_plain_downloads()  # a first start downloads the model; avoid Xet stalls
        self._model = WhisperModel(model, device="cpu", compute_type=compute_type)
        self._language = "en" if model.endswith(".en") else None
        # Priming with the wake name and command words makes Whisper spell them the way we expect.
        # Wording chosen by testing: the name must lead, or "Hey Nova" is misheard.
        name = hint.title() if hint else "Hi-Puter"
        self._prompt = f"{name}. Hey {name}, open Firefox, set the volume, mute, take a screenshot."

    def transcribe(self, audio: bytes) -> str:
        import numpy as np

        samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self._model.transcribe(
            samples,
            language=self._language,
            beam_size=1,
            vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt=self._prompt,
        )
        text = " ".join(segment.text for segment in segments).strip()
        return "" if is_noise(text) else text


def is_noise(text: str) -> bool:
    return re.sub(r"[^a-z ]", "", text.lower()).strip() in HALLUCINATIONS
