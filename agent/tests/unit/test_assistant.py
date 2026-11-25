from datetime import datetime
from pathlib import Path

from fakes import FakeAdapter, ScriptedModel, call

from hi_puter.brain.assistant import (
    MODEL_FAILED,
    NO_MODEL,
    TOO_MANY_STEPS,
    Assistant,
    is_yes,
    speakable,
)
from hi_puter.brain.llm import ChatReply
from hi_puter.brain.tools import build_toolbox
from hi_puter.core.config import Config
from hi_puter.core.errors import ModelError

NOW = datetime(2026, 11, 25, 15, 4)


def make(model: object = None, tmp: Path | None = None) -> tuple[Assistant, FakeAdapter]:
    adapter = FakeAdapter()
    toolbox = build_toolbox(
        adapter, Config(), notes_file=tmp / "notes.md" if tmp else None, clock=lambda: NOW
    )
    return Assistant(toolbox, model, name="nova", clock=lambda: NOW), adapter  # type: ignore[arg-type]


def test_simple_command_skips_the_model() -> None:
    model = ScriptedModel()
    assistant, adapter = make(model)
    assert assistant.is_quick("open firefox")
    reply = assistant.handle("open Firefox")
    assert reply.text == "Opening firefox."
    assert adapter.calls == [("open_app", "firefox")]
    assert model.requests == []


def test_multi_step_request_runs_every_tool_then_answers() -> None:
    model = ScriptedModel(
        call("open_app", app="firefox"),
        call("web_search", query="local first apps"),
        call("set_volume", level=30),
        ChatReply("Firefox is open with your search, and volume is at 30 percent."),
    )
    assistant, adapter = make(model)
    request = "open firefox, look up local first apps and turn the volume to thirty"
    assert not assistant.is_quick(request)
    reply = assistant.handle(request)
    assert reply.text.startswith("Firefox is open")
    assert reply.actions == ["open_app", "web_search", "set_volume"]
    assert [name for name, _ in adapter.calls] == ["open_app", "open_url", "volume_set"]
    # The model sees each tool's result before deciding the next step.
    last = model.requests[-1]
    assert [m["role"] for m in last[-2:]] == ["assistant", "tool"]
    assert last[-1]["content"] == "Volume set to 30 percent."


def test_compound_requests_go_to_the_model_even_if_the_regex_matches() -> None:
    assistant, _ = make(ScriptedModel())
    assert not assistant.is_quick("open firefox and search for cats")
    assert not assistant.is_quick("open the thing I was using yesterday for my essay")
    assert assistant.is_quick("open visual studio code")
    # Without a model the regex still gets its best attempt.
    assert make(None)[0].is_quick("open firefox and search for cats")


def test_tool_failures_are_reported_to_the_model_not_raised() -> None:
    model = ScriptedModel(call("take_screenshot"), ChatReply("I couldn't take a screenshot here."))
    assistant, _ = make(model)
    reply = assistant.handle("grab my screen please")
    assert reply.text == "I couldn't take a screenshot here."
    assert model.requests[-1][-1]["content"] == "That isn't supported on this computer yet."


def test_risky_action_from_the_model_waits_for_confirmation() -> None:
    model = ScriptedModel(call("power", action="shutdown"))
    assistant, adapter = make(model)
    reply = assistant.handle("I'm done for today, turn everything off")
    assert reply.pending is not None
    assert reply.text == "Shut down the computer? Say yes to confirm."
    assert adapter.calls == []
    assert assistant.confirm(reply.pending, approved=False).text == "Okay, I won't."
    assert adapter.calls == []
    assert assistant.confirm(reply.pending, approved=True).text == "Shutting down."
    assert adapter.calls == [("power", "shutdown")]


def test_regex_power_command_also_needs_confirmation() -> None:
    assistant, adapter = make(None)
    reply = assistant.handle("restart")
    assert reply.pending is not None and adapter.calls == []


def test_conversation_memory_reaches_the_model_and_resets() -> None:
    model = ScriptedModel(
        ChatReply("Paris."), ChatReply("About two million people."), ChatReply("Hi.")
    )
    assistant, _ = make(model)
    assistant.handle("what is the capital of france")
    assistant.handle("and how many people live there")
    second = model.requests[1]
    assert [m["content"] for m in second[1:3]] == ["what is the capital of france", "Paris."]
    assistant.reset()
    assistant.handle("hello there friend")
    assert len(model.requests[2]) == 2  # system + user only


def test_without_a_model_only_simple_commands_work() -> None:
    assistant, _ = make(None)
    assert assistant.handle("write me a poem about autumn").text == NO_MODEL
    assert assistant.handle("volume up").text == "Volume up."


def test_model_errors_fall_back_politely() -> None:
    class Broken:
        def chat(self, *_args: object) -> ChatReply:
            raise ModelError("connection refused")

    assistant, _ = make(Broken())
    assert assistant.handle("summarize my day").text == MODEL_FAILED


def test_step_limit() -> None:
    model = ScriptedModel(*[call("current_time") for _ in range(5)])
    assistant, _ = make(model)
    assert assistant.handle("keep checking the clock forever").text == TOO_MANY_STEPS


def test_stop_ends_the_session() -> None:
    assistant, _ = make(None)
    assert assistant.handle("stop listening").end_session


def test_notes_are_saved(tmp_path: Path) -> None:
    model = ScriptedModel(call("write_note", text="buy  milk"), ChatReply("Noted."))
    assistant, _ = make(model, tmp_path)
    assistant.handle("remind me to buy milk")
    assert (tmp_path / "notes.md").read_text() == "- 2026-11-25 15:04 buy milk\n"


def test_speakable_strips_markdown_and_reasoning() -> None:
    text = "<think>plan</think>**Sure!** Here's [the link](https://x.y):\n- one\n- two"
    assert speakable(text) == "Sure! Here's the link: one two"
    long = "This is a sentence. " * 40
    assert len(speakable(long)) <= 420 and speakable(long).endswith(".")


def test_is_yes() -> None:
    assert is_yes("Yes please") and is_yes("yeah, go ahead") and is_yes("okay do it")
    assert not is_yes("no") and not is_yes("not sure") and not is_yes(None)
