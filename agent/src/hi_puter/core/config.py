import dataclasses
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]
import tomli_w

from hi_puter.core.errors import ConfigError

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True)
class WakeConfig:
    name: str = "nova"
    # Minimum similarity (0-1) between what was heard and the wake name.
    threshold: float = 0.8
    verify_with_stt: bool = True


@dataclass(frozen=True)
class AudioConfig:
    device: str | int | None = None
    vad_aggressiveness: int = 2
    max_command_seconds: float = 12.0


@dataclass(frozen=True)
class SttConfig:
    model: str = "base.en"
    compute_type: str = "int8"


@dataclass(frozen=True)
class TtsConfig:
    # "auto" prefers espeak-ng on Linux and SAPI (pyttsx3) on Windows.
    engine: str = "auto"
    rate: int = 175
    voice: str | None = None


@dataclass(frozen=True)
class VoiceConfig:
    listening_phrase: str = "Listening."
    working_phrase: str = "On it."
    chime: bool = True
    # After answering, keep listening this long for a follow-up without the wake name.
    followup_seconds: float = 6.0
    # How long to wait for the request to start after "Listening".
    prompt_timeout_seconds: float = 8.0
    end_silence_ms: int = 700


@dataclass(frozen=True)
class LlmConfig:
    enabled: bool = True
    host: str = "http://127.0.0.1:11434"
    model: str = "qwen3.5:4b"
    temperature: float = 0.2
    max_steps: int = 5
    context_tokens: int = 4096
    timeout_seconds: float = 90.0
    # How long Ollama keeps the model in memory between requests. Reloading takes up to a
    # minute on a slow laptop, so keep it while Hi-Puter runs; stopping Hi-Puter unloads it.
    keep_alive: str = "24h"
    # Audio never leaves the machine; this allows sending transcripts to a non-local model host.
    allow_remote: bool = False


@dataclass(frozen=True)
class LifecycleConfig:
    idle_timeout_minutes: int = 0


@dataclass(frozen=True)
class LoggingConfig:
    log_transcripts: bool = False


@dataclass(frozen=True)
class Config:
    wake: WakeConfig = field(default_factory=WakeConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    apps_aliases: dict[str, str] = field(default_factory=dict)
    search_url_template: str = "https://www.google.com/search?q={query}"
    lifecycle: LifecycleConfig = field(default_factory=LifecycleConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    language: str = "en"

    def validate(self) -> None:
        name = self.wake.name.strip().lower()
        if not 2 <= len(name) <= 24 or not name.replace(" ", "").replace("-", "").isalnum():
            raise ConfigError(
                "Wake name must be 2 to 24 characters using letters, digits, spaces, or hyphens."
            )
        if name[0] in " -" or name[-1] in " -" or "  " in name:
            raise ConfigError(
                "Wake name cannot start or end with a separator or contain repeated spaces."
            )
        if not 1 <= len(name.split()) <= 2:
            raise ConfigError("Wake name must contain one or two words.")
        if not 0 < self.wake.threshold <= 1:
            raise ConfigError("Wake threshold must be between 0 and 1.")
        if not 0 <= self.audio.vad_aggressiveness <= 3:
            raise ConfigError("VAD aggressiveness must be 0 to 3.")
        if self.audio.max_command_seconds <= 0:
            raise ConfigError("Maximum command time must be positive.")
        if self.tts.engine not in {"auto", "espeak", "pyttsx3", "console"}:
            raise ConfigError("TTS engine must be auto, espeak, pyttsx3, or console.")
        if self.voice.followup_seconds < 0 or self.voice.prompt_timeout_seconds <= 0:
            raise ConfigError("Voice timeouts must be positive.")
        if not 200 <= self.voice.end_silence_ms <= 3000:
            raise ConfigError("End-of-speech silence must be 200 to 3000 ms.")
        if "{query}" not in self.search_url_template:
            raise ConfigError("Search URL template must contain {query}.")
        self._validate_llm()

    def _validate_llm(self) -> None:
        host = urlparse(self.llm.host)
        if host.scheme not in {"http", "https"} or not host.hostname:
            raise ConfigError(
                "LLM host must be an http(s) URL, for example http://127.0.0.1:11434."
            )
        if not self.llm.allow_remote and host.hostname not in LOCAL_HOSTS:
            raise ConfigError(
                "LLM host is not local. Set llm.allow_remote = true to send transcripts"
                " off this machine."
            )
        if not 1 <= self.llm.max_steps <= 10:
            raise ConfigError("LLM max_steps must be 1 to 10.")
        if not 0 <= self.llm.temperature <= 2:
            raise ConfigError("LLM temperature must be 0 to 2.")
        if not self.llm.model.strip():
            raise ConfigError("LLM model must be set.")


T = TypeVar("T")


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _build(cls: type[T], values: dict[str, Any]) -> T:
    """Construct a config dataclass from a TOML table, ignoring unknown keys."""
    known = {item.name for item in dataclasses.fields(cls)}  # type: ignore[arg-type]
    try:
        return cls(**{key: value for key, value in values.items() if key in known})
    except TypeError as exc:
        raise ConfigError(f"Invalid [{cls.__name__}] settings: {exc}") from exc


def load_config(path: Path) -> Config:
    if not path.exists():
        return Config()
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"Could not read config at {path}: {exc}") from exc
    config = Config(
        wake=_build(WakeConfig, _section(raw, "wake")),
        audio=_build(AudioConfig, _section(raw, "audio")),
        stt=_build(SttConfig, _section(raw, "stt")),
        tts=_build(TtsConfig, _section(raw, "tts")),
        voice=_build(VoiceConfig, _section(raw, "voice")),
        llm=_build(LlmConfig, _section(raw, "llm")),
        apps_aliases={
            str(k).lower(): str(v) for k, v in _section(raw, "apps").get("aliases", {}).items()
        },
        search_url_template=str(
            _section(raw, "search").get("url_template", Config.search_url_template)
        ),
        lifecycle=_build(LifecycleConfig, _section(raw, "lifecycle")),
        logging=_build(LoggingConfig, _section(raw, "logging")),
        language=str(raw.get("language", "en")),
    )
    config.validate()
    return config


def save_config(path: Path, config: Config) -> None:
    config.validate()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = asdict(config)
    payload["apps"] = {"aliases": payload.pop("apps_aliases")}
    payload["search"] = {"url_template": payload.pop("search_url_template")}
    payload = _without_none(payload)
    fd, temp_name = tempfile.mkstemp(prefix=".config-", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "wb") as handle:
            tomli_w.dump(payload, handle)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _without_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_without_none(item) for item in value]
    return value
