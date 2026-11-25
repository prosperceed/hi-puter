from pathlib import Path

import pytest

from hi_puter.core.config import Config, WakeConfig, load_config, save_config
from hi_puter.core.errors import ConfigError


def test_config_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    save_config(path, Config(wake=WakeConfig(name="my assistant")))
    assert load_config(path).wake.name == "my assistant"


def test_invalid_wake_name() -> None:
    with pytest.raises(ConfigError):
        Config(wake=WakeConfig(name="bad name here")).validate()
