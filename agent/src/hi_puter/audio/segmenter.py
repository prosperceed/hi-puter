from collections import deque

FRAME_MS = 30  # 480 samples at 16 kHz, the frame size webrtcvad expects


class UtteranceSegmenter:
    """Groups voice-activity-labelled frames into whole utterances.

    Speech starts when most of the last few frames are voiced; a short pre-roll is kept so the
    first syllable is not clipped. The utterance ends after `end_silence_ms` of silence or at
    `max_seconds`. Very short bursts (coughs, clicks) are dropped.
    """

    def __init__(
        self,
        *,
        end_silence_ms: int = 700,
        max_seconds: float = 12.0,
        preroll_ms: int = 300,
        min_speech_ms: int = 240,
        start_window: int = 5,
        start_voiced: int = 3,
    ) -> None:
        self._end_frames = max(1, end_silence_ms // FRAME_MS)
        self._max_frames = max(1, int(max_seconds * 1000 / FRAME_MS))
        self._min_voiced = max(1, min_speech_ms // FRAME_MS)
        self._start_voiced = start_voiced
        self._preroll: deque[tuple[bytes, bool]] = deque(
            maxlen=max(start_window, preroll_ms // FRAME_MS)
        )
        self._window: deque[bool] = deque(maxlen=start_window)
        self._frames: list[bytes] = []
        self._silence = 0
        self._voiced = 0

    @property
    def in_speech(self) -> bool:
        return bool(self._frames)

    def reset(self) -> None:
        self._preroll.clear()
        self._window.clear()
        self._frames = []
        self._silence = 0
        self._voiced = 0

    def push(self, frame: bytes, is_speech: bool) -> bytes | None:
        """Add one frame; returns the finished utterance's PCM bytes when one ends."""
        if not self._frames:
            self._preroll.append((frame, is_speech))
            self._window.append(is_speech)
            if sum(self._window) < self._start_voiced:
                return None
            self._frames = [item for item, _ in self._preroll]
            self._voiced = sum(1 for _, voiced in self._preroll if voiced)
            self._preroll.clear()
            self._window.clear()
            return None
        self._frames.append(frame)
        if is_speech:
            self._voiced += 1
            self._silence = 0
        else:
            self._silence += 1
        if self._silence < self._end_frames and len(self._frames) < self._max_frames:
            return None
        audio, voiced = b"".join(self._frames), self._voiced
        self.reset()
        return audio if voiced >= self._min_voiced else None
