from enum import StrEnum


class State(StrEnum):
    LISTENING = "listening"; CAPTURING = "capturing"; TRANSCRIBING = "transcribing"; AWAITING_FOLLOWUP = "awaiting_followup"; EXECUTING = "executing"; AWAITING_CONFIRMATION = "awaiting_confirmation"; RESPONDING = "responding"; STOPPING = "stopping"


ALLOWED: dict[State, frozenset[State]] = {
    State.LISTENING: frozenset({State.CAPTURING, State.STOPPING}),
    State.CAPTURING: frozenset({State.TRANSCRIBING, State.STOPPING}),
    State.TRANSCRIBING: frozenset({State.EXECUTING, State.AWAITING_FOLLOWUP, State.LISTENING, State.STOPPING}),
    State.AWAITING_FOLLOWUP: frozenset({State.CAPTURING, State.LISTENING, State.STOPPING}),
    State.EXECUTING: frozenset({State.RESPONDING, State.AWAITING_CONFIRMATION, State.LISTENING, State.STOPPING}),
    State.AWAITING_CONFIRMATION: frozenset({State.EXECUTING, State.LISTENING, State.STOPPING}),
    State.RESPONDING: frozenset({State.LISTENING, State.STOPPING}),
    State.STOPPING: frozenset(),
}


def transition(current: State, next_state: State) -> State:
    if next_state not in ALLOWED[current]: raise ValueError(f"Invalid transition: {current} -> {next_state}")
    return next_state
