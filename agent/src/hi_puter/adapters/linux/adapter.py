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


def _desktop_ids(name: str) -> list[str]:
    """Desktop entry IDs to try for a spoken app name, e.g. "visual studio code" -> code, ..."""
    spoken = name.strip().lower()
    ids = [spoken, spoken.replace(" ", "-"), spoken.replace(" ", "")]
    for folder in (
        Path("/usr/share/applications"),
        Path.home() / ".local/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
    ):
        if not folder.is_dir():
            continue
        for entry in folder.glob("*.desktop"):
            try:
                text = entry.read_text(errors="ignore")
            except OSError:
                continue
            found = re.search(r"^Name=(.+)$", text, re.M)
            if found and found.group(1).strip().lower() == spoken:
                ids.insert(0, entry.stem)
    return list(dict.fromkeys(ids))
