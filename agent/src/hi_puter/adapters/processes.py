"""Closing applications by spoken name, the same way on Linux and Windows."""

import os
import re
from collections.abc import Iterable
from pathlib import Path

import psutil

from hi_puter.core.errors import ActionError

# Never closed by voice: the desktop itself, audio, the model server, and Hi-Puter's tools.
PROTECTED = frozenset(
    {
        "systemd", "init", "dbus-daemon", "dbus-broker", "gnome-shell", "gnome-session-binary",
        "xwayland", "xorg", "kwin_wayland", "kwin_x11", "plasmashell", "pipewire",
        "pipewire-pulse", "wireplumber", "pulseaudio", "ollama", "llama-server", "sshd", "sudo",
        "login", "polkitd", "explorer.exe", "dwm.exe", "csrss.exe", "winlogon.exe",
    }
)  # fmt: skip
# Desktop and system service families, protected by prefix (gnome-shell-calendar-server, ...).
PROTECTED_PREFIXES = (
    "gnome-shell", "gnome-session", "xdg-", "at-spi", "dbus-", "systemd", "pipewire", "ibus-",
)  # fmt: skip
FILLER = frozenset({"the", "a", "my", "app", "application", "program", "window", "browser"})
MIN_WORD = 3  # single words shorter than this ("vs") are too vague to match on
MIN_PREFIX = 4  # "chrome" may match "chrome_crashpad", but "co" must not match "code"


def process_names(spoken: str, executables: Iterable[str] = ()) -> set[str]:
    """Process names a spoken app name might run as: "chrome browser" -> {"chrome", ...}."""
    words = [word for word in re.findall(r"[a-z0-9]+", spoken.lower()) if word not in FILLER]
    names = {Path(exe).name.lower() for exe in executables if exe}
    if words:
        names |= {
            "".join(words),
            "-".join(words),
            *[word for word in words if len(word) >= MIN_WORD],
        }
    return {name.removesuffix(".exe") for name in names if name}


def _matches(process: psutil.Process, names: set[str]) -> bool:
    try:
        name = process.name().lower().removesuffix(".exe")
        exe = Path(process.exe() or "").name.lower().removesuffix(".exe")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    if {name, exe} & PROTECTED or name.startswith(PROTECTED_PREFIXES):
        return False
    return any(
        candidate in {name, exe}
        or (
            len(candidate) >= MIN_PREFIX
            and (name.startswith(candidate) or exe.startswith(candidate))
        )
        for candidate in names
    )


def find_app_processes(names: set[str]) -> list[psutil.Process]:
    """Top-level processes of the user's own apps that match `names`."""
    names = {name for name in names if name not in PROTECTED}
    if not names:
        return []
    me = psutil.Process()
    own_chain = {me.pid} | {parent.pid for parent in me.parents()}  # never close our own terminal
    uid = os.getuid() if hasattr(os, "getuid") else None
    found: dict[int, psutil.Process] = {}
    for process in psutil.process_iter():
        try:
            if process.pid in own_chain or process.pid <= 1:
                continue
            if uid is not None and process.uids().real != uid:
                continue
            if "hi_puter" in " ".join(process.cmdline()):
                continue
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        if _matches(process, names):
            found[process.pid] = process
    # Ask only the top of each app's process tree to quit; its helpers exit with it.
    roots = []
    for process in found.values():
        try:
            if process.ppid() not in found:
                roots.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return roots


def close_app(spoken: str, executables: Iterable[str] = ()) -> int:
    """Ask a running app to quit (like closing its window). Returns how many were asked."""
    names = process_names(spoken, executables)
    if not names:
        raise ActionError("Which app should I close?")
    processes = find_app_processes(names)
    for process in processes:
        try:
            process.terminate()  # a normal quit request, never a forced kill
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    psutil.wait_procs(processes, timeout=3)
    return len(processes)
