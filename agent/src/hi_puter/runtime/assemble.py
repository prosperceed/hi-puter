import dataclasses
from pathlib import Path

from hi_puter.adapters.base import SystemAdapter
from hi_puter.brain.assistant import Assistant
from hi_puter.brain.llm import OllamaClient
from hi_puter.brain.tools import build_toolbox
from hi_puter.brain.writer import Writer
from hi_puter.core.config import Config
from hi_puter.core.paths import AppPaths


class DryRunAdapter:
    """Prints what would happen instead of touching the system."""

    def capabilities(self) -> frozenset[str]:
        return frozenset(
            {"volume", "lock", "screenshot", "recording", "apps", "web", "power", "media", "files"}
        )

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

    def screenshot(self, interactive: bool = False) -> Path | None:
        if interactive:
            self._show("open the screenshot tool")
            return None
        self._show("take a screenshot")
        return Path.home() / "Pictures" / "Screenshots" / "dry-run.png"

    def start_recording(self, seconds: float | None) -> Path:
        self._show("start screen recording" + (f" for {seconds:g}s" if seconds else ""))
        return Path.home() / "Videos" / "Screencasts" / "dry-run.webm"

    def stop_recording(self) -> Path | None:
        self._show("stop screen recording")
        return Path.home() / "Videos" / "Screencasts" / "dry-run.webm"

    def open_path(self, path: Path) -> None:
        self._show(f"open file {path}")

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
    model = make_model(config)
    writing_model = model
    if model is not None and config.documents.model.strip():
        llm = dataclasses.replace(config.llm, model=config.documents.model.strip())
        writing_model = make_model(dataclasses.replace(config, llm=llm))
    writer = Writer(writing_model, config.documents.path) if writing_model is not None else None
    toolbox = build_toolbox(adapter, config, notes_file=paths.data_dir / "notes.md", writer=writer)
    return Assistant(
        toolbox,
        model,
        name=config.wake.name,
        max_steps=config.llm.max_steps,
        writer=writer,
        open_documents=config.documents.open_after_writing,
    )
