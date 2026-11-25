import sys

from hi_puter.adapters.base import SystemAdapter
from hi_puter.core.errors import ActionError


def get_adapter() -> SystemAdapter:
    if sys.platform == "win32":
        from hi_puter.adapters.windows.adapter import WindowsAdapter

        return WindowsAdapter()
    if sys.platform.startswith("linux"):
        from hi_puter.adapters.linux.adapter import LinuxAdapter

        return LinuxAdapter()
    raise ActionError(f"Unsupported platform: {sys.platform}")
