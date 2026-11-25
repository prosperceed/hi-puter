from collections import deque


class RingBuffer:
    def __init__(self, max_frames: int = 67) -> None:
        self._frames: deque[bytes] = deque(maxlen=max_frames)

    def append(self, frame: bytes) -> None:
        self._frames.append(bytes(frame))

    def snapshot(self) -> list[bytes]:
        return list(self._frames)
