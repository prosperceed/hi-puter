"""`hi-puter setup`: get from a fresh `pipx install` to a working assistant.

pipx installs every Python package Hi-Puter needs. What's left are things only the system or
the user can provide: the microphone and voice libraries on Linux, the Ollama app, the
language model and the speech model. Each step explains itself, asks before anything that
needs a password, and never stops the rest of setup if it fails; it prints the command to
run by hand instead.
"""

import ctypes.util
import dataclasses
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import psutil

from hi_puter.brain.llm import OllamaClient
from hi_puter.cli.commands.doctor import FAIL, Check, collect_checks
from hi_puter.core.config import Config, load_config, save_config
from hi_puter.core.errors import ConfigError, ModelError
from hi_puter.core.paths import AppPaths
from hi_puter.onboarding import ollama_setup, system
from hi_puter.onboarding.speech_setup import download_speech_model
from hi_puter.runtime.assemble import make_model

STEPS = 5
MAX_NAME_TRIES = 3


class Console(Protocol):
    def say(self, text: str = "") -> None: ...
    def ask(self, question: str, default: str) -> str: ...
    def confirm(self, question: str, default: bool = True) -> bool: ...
    def progress(self, text: str) -> None: ...
    def progress_done(self) -> None: ...


def run_command(argv: list[str]) -> int:
    """Run a command attached to the user's terminal, so sudo can ask for a password."""
    try:
        return subprocess.run(argv, check=False).returncode
    except OSError:
        return 127


