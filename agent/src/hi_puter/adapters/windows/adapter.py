from pathlib import Path
import os
import webbrowser


class WindowsAdapter:
    """Windows implementation boundary. Real Windows verification is pending."""

    def capabilities(self) -> frozenset[str]: return frozenset({"volume", "lock", "screenshot", "apps", "web", "power"})
    def volume_get(self) -> int: raise NotImplementedError
    def volume_set(self, level: int) -> None: raise NotImplementedError
    def volume_change(self, delta: int) -> None: raise NotImplementedError
    def set_mute(self, muted: bool) -> None: raise NotImplementedError
    def lock(self) -> None: raise NotImplementedError
    def screenshot(self) -> Path: raise NotImplementedError
    def open_app(self, name: str) -> None: os.startfile(name)  # type: ignore[attr-defined]
    def open_url(self, url: str) -> None: webbrowser.open(url)
    def power(self, kind: str) -> None: raise NotImplementedError
