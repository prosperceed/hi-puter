"""System libraries Hi-Puter needs on Linux, which pip cannot install.

PortAudio lets the microphone work (sounddevice loads the system library on Linux), and
espeak-ng gives Hi-Puter its voice. Both come from the distribution's package manager.
"""

import ctypes.util
import shutil
import sys
from collections.abc import Callable

Which = Callable[[str], str | None]

# What each library is called by each package manager.
PACKAGE_NAMES: dict[str, dict[str, str]] = {
    "apt-get": {"PortAudio": "libportaudio2", "espeak-ng": "espeak-ng"},
    "dnf": {"PortAudio": "portaudio", "espeak-ng": "espeak-ng"},
    "pacman": {"PortAudio": "portaudio", "espeak-ng": "espeak-ng"},
    "zypper": {"PortAudio": "libportaudio2", "espeak-ng": "espeak-ng"},
}
INSTALL_ARGS: dict[str, list[str]] = {
    "apt-get": ["install", "-y"],
    "dnf": ["install", "-y"],
    "pacman": ["-S", "--needed", "--noconfirm"],
    "zypper": ["install", "-y"],
}
WHY = {
    "PortAudio": "lets Hi-Puter use your microphone",
    "espeak-ng": "gives Hi-Puter a voice to answer with",
}


def missing_libraries(
    which: Which = shutil.which,
    find_library: Callable[[str], str | None] = ctypes.util.find_library,
    platform: str = sys.platform,
) -> list[str]:
    """Names of the system libraries that still need installing (Linux only)."""
    if not platform.startswith("linux"):
        return []  # Windows and macOS builds of sounddevice bundle PortAudio
    missing = []
    if find_library("portaudio") is None:
        missing.append("PortAudio")
    if which("espeak-ng") is None and which("espeak") is None:
        missing.append("espeak-ng")
    return missing


def package_manager(which: Which = shutil.which) -> str | None:
    return next((manager for manager in PACKAGE_NAMES if which(manager)), None)


def install_command(missing: list[str], which: Which = shutil.which) -> list[str] | None:
    """The command that installs `missing`, or None if the package manager is unknown."""
    manager = package_manager(which)
    if manager is None or not missing:
        return None
    packages = [PACKAGE_NAMES[manager][library] for library in missing]
    return ["sudo", manager, *INSTALL_ARGS[manager], *packages]
