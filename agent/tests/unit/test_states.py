import pytest

from hi_puter.runtime.states import State, transition


def test_valid_transition() -> None:
    assert transition(State.LISTENING, State.CAPTURING) is State.CAPTURING


def test_invalid_transition() -> None:
    with pytest.raises(ValueError):
        transition(State.LISTENING, State.EXECUTING)
