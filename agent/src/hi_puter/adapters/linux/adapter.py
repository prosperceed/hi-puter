import re
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

from hi_puter.adapters.runner import run
from hi_puter.core.errors import ActionError

SINK = "@DEFAULT_AUDIO_SINK@"


class LinuxAdapter:
    def capabilities(self) -> frozenset[str]:
        return frozenset({"volume", "lock", "screenshot", "apps", "web", "power"})

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

    def screenshot(self) -> Path:
        folder = Path.home() / "Pictures" / "Screenshots"
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
                run(argv, timeout=15)
                if target.exists():
                    return target
        raise ActionError("No screenshot tool found (install gnome-screenshot, grim or scrot).")

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


def _desktop_entries(folders: tuple[Path, ...] = APP_FOLDERS) -> list[tuple[str, str]]:
    """(entry id, display name) for installed, visible applications."""
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
            entries.append((entry.stem, found.group(1).strip() if found else entry.stem))
    return entries


def _desktop_ids(name: str, entries: list[tuple[str, str]] | None = None) -> list[str]:
    """Desktop entry IDs to try for a spoken app name, best match first.

    "firefox" -> firefox; "chrome browser" -> google-chrome; "visual studio code" -> code.
    """
    spoken = name.strip().lower()
    words = [word for word in re.findall(r"[a-z0-9]+", spoken) if word not in FILLER]
    exact: list[str] = []
    partial: list[str] = []
    for entry_id, display in entries if entries is not None else _desktop_entries():
        if display.lower() == spoken or entry_id.lower() == spoken:
            exact.append(entry_id)
        elif words and all(word in f"{display} {entry_id}".lower() for word in words):
            partial.append(entry_id)
    guesses = [spoken, spoken.replace(" ", "-"), spoken.replace(" ", "")]
    return list(dict.fromkeys(exact + sorted(partial, key=len) + guesses))
