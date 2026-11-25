from pathlib import Path

from hi_puter.adapters.base import SystemAdapter
from hi_puter.brain.assistant import Assistant
from hi_puter.brain.llm import OllamaClient
from hi_puter.brain.tools import build_toolbox
from hi_puter.core.config import Config
from hi_puter.core.paths import AppPaths


class DryRunAdapter:
    """Prints what would happen instead of touching the system."""

    def capabilities(self) -> frozenset[str]:
        return frozenset({"volume", "lock", "screenshot", "apps", "web", "power", "media"})

    def _show(self, action: str) -> None:
        print(f"  [dry run] {action}", flush=True)

    def volume_get(self) -> int:
        return 50

    def volume_set(self, level: int) -> None:
        self._show(f"set volume to {level}%")

    def volume_change(self, delta: int) -> None:
        self._show(f"change volume by {delta:+d}%")

    def set_mute(self, muted: bool) -> None:
        self._show("mute" if muted else "unmute")

    def lock(self) -> None:
        self._show("lock the screen")

    def screenshot(self) -> Path:
        self._show("take a screenshot")
        return Path.home() / "Pictures" / "Screenshots" / "dry-run.png"

    def open_app(self, name: str) -> None:
        self._show(f"open app {name!r}")

    def open_url(self, url: str) -> None:
        self._show(f"open {url}")

    def close_app(self, name: str) -> int:
        self._show(f"close app {name!r}")
        return 1

    def media(self, action: str, app: str | None) -> str:
        self._show(f"media {action}" + (f" on {app}" if app else ""))
        return (app or "Spotify").title()

    def power(self, kind: str) -> None:
        self._show(f"power {kind}")


def make_model(config: Config) -> OllamaClient | None:
    if not config.llm.enabled:
        return None
    llm = config.llm
    return OllamaClient(
        llm.host,
        llm.model,
        temperature=llm.temperature,
        context_tokens=llm.context_tokens,
        timeout=llm.timeout_seconds,
        keep_alive=llm.keep_alive,
    )


def build_assistant(config: Config, paths: AppPaths, adapter: SystemAdapter) -> Assistant:
    toolbox = build_toolbox(adapter, config, notes_file=paths.data_dir / "notes.md")
    return Assistant(
        toolbox, make_model(config), name=config.wake.name, max_steps=config.llm.max_steps
    )
