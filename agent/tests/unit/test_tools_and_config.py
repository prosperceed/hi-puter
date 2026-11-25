import dataclasses
from datetime import datetime
from pathlib import Path

import pytest
from fakes import FakeAdapter

from hi_puter.actions.registry import execute
from hi_puter.brain.tools import build_toolbox, normalize_url
from hi_puter.core.config import Config, LlmConfig, load_config, save_config
from hi_puter.core.errors import ConfigError
from hi_puter.nlu.matcher import match


def test_tools_follow_adapter_capabilities() -> None:
    names = build_toolbox(FakeAdapter(frozenset({"web"})), Config()).names()
    assert "web_search" in names and "set_volume" not in names and "power" not in names
    assert "current_time" in names and "system_status" in names


def test_volume_is_clamped_and_aliases_apply() -> None:
    adapter = FakeAdapter()
    config = dataclasses.replace(Config(), apps_aliases={"browser": "firefox"})
    toolbox = build_toolbox(adapter, config)
    assert toolbox.call("set_volume", {"level": 180}).text == "Volume set to 100 percent."
    toolbox.call("open_app", {"app": "Browser"})
    assert adapter.calls == [("volume_set", 100), ("open_app", "firefox")]


def test_bad_arguments_become_messages() -> None:
    toolbox = build_toolbox(FakeAdapter(), Config())
    assert not toolbox.call("set_volume", {}).ok
    assert not toolbox.call("open_website", {"url": "javascript:alert(1)"}).ok
    assert not toolbox.call("nope", {}).ok


def test_search_uses_template() -> None:
    adapter = FakeAdapter()
    build_toolbox(adapter, Config()).call("web_search", {"query": "local first & fast"})
    assert adapter.calls == [("open_url", "https://www.google.com/search?q=local+first+%26+fast")]


def test_normalize_url() -> None:
    assert normalize_url("youtube.com") == "https://youtube.com"
    assert normalize_url("http://example.org/a") == "http://example.org/a"
    assert normalize_url("localhost:3000") == "https://localhost:3000"
    for bad in ("file:///etc/passwd", "javascript:alert(1)", "mailto:a@b.c"):
        with pytest.raises(ValueError):
            normalize_url(bad)


def test_time_is_spoken_naturally() -> None:
    toolbox = build_toolbox(FakeAdapter(), Config(), clock=lambda: datetime(2026, 11, 25, 9, 5))
    assert toolbox.call("current_time", {}).text == "It's 9:05 AM on Wednesday, November 25."


def test_whisper_style_percentages_match() -> None:
    phrases = (
        "Set volume to 30%.",
        "set the volume to 30 percent",
        "Volume to 30 %",
        "turn the volume to 30",
    )
    for heard in phrases:
        intent = match(heard)
        assert intent is not None and intent.slots["level"] == "30", heard


def test_registry_routes_regex_intents_through_tools() -> None:
    adapter = FakeAdapter()
    intent = match("search for cats")
    assert intent is not None
    assert execute(intent, adapter).ok
    assert adapter.calls[0][0] == "open_url"
    unmute = match("unmute")
    assert unmute is not None
    execute(unmute, adapter, text="unmute")
    assert adapter.calls[-1] == ("set_mute", False)


def test_new_sections_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    config = dataclasses.replace(Config(), llm=LlmConfig(model="qwen3.5:2b", max_steps=3))
    save_config(path, config)
    loaded = load_config(path)
    assert loaded.llm.model == "qwen3.5:2b" and loaded.llm.max_steps == 3
    assert loaded.voice.listening_phrase == "Listening."


def test_old_config_files_still_load(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        '[wake]\nname = "jarvis"\nthreshold = 0.65\n[stt]\nmodel = "tiny.en"\nunknown = 1\n'
    )
    loaded = load_config(path)
    assert loaded.wake.name == "jarvis" and loaded.stt.model == "tiny.en" and loaded.llm.enabled


def test_remote_model_hosts_need_opt_in() -> None:
    remote = dataclasses.replace(Config(), llm=LlmConfig(host="http://gpu-box.lan:11434"))
    with pytest.raises(ConfigError, match="allow_remote"):
        remote.validate()
    dataclasses.replace(remote, llm=dataclasses.replace(remote.llm, allow_remote=True)).validate()
