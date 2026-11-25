from hi_puter.nlu.matcher import match


def test_open_app_and_normalization() -> None:
    result = match("Hey, please open Firefox!")
    assert result is not None and result.action == "open_app" and result.slots["app"] == "firefox"


def test_volume_is_clamped() -> None:
    result = match("set volume to 150")
    assert result is not None and result.slots["level"] == "100"


def test_confirmation_risk() -> None:
    result = match("shut down")
    assert result is not None and result.risk.value == "confirm"


def test_unknown() -> None:
    assert match("play a song") is None


def test_everyday_phrases_skip_the_model() -> None:
    expected = {
        "louder": "volume_up",
        "turn it down": "volume_down",
        "it's way too loud in here": "volume_down",
        "open youtube": "open_site",
        "go to github.com": "open_site",
        "lock my computer": "lock",
        "what's the date": "time",
        "turn off the computer": "shutdown",
        "never mind": "stop",
        "stop": "stop",
        "look up the weather in lagos": "search",
    }
    for text, intent_id in expected.items():
        result = match(text)
        assert result is not None and result.id == intent_id, text


def test_sites_open_in_the_browser() -> None:
    from hi_puter.actions.registry import intent_call

    youtube = match("open YouTube")
    domain = match("go to docs.python.org.")
    assert youtube is not None and intent_call(youtube) == ("open_website", {"url": "youtube.com"})
    assert domain is not None and intent_call(domain) == (
        "open_website",
        {"url": "docs.python.org"},
    )
