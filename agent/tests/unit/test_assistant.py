from datetime import datetime
from itertools import pairwise
from pathlib import Path

from fakes import FakeAdapter, ScriptedModel, call

from hi_puter.brain.assistant import (
    GREETING,
    MODEL_FAILED,
    NO_MODEL,
    Assistant,
    count_parts,
    is_yes,
    speakable,
)
from hi_puter.brain.llm import ChatReply, ToolCall
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


def test_multi_step_request_runs_every_tool_and_speaks_results_without_a_summary_round() -> None:
    model = ScriptedModel(
        call("open_app", app="firefox"),
        call("web_search", query="local first apps"),
        call("set_volume", level=30),
    )
    assistant, adapter = make(model)
    request = "open firefox, look up local first apps and turn the volume to thirty"
    assert not assistant.is_quick(request)
    reply = assistant.handle(request)
    assert reply.text == (
        "Opening firefox. Searching the web for local first apps. Volume set to 30 percent."
    )
    assert reply.actions == ["open_app", "web_search", "set_volume"]
    assert [name for name, _ in adapter.calls] == ["open_app", "open_url", "volume_set"]
    # Three parts, three actions: no fourth round asking the model to summarize.
    assert len(model.requests) == 3
    # The model sees each tool's result before deciding the next step.
    assert [m["role"] for m in model.requests[-1][-2:]] == ["assistant", "tool"]


def test_parallel_tool_calls_need_only_one_model_round() -> None:
    both = ChatReply(
        "", [ToolCall("open_app", {"app": "spotify"}), ToolCall("set_mute", {"muted": True})]
    )
    model = ScriptedModel(both)
    assistant, adapter = make(model)
    reply = assistant.handle("open spotify and mute everything")
    assert reply.text == "Opening spotify. Muted."
    assert len(model.requests) == 1 and len(adapter.calls) == 2


def test_repeated_calls_are_not_run_twice_and_the_rest_still_happens() -> None:
    # The sequence a real qwen3.5:2b produced: it re-opened Spotify before getting to YouTube.
    model = ScriptedModel(
        call("open_app", app="spotify"),
        call("web_search", query="who wants to be a millionaire"),
        call("open_app", app="spotify"),
        call("open_website", url="youtube.com"),
    )
    assistant, adapter = make(model)
    reply = assistant.handle("open spotify, search who wants to be a millionaire and open youtube")
    assert [name for name, _ in adapter.calls] == ["open_app", "open_url", "open_url"]
    assert reply.text.endswith("Opened youtube.com.")
    nudge = model.requests[3][-1]
    assert nudge["role"] == "tool" and "Already done" in nudge["content"]


def test_a_model_that_keeps_repeating_is_stopped() -> None:
    model = ScriptedModel(*[call("current_time") for _ in range(4)])
    assistant, _ = make(model)
    reply = assistant.handle("tell me the time, then the time, then the time again")
    assert reply.text == "It's 3:04 PM on Wednesday, November 25."
    assert len(model.requests) == 3  # first call, one nudge, then stop


def test_compound_requests_go_to_the_model_even_if_the_regex_matches() -> None:
    assistant, _ = make(ScriptedModel())
    assert not assistant.is_quick("open firefox and search for cats")
    assert not assistant.is_quick("open the thing I was using yesterday for my essay")
    assert assistant.is_quick("open visual studio code")
    # Without a model the regex still gets its best attempt.
    assert make(None)[0].is_quick("open firefox and search for cats")


def test_tool_failures_are_spoken_not_raised() -> None:
    class NoScreenshots(FakeAdapter):
        def screenshot(self, interactive: bool = False) -> Path | None:
            raise NotImplementedError

    model = ScriptedModel(call("take_screenshot"))
    assistant = Assistant(build_toolbox(NoScreenshots(), Config()), model, name="nova")  # type: ignore[arg-type]
    reply = assistant.handle("grab my screen please")
    assert reply.text == "That isn't supported on this computer yet."
    assert reply.actions == []


def test_general_questions_still_get_the_models_answer() -> None:
    model = ScriptedModel(ChatReply("Tokyo."))
    assistant, _ = make(model)
    assert assistant.handle("what's the capital of japan").text == "Tokyo."


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


