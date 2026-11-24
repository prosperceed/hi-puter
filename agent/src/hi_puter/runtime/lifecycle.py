from pathlib import Path
import os
import signal
import subprocess
import sys
import time

import psutil

from hi_puter.core.errors import LifecycleError


def _identity(pid: int) -> bool:
    try: return "hi_puter" in " ".join(psutil.Process(pid).cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied): return False


def is_running(pid_file: Path) -> bool:
    try: pid = int(pid_file.read_text().strip())
    except (OSError, ValueError): return False
    return psutil.pid_exists(pid) and _identity(pid)


def start(pid_file: Path, foreground: bool = False) -> int:
    if is_running(pid_file): raise LifecycleError("Hi-Puter is already running.")
    pid_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    kwargs: dict[str, object] = {}
    if not foreground and os.name != "nt": kwargs["start_new_session"] = True
    process = subprocess.Popen([sys.executable, "-m", "hi_puter.runtime.daemon"], stdout=None if foreground else subprocess.DEVNULL, stderr=None if foreground else subprocess.DEVNULL, **kwargs)
    pid_file.write_text(str(process.pid)); os.chmod(pid_file, 0o600)
    return process.pid


def stop(pid_file: Path) -> None:
    try: pid = int(pid_file.read_text().strip())
    except (OSError, ValueError): raise LifecycleError("Hi-Puter is not running.")
    if not _identity(pid):
        pid_file.unlink(missing_ok=True); raise LifecycleError("Refused to signal an unverified process.")
    process = psutil.Process(pid); process.terminate()
    try: process.wait(5)
    except psutil.TimeoutExpired:
        process.kill(); process.wait(2)
    pid_file.unlink(missing_ok=True)
