from pathlib import Path
import subprocess
import webbrowser

from hi_puter.adapters.runner import run


class LinuxAdapter:
    def capabilities(self) -> frozenset[str]: return frozenset({"volume", "lock", "screenshot", "apps", "web", "power"})
    def volume_get(self) -> int: return 50
    def volume_set(self, level: int) -> None: run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{max(0, min(100, level))}%"])
    def volume_change(self, delta: int) -> None: run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{delta:+d}%"])
    def set_mute(self, muted: bool) -> None: run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if muted else "0"])
    def lock(self) -> None: run(["loginctl", "lock-session"])
    def screenshot(self) -> Path: raise NotImplementedError("Screenshot backend detection is required before use")
    def open_app(self, name: str) -> None: run(["gtk-launch", name])
    def open_url(self, url: str) -> None: webbrowser.open(url)
    def power(self, kind: str) -> None:
        command = {"shutdown": "poweroff", "restart": "reboot", "suspend": "suspend"}[kind]
        run(["systemctl", command])
