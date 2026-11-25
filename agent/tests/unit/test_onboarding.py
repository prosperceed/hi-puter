import dataclasses
import io
import json
from pathlib import Path
from typing import Any

import pytest

from hi_puter.brain import llm
from hi_puter.brain.llm import OllamaClient
from hi_puter.cli.commands.doctor import FAIL, PASS
from hi_puter.core.config import Config, LlmConfig, TtsConfig, load_config, save_config
from hi_puter.core.errors import ModelError
from hi_puter.core.paths import AppPaths
from hi_puter.onboarding import ollama_setup, system
from hi_puter.onboarding.wizard import Wizard

GiB = 1024**3


# -- building blocks -------------------------------------------------------------------------


def test_missing_libraries_on_linux() -> None:
    nothing = lambda _name: None  # noqa: E731
    assert system.missing_libraries(nothing, nothing, "linux") == ["PortAudio", "espeak-ng"]
    everything = lambda name: f"/usr/bin/{name}"  # noqa: E731
    assert system.missing_libraries(everything, everything, "linux") == []
    assert system.missing_libraries(nothing, nothing, "win32") == []  # bundled on Windows


@pytest.mark.parametrize(
    ("manager", "command"),
    [
        ("apt-get", ["sudo", "apt-get", "install", "-y", "libportaudio2", "espeak-ng"]),
        ("dnf", ["sudo", "dnf", "install", "-y", "portaudio", "espeak-ng"]),
        ("pacman", ["sudo", "pacman", "-S", "--needed", "--noconfirm", "portaudio", "espeak-ng"]),
    ],
)
def test_install_command_per_distribution(manager: str, command: list[str]) -> None:
    def which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == manager else None

    assert system.install_command(["PortAudio", "espeak-ng"], which) == command


def test_unknown_package_manager() -> None:
    assert system.install_command(["PortAudio"], lambda _name: None) is None


def test_model_choice_by_memory() -> None:
    assert ollama_setup.recommended_model(8 * GiB) == "qwen3.5:2b"
    assert ollama_setup.recommended_model(int(15.5 * GiB)) == "qwen3.5:4b"  # a 16 GB machine


def test_ollama_installers() -> None:
    assert ollama_setup.install_command("linux")[-1].endswith("install.sh | sh")  # type: ignore[index]
    assert ollama_setup.install_command("win32")[:2] == ["winget", "install"]  # type: ignore[index]
    assert ollama_setup.install_command("darwin") is None


