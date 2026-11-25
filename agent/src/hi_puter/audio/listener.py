from queue import Empty
from threading import Event
from time import monotonic
from typing import Any, Protocol

from hi_puter.audio.capture import CaptureQueue, open_stream
from hi_puter.audio.segmenter import UtteranceSegmenter
from hi_puter.audio.vad import VoiceActivityDetector


class UtteranceSource(Protocol):
    def next_utterance(self, start_timeout: float | None = None) -> bytes | None:
        """Block until someone finishes speaking.

        Returns None when stopped, or when `start_timeout` seconds pass without speech starting.
        """
        ...

    def flush(self) -> None:
        """Drop audio captured so far (e.g. the assistant's own voice)."""
        ...


class MicListener:
    """Microphone -> 30 ms frames -> voice activity detection -> whole utterances."""

    def __init__(
        self,
        stop: Event,
        *,
        device: str | int | None = None,
        vad_aggressiveness: int = 2,
        end_silence_ms: int = 700,
        max_seconds: float = 12.0,
    ) -> None:
        self._stop = stop
        self._queue = CaptureQueue()
        self._vad = VoiceActivityDetector(vad_aggressiveness)
        self._segmenter = UtteranceSegmenter(end_silence_ms=end_silence_ms, max_seconds=max_seconds)
        self._stream: Any = open_stream(self._queue, device)

    def __enter__(self) -> "MicListener":
        self._stream.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._stream.stop()
        self._stream.close()

    def next_utterance(self, start_timeout: float | None = None) -> bytes | None:
        started = monotonic()
        while not self._stop.is_set():
            if (
                start_timeout is not None
                and not self._segmenter.in_speech
                and monotonic() - started > start_timeout
            ):
                return None
            try:
                frame = self._queue.frames.get(timeout=0.1)
            except Empty:
                continue
            utterance = self._segmenter.push(frame, self._vad.is_speech(frame))
            if utterance is not None:
                return utterance
        return None

    def flush(self) -> None:
        while True:
            try:
                self._queue.frames.get_nowait()
            except Empty:
                break
        self._segmenter.reset()