@dataclass
class Wizard:
    console: Console
    paths: AppPaths
    yes: bool = False
    name: str | None = None
    run: Callable[[list[str]], int] = run_command
    which: Callable[[str], str | None] = shutil.which
    find_library: Callable[[str], str | None] = ctypes.util.find_library
    platform: str = sys.platform
    total_memory: Callable[[], int] = field(default=lambda: psutil.virtual_memory().total)
    client_for: Callable[[Config], OllamaClient | None] = make_model
    download_speech: Callable[[str], Path] = download_speech_model
    checks: Callable[[], list[Check]] = collect_checks
    start_ollama: Callable[[], object] | None = None

    # -- the whole flow ---------------------------------------------------------------------

    def run_all(self) -> bool:
        self.console.say("Hi-Puter setup")
        self.console.say("Every step can be re-run safely; nothing is installed without asking.")
        config = self._load()
        config = self.choose_name(config)
        self.system_libraries()
        config = self.language_model(config)
        self.speech_model(config)
        save_config(self.paths.config_file, config)
        return self.summary()

    def _load(self) -> Config:
        try:
            return load_config(self.paths.config_file)
        except ConfigError as exc:
            self.console.say(f"Your existing settings couldn't be read ({exc}); starting fresh.")
            return Config()

    def _step(self, number: int, title: str) -> None:
        self.console.say()
        self.console.say(f"[{number}/{STEPS}] {title}")

    def _agree(self, question: str) -> bool:
        return self.yes or self.console.confirm(question, default=True)

    # -- 1. name ----------------------------------------------------------------------------

    def choose_name(self, config: Config) -> Config:
        self._step(1, "Name")
        name = self.name or config.wake.name.title()
        for _ in range(MAX_NAME_TRIES):
            if not self.yes and self.name is None:
                name = self.console.ask("What should your assistant be called?", name)
            wake = dataclasses.replace(config.wake, name=name.strip().lower())
            candidate = dataclasses.replace(config, wake=wake)
            try:
                candidate.validate()
            except ConfigError as exc:
                self.console.say(f"  {exc}")
                if self.yes or self.name is not None:
                    break
                continue
            self.console.say(f"  Say “{name.strip().title()}” to wake it.")
            return candidate
        self.console.say(f"  Keeping “{config.wake.name.title()}”.")
        return config

    # -- 2. voice and microphone ------------------------------------------------------------

    def system_libraries(self) -> None:
        self._step(2, "Voice and microphone")
        missing = system.missing_libraries(self.which, self.find_library, self.platform)
        if not missing:
            self.console.say("  ✓ Already set up.")
            return
        for library in missing:
            self.console.say(f"  Missing {library}: it {system.WHY[library]}.")
        command = system.install_command(missing, self.which)
        if command is None:
            self.console.say(
                "  Install them with your system's package manager, then run setup again."
            )
            return
        self.console.say(f"  This needs your password: {' '.join(command)}")
        if not self._agree("  Install them now?"):
            self.console.say("  Skipped. Run the command above when you're ready.")
            return
        if self.run(command) == 0 and not system.missing_libraries(
            self.which, self.find_library, self.platform
        ):
            self.console.say("  ✓ Installed.")
        else:
            self.console.say(f"  That didn't finish. You can run it yourself: {' '.join(command)}")

    # -- 3 and 4. Ollama and the language model --------------------------------------------

    def language_model(self, config: Config) -> Config:
        self._step(3, "Local AI (Ollama)")
        client = self.client_for(config)
        if client is None:
            self.console.say("  The language model is turned off in your settings; skipping.")
            self._step(4, "Language model")
            self.console.say("  Skipped.")
            return config
        if not self._ollama_ready(client):
            self._step(4, "Language model")
            self.console.say("  Skipped until Ollama is running. Simple commands still work.")
            return config
        self._step(4, "Language model")
        return self._choose_model(config, client)

    def _ollama_ready(self, client: OllamaClient) -> bool:
        if not ollama_setup.installed(self.which):
            self.console.say(
                "  Ollama runs the language model on this computer, for questions and"
                " multi-step requests. Nothing leaves your machine."
            )
            command = ollama_setup.install_command(self.platform)
            if command is None:
                self.console.say("  Install it from https://ollama.com, then run setup again.")
                return False
            self.console.say(f"  Official installer: {' '.join(command)}")
            if not self._agree("  Install Ollama now?"):
                self.console.say("  Skipped. Install it from https://ollama.com when you're ready.")
                return False
            if self.run(command) != 0 or not ollama_setup.installed(self.which):
                self.console.say("  The installer didn't finish. Get it from https://ollama.com.")
                return False
        if ollama_setup.ensure_running(client, start=self.start_ollama):
            self.console.say("  ✓ Ollama is running.")
            return True
        self.console.say("  Ollama is installed but not answering. Start it, then run setup again.")
        return False

    def _choose_model(self, config: Config, client: OllamaClient) -> Config:
        if _has_model(client):
            self.console.say(f"  ✓ {config.llm.model} is ready.")
            return config
        memory = self.total_memory()
        model = ollama_setup.recommended_model(memory)
        updated = dataclasses.replace(config, llm=dataclasses.replace(config.llm, model=model))
        chosen = self.client_for(updated) or client
        self.console.say(
            f"  This computer has {memory / 1024**3:.0f} GB of memory, so {model} fits best."
        )
        if _has_model(chosen):
            self.console.say(f"  ✓ {model} is already downloaded.")
            return updated
        size = ollama_setup.DOWNLOAD_SIZES.get(model, "a few GB")
        if not self._agree(f"  Download {model} now ({size})?"):
            self.console.say(f"  Skipped. Later, run: ollama pull {model}")
            return updated
        try:
            chosen.pull(self._show_progress(model))
        except ModelError as exc:
            self.console.progress_done()
            self.console.say(f"  {exc} Run setup again to resume; finished parts are kept.")
            return updated
        self.console.progress_done()
        self.console.say(f"  ✓ {model} is ready.")
        return updated

    def _show_progress(self, model: str) -> Callable[[str, int, int], None]:
        def show(status: str, done: int, total: int) -> None:
            if total:
                percent = 100 * done / total
                self.console.progress(
                    f"  Downloading {model}  {percent:3.0f}%  "
                    f"{done / 1e9:.1f} of {total / 1e9:.1f} GB"
                )
            elif status:
                self.console.progress(f"  {status.capitalize()}")

        return show

    # -- 5. speech recognition --------------------------------------------------------------

    def speech_model(self, config: Config) -> None:
        self._step(5, "Speech recognition")
        self.console.say(f"  Getting the {config.stt.model} speech model (about 150 MB, once).")
        try:
            self.download_speech(config.stt.model)
        except Exception as exc:  # network, disk, or a missing package
            self.console.say(f"  Couldn't download it now ({exc}). It downloads on first start.")
            return
        self.console.say("  ✓ Ready.")

    # -- summary ----------------------------------------------------------------------------

    def summary(self) -> bool:
        self.console.say()
        self.console.say("Checking everything")
        results = self.checks()
        for status, label, detail in results:
            self.console.say(f"  {status:<5} {label:<16} {detail}")
        ok = not any(status == FAIL for status, _, _ in results)
        self.console.say()
        if ok:
            self.console.say("All set. Start Hi-Puter with:  hi-puter start")
        else:
            self.console.say(
                "Almost there: fix the FAIL lines above, then run hi-puter setup again."
            )
        return ok


def _has_model(client: OllamaClient) -> bool:
    try:
        return client.has_model()
    except ModelError:
        return False