class FakeResponse(io.BytesIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_pull_reports_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    events = [
        {"status": "pulling manifest"},
        {"status": "pulling 0689d4", "total": 2_000, "completed": 500},
        {"status": "pulling 0689d4", "total": 2_000, "completed": 2_000},
        {"status": "success"},
    ]
    body = "\n".join(json.dumps(event) for event in events).encode()
    sent: list[dict[str, Any]] = []

    def urlopen(request: Any, timeout: float) -> FakeResponse:
        sent.append(json.loads(request.data))
        return FakeResponse(body)

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    seen: list[tuple[str, int, int]] = []
    OllamaClient("http://127.0.0.1:11434", "qwen3.5:2b").pull(
        lambda status, done, total: seen.append((status, done, total))
    )
    assert sent == [{"model": "qwen3.5:2b", "stream": True}]
    assert seen[1] == ("pulling 0689d4", 500, 2_000) and seen[-1][0] == "success"


def test_pull_error_event(monkeypatch: pytest.MonkeyPatch) -> None:
    missing = b'{"error": "pull model manifest: file does not exist"}'
    monkeypatch.setattr(
        llm.urllib.request, "urlopen", lambda request, timeout: FakeResponse(missing)
    )
    with pytest.raises(ModelError, match="couldn't download"):
        OllamaClient("http://127.0.0.1:11434", "nope:1b").pull()


# -- the wizard ------------------------------------------------------------------------------


class Terminal:
    """Records what the wizard says and answers its questions from a script."""

    def __init__(self, answers: list[bool] | None = None, names: list[str] | None = None) -> None:
        self.lines: list[str] = []
        self.questions: list[str] = []
        self.answers = list(answers or [])
        self.names = list(names or [])

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def ask(self, question: str, default: str) -> str:
        self.questions.append(question)
        return self.names.pop(0) if self.names else default

    def confirm(self, question: str, default: bool = True) -> bool:
        self.questions.append(question)
        return self.answers.pop(0) if self.answers else default

    def progress(self, text: str) -> None:
        self.lines.append(text)

    def progress_done(self) -> None:
        return None

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclasses.dataclass
class FakeOllama:
    """One shared state: installed, running, and which models are downloaded."""

    installed: bool = True
    running: bool = True
    models: set[str] = dataclasses.field(default_factory=set)
    pulled: list[str] = dataclasses.field(default_factory=list)
    fail_pull: bool = False

    def client(self, config: Config) -> "FakeClient":
        return FakeClient(self, config.llm.model)


class FakeClient:
    host = "http://127.0.0.1:11434"
    timeout = 90.0

    def __init__(self, state: FakeOllama, model: str) -> None:
        self.state = state
        self.model = model

    def version(self) -> str | None:
        return "0.40.2" if self.state.running else None

    def has_model(self) -> bool:
        return self.model in self.state.models

    def pull(self, on_progress: Any = None) -> None:
        if self.state.fail_pull:
            raise ModelError("Download of qwen3.5:2b stopped: connection reset.")
        on_progress("pulling 0689d4", 1_350_000_000, 2_700_000_000)
        self.state.models.add(self.model)
        self.state.pulled.append(self.model)


def make_wizard(
    tmp_path: Path,
    *,
    terminal: Terminal,
    ollama: FakeOllama,
    libraries_present: bool = True,
    memory: int = 8 * GiB,
    yes: bool = False,
    checks: list[tuple[str, str, str]] | None = None,
) -> tuple[Wizard, list[list[str]]]:
    paths = AppPaths(tmp_path / "config", tmp_path / "data", tmp_path / "state", tmp_path / "run")
    commands: list[list[str]] = []
    present = {"libs": libraries_present}

    def run(argv: list[str]) -> int:
        commands.append(argv)
        if argv[0] == "sudo":
            present["libs"] = True
        if "install.sh" in argv[-1]:
            ollama.installed = True
        return 0

    def which(name: str) -> str | None:
        if name == "ollama":
            return "/usr/local/bin/ollama" if ollama.installed else None
        if name in {"espeak-ng", "espeak"}:
            return "/usr/bin/espeak-ng" if present["libs"] else None
        return "/usr/bin/apt-get" if name == "apt-get" else None

    def find_library(_name: str) -> str | None:
        return "libportaudio.so.2" if present["libs"] else None

    def start() -> object:
        ollama.running = True
        return object()

    wizard = Wizard(
        terminal, paths, yes=yes, run=run, which=which, find_library=find_library,
        platform="linux", total_memory=lambda: memory, client_for=ollama.client,  # type: ignore[arg-type]
        download_speech=lambda _name: tmp_path / "whisper", start_ollama=start,
        checks=lambda: checks or [(PASS, "Language model", "ok")],
    )  # fmt: skip
    return wizard, commands


def test_a_working_machine_needs_nothing(tmp_path: Path) -> None:
    terminal = Terminal()
    ollama = FakeOllama(models={"qwen3.5:4b"})
    wizard, commands = make_wizard(tmp_path, terminal=terminal, ollama=ollama)
    assert wizard.run_all()
    assert commands == [] and ollama.pulled == []
    assert terminal.questions == ["What should your assistant be called?"]
    assert "All set. Start Hi-Puter with:  hi-puter start" in terminal.text


def test_fresh_linux_install_does_everything_with_consent(tmp_path: Path) -> None:
    terminal = Terminal(names=["Jarvis"])
    ollama = FakeOllama(installed=False, running=False)
    wizard, commands = make_wizard(
        tmp_path, terminal=terminal, ollama=ollama, libraries_present=False, memory=8 * GiB
    )
    assert wizard.run_all()
    assert commands[0] == ["sudo", "apt-get", "install", "-y", "libportaudio2", "espeak-ng"]
    assert "install.sh" in commands[1][-1]
    assert ollama.pulled == ["qwen3.5:2b"]  # 8 GB of RAM: the smaller model
    assert "Downloading qwen3.5:2b   50%  1.4 of 2.7 GB" in terminal.text
    config = load_config(wizard.paths.config_file)
    assert config.wake.name == "jarvis" and config.llm.model == "qwen3.5:2b"
    assert any("This needs your password" in line for line in terminal.lines)


def test_declining_installs_nothing_but_still_saves_the_name(tmp_path: Path) -> None:
    terminal = Terminal(answers=[False, False], names=["Nova"])
    ollama = FakeOllama(installed=False, running=False)
    wizard, commands = make_wizard(
        tmp_path, terminal=terminal, ollama=ollama, libraries_present=False
    )
    wizard.run_all()
    assert commands == []
    assert "Skipped. Run the command above when you're ready." in terminal.text
    assert load_config(wizard.paths.config_file).wake.name == "nova"


def test_yes_never_asks(tmp_path: Path) -> None:
    terminal = Terminal()
    ollama = FakeOllama(installed=False, running=False)
    wizard, commands = make_wizard(
        tmp_path, terminal=terminal, ollama=ollama, libraries_present=False, yes=True,
        memory=16 * GiB,
    )  # fmt: skip
    wizard.run_all()
    assert terminal.questions == []
    assert len(commands) == 2 and ollama.pulled == ["qwen3.5:4b"]


def test_a_failed_download_does_not_stop_setup(tmp_path: Path) -> None:
    terminal = Terminal()
    ollama = FakeOllama(fail_pull=True)
    wizard, _ = make_wizard(tmp_path, terminal=terminal, ollama=ollama)
    wizard.run_all()
    assert "connection reset. Run setup again to resume" in terminal.text
    assert "[5/5] Speech recognition" in terminal.text  # carried on


def test_an_invalid_name_is_asked_again(tmp_path: Path) -> None:
    terminal = Terminal(names=["way too many words here", "Nova"])
    wizard, _ = make_wizard(tmp_path, terminal=terminal, ollama=FakeOllama(models={"qwen3.5:4b"}))
    wizard.run_all()
    assert terminal.questions.count("What should your assistant be called?") == 2
    assert load_config(wizard.paths.config_file).wake.name == "nova"


def test_existing_settings_are_kept(tmp_path: Path) -> None:
    terminal = Terminal(names=["Jarvis"])
    ollama = FakeOllama(models={"qwen3.5:2b"})
    wizard, _ = make_wizard(tmp_path, terminal=terminal, ollama=ollama)
    previous = dataclasses.replace(
        Config(), llm=LlmConfig(model="qwen3.5:2b"), tts=TtsConfig(rate=150)
    )
    save_config(wizard.paths.config_file, previous)
    wizard.run_all()
    config = load_config(wizard.paths.config_file)
    assert config.tts.rate == 150 and config.llm.model == "qwen3.5:2b"
    assert config.wake.name == "jarvis"
    assert ollama.pulled == []


def test_summary_reports_remaining_problems(tmp_path: Path) -> None:
    terminal = Terminal()
    wizard, _ = make_wizard(
        tmp_path, terminal=terminal, ollama=FakeOllama(models={"qwen3.5:4b"}),
        checks=[(FAIL, "Microphone", "no input devices found")],
    )  # fmt: skip
    assert not wizard.run_all()
    assert "Almost there" in terminal.text and "no input devices found" in terminal.text
