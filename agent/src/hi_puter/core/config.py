from dataclasses import asdict, dataclass, field
from pathlib import Path
import os
import tempfile
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

from hi_puter.core.errors import ConfigError


@dataclass(frozen=True)
class WakeConfig:
    name: str = "nova"
    threshold: float = 0.65
    verify_with_stt: bool = True


@dataclass(frozen=True)
class AudioConfig:
    device: str | int | None = None
    vad_aggressiveness: int = 2
    max_command_seconds: float = 6.0


@dataclass(frozen=True)
class SttConfig:
    model: str = "tiny.en"
    compute_type: str = "int8"


@dataclass(frozen=True)
class TtsConfig:
    rate: int = 175
    voice: str | None = None


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
    apps_aliases: dict[str, str] = field(default_factory=dict)
    search_url_template: str = "https://www.google.com/search?q={query}"
    lifecycle: LifecycleConfig = field(default_factory=LifecycleConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    language: str = "en"

    def validate(self) -> None:
        name = self.wake.name.strip().lower()
        if not 2 <= len(name) <= 24 or not name.replace(" ", "").replace("-", "").isalnum():
            raise ConfigError("Wake name must be 2 to 24 characters using letters, digits, spaces, or hyphens.")
        if name[0] in " -" or name[-1] in " -" or "  " in name:
            raise ConfigError("Wake name cannot start or end with a separator or contain repeated spaces.")
        if not 1 <= len(name.split()) <= 2: raise ConfigError("Wake name must contain one or two words.")
        if not 0 <= self.audio.vad_aggressiveness <= 3: raise ConfigError("VAD aggressiveness must be 0 to 3.")
        if self.audio.max_command_seconds <= 0: raise ConfigError("Maximum command time must be positive.")


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def load_config(path: Path) -> Config:
    if not path.exists(): return Config()
    try:
        with path.open("rb") as handle: raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"Could not read config at {path}: {exc}") from exc
    wake = _section(raw, "wake"); audio = _section(raw, "audio"); stt = _section(raw, "stt")
    tts = _section(raw, "tts"); lifecycle = _section(raw, "lifecycle"); logging = _section(raw, "logging")
    config = Config(WakeConfig(**{k: wake[k] for k in ("name", "threshold", "verify_with_stt") if k in wake}), AudioConfig(**{k: audio[k] for k in ("device", "vad_aggressiveness", "max_command_seconds") if k in audio}), SttConfig(**{k: stt[k] for k in ("model", "compute_type") if k in stt}), TtsConfig(**{k: tts[k] for k in ("rate", "voice") if k in tts}), dict(_section(raw, "apps").get("aliases", {})), str(_section(raw, "search").get("url_template", Config.search_url_template)), LifecycleConfig(**{k: lifecycle[k] for k in ("idle_timeout_minutes",) if k in lifecycle}), LoggingConfig(**{k: logging[k] for k in ("log_transcripts",) if k in logging}), str(raw.get("language", "en")))
    config.validate()
    return config


def save_config(path: Path, config: Config) -> None:
    config.validate(); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = asdict(config); payload["apps"] = {"aliases": payload.pop("apps_aliases")}; payload["search"] = {"url_template": payload.pop("search_url_template")}
    payload = _without_none(payload)
    fd, temp_name = tempfile.mkstemp(prefix=".config-", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "wb") as handle: tomli_w.dump(payload, handle)
        os.chmod(temp_name, 0o600); os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def _without_none(value: Any) -> Any:
    if isinstance(value, dict): return {key: _without_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list): return [_without_none(item) for item in value]
    return value
