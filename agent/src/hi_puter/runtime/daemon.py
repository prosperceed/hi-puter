from threading import Event
import signal
import time

from hi_puter.core.paths import get_paths


def main() -> None:
    stop = Event()
    def handler(_signum: int, _frame: object) -> None: stop.set()
    signal.signal(signal.SIGTERM, handler); signal.signal(signal.SIGINT, handler)
    paths = get_paths(); paths.ensure()
    try:
        while not stop.wait(0.5): pass
    finally:
        paths.pid_file.unlink(missing_ok=True)


if __name__ == "__main__": main()
