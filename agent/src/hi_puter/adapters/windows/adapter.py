import os
import webbrowser
from pathlib import Path

from hi_puter.adapters.processes import close_app


class WindowsAdapter:
    """Windows implementation boundary. Real Windows verification is pending."""

    def capabilities(self) -> frozenset[str]:
        return frozenset({"volume", "lock", "screenshot", "apps", "web", "power", "files"})

    def volume_get(self) -> int:
        raise NotImplementedError

    def volume_set(self, level: int) -> None:
        raise NotImplementedError

    def volume_change(self, delta: int) -> None:
        raise NotImplementedError

    def set_mute(self, muted: bool) -> None:
        raise NotImplementedError

    def lock(self) -> None:
        raise NotImplementedError

    def screenshot(self) -> Path:
        raise NotImplementedError

    def open_app(self, name: str) -> None:
        os.startfile(name)  # type: ignore[attr-defined]  # noqa: S606 (opens the app, no shell)

    def close_app(self, name: str) -> int:
        return close_app(name)

    def media(self, action: str, app: str | None) -> str:
        raise NotImplementedError

    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    def power(self, kind: str) -> None:
        raise NotImplementedError
