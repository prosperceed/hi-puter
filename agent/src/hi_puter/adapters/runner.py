import os
import subprocess
from collections.abc import Sequence

from hi_puter.core.errors import ActionError


def run(argv: Sequence[str], timeout: float = 5) -> subprocess.CompletedProcess[str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "PATH",
            "HOME",
            "DISPLAY",
            "WAYLAND_DISPLAY",
            "XDG_RUNTIME_DIR",
            "DBUS_SESSION_BUS_ADDRESS",
            "XDG_SESSION_TYPE",
            "LANG",
        }
    }
    try:
        return subprocess.run(
            list(argv),
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActionError(f"Command failed: {argv[0]}") from exc
