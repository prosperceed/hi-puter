from queue import Full, Queue


class CaptureQueue:
    def __init__(self, maxsize: int = 200) -> None: self.frames: Queue[bytes] = Queue(maxsize=maxsize); self.dropped = 0
    def push(self, frame: bytes) -> None:
        try: self.frames.put_nowait(bytes(frame))
        except Full:
            self.frames.get_nowait(); self.frames.put_nowait(bytes(frame)); self.dropped += 1


def open_stream(queue: CaptureQueue, device: str | int | None = None) -> object:
    import sounddevice
    return sounddevice.RawInputStream(samplerate=16_000, channels=1, dtype="int16", blocksize=480, device=device, callback=lambda data, _frames, _time, _status: queue.push(bytes(data)))
