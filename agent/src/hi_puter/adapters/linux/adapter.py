import logging
import re
import shutil
import subprocess
import webbrowser
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from hi_puter.adapters import processes
from hi_puter.adapters.linux import mpris, screen
from hi_puter.adapters.runner import run
from hi_puter.core.errors import ActionError

SINK = "@DEFAULT_AUDIO_SINK@"
log = logging.getLogger("hi_puter")


class LinuxAdapter:
    def __init__(self) -> None:
        self._recorder = screen.ScreenRecorder()

    def capabilities(self) -> frozenset[str]:
        return frozenset(
            {"volume", "lock", "screenshot", "recording", "apps", "web", "power", "media", "files"}
        )

    def volume_get(self) -> int:
        output = run(["wpctl", "get-volume", SINK]).stdout  # "Volume: 0.40"
        found = re.search(r"([\d.]+)", output)
        return round(float(found.group(1)) * 100) if found else 0

    def volume_set(self, level: int) -> None:
        run(["wpctl", "set-volume", SINK, f"{max(0, min(100, level))}%"])

    def volume_change(self, delta: int) -> None:
        sign = "+" if delta >= 0 else "-"
        run(["wpctl", "set-volume", "-l", "1.0", SINK, f"{abs(delta)}%{sign}"])

    def set_mute(self, muted: bool) -> None:
        run(["wpctl", "set-mute", SINK, "1" if muted else "0"])

    def lock(self) -> None:
        run(["loginctl", "lock-session"])

    def screenshot(self, interactive: bool = False) -> Path | None:
        """Save a full-screen capture, or open the screenshot tool (returns None)."""
        if not interactive:
            try:
                path = screen.portal_screenshot(interactive=False, timeout=15)
            except ActionError as exc:
                log.info("Portal screenshot unavailable: %s", exc)
                path = None
            if path is not None:
                return path
            path = _screenshot_with_cli()
            if path is not None:
                return path
        # Silent capture refused or unavailable: let the user pick what to capture.
        screen.open_screenshot_tool()
        return None

    def start_recording(self, seconds: float | None) -> Path:
        return self._recorder.start(seconds)

    def stop_recording(self) -> Path | None:
        return self._recorder.stop()

    def open_path(self, path: Path) -> None:
        opener = shutil.which("gio") or shutil.which("xdg-open")
        if opener is None:
            raise ActionError("No program to open files with (install xdg-utils).")
        argv = [opener, "open", str(path)] if opener.endswith("gio") else [opener, str(path)]
        subprocess.Popen(
            argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )

    def open_app(self, name: str) -> None:
        for desktop_id in _desktop_ids(name):
            try:
                run(["gtk-launch", desktop_id])
                return
            except ActionError:
                continue
        binary = shutil.which(name.strip().lower().replace(" ", "-"))
        if binary is None:
            raise ActionError(f"I couldn't find an app called {name}.")
        subprocess.Popen(
            [binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )

    def close_app(self, name: str) -> int:
        return processes.close_app(name, _executables(name))

    def media(self, action: str, app: str | None) -> str:
        return mpris.control(action, app)

    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    def power(self, kind: str) -> None:
        command = {"shutdown": "poweroff", "restart": "reboot", "suspend": "suspend"}[kind]
        run(["systemctl", command])


APP_FOLDERS = (
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    Path("/var/lib/snapd/desktop/applications"),
)
FILLER = frozenset({"the", "a", "my", "app", "application", "program", "browser", "web"})


def _desktop_entries(folders: tuple[Path, ...] = APP_FOLDERS) -> list[tuple[str, str, str]]:
    """(entry id, display name, program) for installed, visible applications."""
    entries = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for entry in sorted(folder.glob("*.desktop")):
            try:
                text = entry.read_text(errors="ignore")
            except OSError:
                continue
            if re.search(r"^NoDisplay=true$", text, re.M):
                continue
            found = re.search(r"^Name=(.+)$", text, re.M)
            program = re.search(r"^Exec=(.+)$", text, re.M)
            entries.append(
                (
                    entry.stem,
                    found.group(1).strip() if found else entry.stem,
                    _program(program.group(1)) if program else "",
                )
            )
    return entries


def _screenshot_with_cli() -> Path | None:
    """Screenshot tools for X11 and non-GNOME desktops."""
    folder = screen.screenshots_folder()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"Screenshot {datetime.now():%Y-%m-%d %H-%M-%S}.png"
    commands = (
        ["gnome-screenshot", "-f", str(target)],
        ["spectacle", "-b", "-n", "-f", "-o", str(target)],
        ["grim", str(target)],
        ["scrot", str(target)],
        ["import", "-window", "root", str(target)],
    )
    for argv in commands:
        if shutil.which(argv[0]):
            try:
                run(argv, timeout=15)
            except ActionError:
                continue
            if target.exists():
                return target
    return None


def _program(exec_line: str) -> str:
    """The binary an Exec= line runs: "env FOO=1 /snap/bin/firefox %u" -> "firefox"."""
    for token in exec_line.split():
        if token in {"env", "flatpak", "run"} or "=" in token or token.startswith("-"):
            continue
        return Path(token.strip('"')).name
    return ""


def _executables(name: str) -> list[str]:
    """Programs behind the desktop entries a spoken app name matches."""
    entries = _desktop_entries()
    ids = set(_desktop_ids(name, entries)[:3])
    return [program for entry_id, _display, program in entries if entry_id in ids and program]


def _desktop_ids(name: str, entries: Sequence[tuple[str, ...]] | None = None) -> list[str]:
    """Desktop entry IDs to try for a spoken app name, best match first.

    "firefox" -> firefox; "chrome browser" -> google-chrome; "visual studio code" -> code.
    """
    spoken = name.strip().lower()
    words = [word for word in re.findall(r"[a-z0-9]+", spoken) if word not in FILLER]
    exact: list[str] = []
    partial: list[str] = []
    for entry_id, display, *_ in entries if entries is not None else _desktop_entries():
        if display.lower() == spoken or entry_id.lower() == spoken:
            exact.append(entry_id)
        elif words and all(word in f"{display} {entry_id}".lower() for word in words):
            partial.append(entry_id)
    guesses = [spoken, spoken.replace(" ", "-"), spoken.replace(" ", "")]
    return list(dict.fromkeys(exact + sorted(partial, key=len) + guesses))
