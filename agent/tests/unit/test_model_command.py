from pathlib import Path

import pytest
from typer.testing import CliRunner

from hi_puter.cli.app import app
from hi_puter.cli.commands import model as model_command
from hi_puter.core.config import Config, load_config, save_config
from hi_puter.core.paths import AppPaths

runner = CliRunner()


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppPaths:
    app_paths = AppPaths(
        tmp_path / "config", tmp_path / "data", tmp_path / "state", tmp_path / "run"
    )
    save_config(app_paths.config_file, Config())
    monkeypatch.setattr(model_command, "get_paths", lambda: app_paths)
    monkeypatch.setattr(model_command, "_downloaded", lambda _host: ["qwen3.5:2b", "qwen3.5:4b"])
    return app_paths


def test_lists_downloaded_models_and_marks_current(paths: AppPaths) -> None:
    result = runner.invoke(app, ["model"])
    assert result.exit_code == 0
    assert "Current model: qwen3.5:4b" in result.output
    assert "* qwen3.5:4b" in result.output and "  qwen3.5:2b" in result.output


def test_switches_to_a_downloaded_model(paths: AppPaths) -> None:
    result = runner.invoke(app, ["model", "qwen3.5:2b"])
    assert result.exit_code == 0
    assert load_config(paths.config_file).llm.model == "qwen3.5:2b"


def test_refuses_a_model_that_is_not_downloaded(paths: AppPaths) -> None:
    result = runner.invoke(app, ["model", "qwen3.5:9b"])
    assert result.exit_code == 1
    assert "ollama pull qwen3.5:9b" in result.output
    assert load_config(paths.config_file).llm.model == "qwen3.5:4b"
