from threading import Event
import signal
import sys

from hi_puter.audio.capture import CaptureQueue, open_stream
from hi_puter.core.config import load_config
from hi_puter.core.errors import AudioError, ConfigError
from hi_puter.core.paths import get_paths


def main() -> None:
    stop = Event()
    def handler(_signum: int, _frame: object) -> None: stop.set()
    signal.signal(signal.SIGTERM, handler); signal.signal(signal.SIGINT, handler)
    paths = get_paths(); paths.ensure()
    stream = None
    try:
        config = load_config(paths.config_file)
        queue = CaptureQueue()
        try:
            stream = open_stream(queue, config.audio.device)
            stream.start()
        except (ImportError, OSError, RuntimeError) as exc:
            raise AudioError("Microphone is unavailable. Install the audio extra and check the input device.") from exc
        while not stop.wait(0.5): pass
    except (AudioError, ConfigError) as exc:
        print(f"Hi-Puter: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        if stream is not None:
            stream.stop(); stream.close()
        paths.pid_file.unlink(missing_ok=True)


if __name__ == "__main__": main()