def test_step_limit_speaks_what_was_done() -> None:
    model = ScriptedModel(*[call("set_volume", level=level) for level in range(1, 9)])
    assistant, adapter = make(model)
    reply = assistant.handle("one, two, three, four, five, six, seven, eight")
    assert len(adapter.calls) == 5  # max_steps
    assert reply.text.endswith("Volume set to 5 percent.")


def test_count_parts() -> None:
    assert count_parts("open firefox") == 1
    assert count_parts("open spotify, search for jazz and open youtube") == 3
    assert count_parts("mute, then lock the screen") == 2


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


def test_system_prompt_is_stable_so_ollama_can_cache_it() -> None:
    first, _ = make(ScriptedModel())
    later = Assistant(
        first.toolbox, ScriptedModel(), name="nova", clock=lambda: datetime(2027, 1, 1, 23, 59)
    )  # type: ignore[arg-type]
    assert first._system_prompt() == later._system_prompt()


def test_prime_loads_the_model_and_keeps_the_greeting_as_the_first_turn() -> None:
    class Warmable(ScriptedModel):
        warmed = 0

        def warm(self) -> None:
            self.warmed += 1

    model = Warmable(ChatReply("Yes, I'm ready."), ChatReply("Paris."))
    assistant, _ = make(model)
    assistant.prime(timeout=300)
    assert model.warmed == 1
    greeting = model.requests[0]
    assert greeting[0] == {"role": "system", "content": assistant._system_prompt()}
    assert greeting[1] == {"role": "user", "content": GREETING}
    assistant.handle("what is the capital of france")
    # The first real request extends the greeting exchange the model already processed.
    assert model.requests[1][:3] == [*greeting, {"role": "assistant", "content": "Yes, I'm ready."}]


def _extends(previous: list[dict[str, object]], current: list[dict[str, object]]) -> bool:
    return current[: len(previous)] == previous


def test_every_model_request_extends_the_previous_one_exactly() -> None:
    """Hybrid models (qwen3.5) only reuse their cache when the new prompt continues the old one."""
    model = ScriptedModel(
        ChatReply("Tokyo."),
        ChatReply("About 14 million."),
        ChatReply(
            "", [ToolCall("open_app", {"app": "spotify"}), ToolCall("set_mute", {"muted": True})]
        ),
        call("power", action="shutdown"),
        ChatReply("Okay, it stays on."),
    )
    assistant, _ = make(model)
    assistant.handle("what's the capital of japan")
    assistant.handle("volume up")  # fast path: recorded, but no model call
    assistant.handle("and how many people live there")
    assistant.handle("open spotify and mute everything")
    pending = assistant.handle("I'm done, power the computer off")
    assert pending.pending is not None and pending.pending.from_model
    assistant.confirm(pending.pending, approved=False)
    assistant.handle("thanks, leave it on")
    requests = model.requests
    assert len(requests) == 5
    for before, after in pairwise(requests):
        assert _extends(before, after)
    # The open tool call was answered before the next user turn.
    last = requests[-1]
    assert last[-2] == {
        "role": "tool",
        "tool_name": "power",
        "content": "The user said no, so it was not done.",
    }


def test_memory_is_trimmed_at_a_user_turn_when_too_long() -> None:
    model = ScriptedModel(*[ChatReply("x" * 400) for _ in range(30)])
    assistant, _ = make(model)
    for number in range(30):
        assistant.handle(f"tell me something long number {number}")
    history = assistant._history
    assert sum(len(str(m["content"])) for m in history) <= assistant.memory_chars
    assert history[0]["role"] == "user"


def test_memory_is_forgotten_after_a_long_idle_period() -> None:
    times = iter(
        [datetime(2026, 11, 25, 9, 0), datetime(2026, 11, 25, 9, 5), datetime(2026, 11, 25, 10, 0)]
    )
    model = ScriptedModel(ChatReply("Hi."), ChatReply("Hello again."), ChatReply("Morning."))
    toolbox = build_toolbox(FakeAdapter(), Config())
    assistant = Assistant(toolbox, model, name="nova", clock=lambda: next(times))  # type: ignore[arg-type]
    assistant.handle("good morning to you")
    assistant.handle("how are you doing")
    assert len(model.requests[1]) == 4  # system, user, assistant, user
    assistant.handle("are you still there")  # 55 minutes later
    assert len(model.requests[2]) == 2  # system, user
