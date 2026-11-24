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
