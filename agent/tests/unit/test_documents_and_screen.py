from datetime import datetime
from pathlib import Path
from threading import Event

import pytest
from fakes import EchoStt, FakeAdapter, FakeSource, RecordingTts, ScriptedModel, call

from hi_puter.actions.registry import intent_call
from hi_puter.brain.assistant import Assistant
from hi_puter.brain.llm import ChatReply
from hi_puter.brain.tools import build_toolbox
from hi_puter.brain.writer import (
    MAX_DOCUMENT_TOKENS,
    DocumentRequest,
    Writer,
    clean_markdown,
    safe_filename,
    tidy_for,
    title_of,
    topic_phrase,
)
from hi_puter.core.config import Config, VoiceConfig
from hi_puter.core.errors import ModelError
from hi_puter.nlu.matcher import match
from hi_puter.runtime.voice_loop import VoiceLoop, split_finished

LETTER = """# Request to Repair the Leaking Roof

Dear [Landlord name],

The roof above the kitchen has been leaking since Monday, and water now drips onto the
counter whenever it rains. Please arrange a repair this week.

Kind regards,
Prosper
"""
NOW = datetime(2026, 11, 25, 12, 0)


def make(tmp_path: Path, *replies: ChatReply):  # type: ignore[no-untyped-def]
    adapter = FakeAdapter()
    model = ScriptedModel(*replies)
    writer = Writer(model, tmp_path / "Hi-Puter", clock=lambda: NOW)
    toolbox = build_toolbox(adapter, Config(), writer=writer)
    assistant = Assistant(toolbox, model, name="nova", writer=writer)
    return assistant, adapter, model, writer


# -- phrases ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "call_"),
    [
        (
            "write a letter to my landlord about the leaking roof",
            (
                "start_document",
                {"kind": "letter", "topic": "to my landlord about the leaking roof"},
            ),
        ),
        ("help me draft an email", ("start_document", {"kind": "email", "topic": ""})),
        ("write a document", ("start_document", {"kind": "document", "topic": ""})),
        ("open the document", ("open_document", {})),
        ("start recording", ("start_recording", {"seconds": None})),
        ("record my screen for 30 seconds", ("start_recording", {"seconds": 30})),
        ("record the screen for two minutes", ("start_recording", {"seconds": 120})),
        ("bring up the screen recorder", ("start_recording", {"seconds": None})),
        ("stop recording", ("stop_recording", {})),
        ("take a screenshot", ("take_screenshot", {})),
        ("take a screenshot of a window", ("take_screenshot", {"mode": "choose"})),
        ("bring up the screenshot tool", ("take_screenshot", {"mode": "choose"})),
    ],
)
def test_phrases(text: str, call_: tuple[str, dict[str, object]]) -> None:
    intent = match(text)
    assert intent is not None, text
    assert intent_call(intent, text) == call_


def test_phrases_that_must_not_change() -> None:
    assert match("write a note to buy milk") is None  # still the quick-notes tool, via the model
    stop, app = match("stop"), match("start spotify")
    assert stop is not None and stop.id == "stop"
    assert app is not None and app.id == "open_app"


# -- screen tools ----------------------------------------------------------------------------


def test_screenshot_and_recording_tools() -> None:
    adapter = FakeAdapter()
    toolbox = build_toolbox(adapter, Config())
    assert toolbox.call("take_screenshot", {}).text == "Screenshot saved to Screenshots."
    assert toolbox.call("take_screenshot", {"mode": "choose"}).text.startswith("I've opened")
    assert toolbox.call("stop_recording", {}).text == "Nothing is being recorded."
    assert toolbox.call("start_recording", {"seconds": 90}).text == (
        "Recording the screen for 1 minute and 30 seconds."
    )
    assert toolbox.call("stop_recording", {}).text == "Recording saved to Screencasts."
    assert ("start_recording", 90) in adapter.calls


# -- writer ----------------------------------------------------------------------------------


def test_clean_markdown_strips_chatter_and_fences() -> None:
    chatty = "Sure! Here is your letter:\n\n```markdown\n" + LETTER + "```\nHope this helps!"
    cleaned = clean_markdown(chatty)
    assert cleaned.startswith("# Request to Repair")
    assert "Sure!" not in cleaned
    assert clean_markdown("**My Title**\nBody text here.").startswith("# My Title")


def test_titles_filenames_and_topics() -> None:
    assert title_of(LETTER) == "Request to Repair the Leaking Roof"
    assert safe_filename("Q3: Plan / Budget?") == "Q3 Plan Budget"
    assert topic_phrase("to my landlord about rent") == " to my landlord about rent"
    assert topic_phrase("rent") == " about rent"
    assert topic_phrase("") == ""


def test_writer_saves_a_titled_document(tmp_path: Path) -> None:
    model = ScriptedModel(ChatReply(LETTER))
    writer = Writer(model, tmp_path, clock=lambda: NOW)
    document = writer.write(
        "um so the roof is leaking since monday no wait since sunday, please fix it",
        DocumentRequest("letter", "to my landlord"),
    )
    assert document.path == tmp_path / "2026-11-25 Request to Repair the Leaking Roof.md"
    assert document.path.read_text() == LETTER
    assert document.title == "Request to Repair the Leaking Roof" and document.words > 20
    system, user = model.requests[0]
    assert "Keep every point" in str(system["content"]) and "letter" in str(system["content"])
    assert str(user["content"]).startswith("Write a letter to my landlord.")
    assert "no wait since sunday" in str(user["content"])  # the model sees the raw words
    assert model.max_tokens == [MAX_DOCUMENT_TOKENS]


def test_same_title_never_overwrites(tmp_path: Path) -> None:
    writer = Writer(
        ScriptedModel(ChatReply(LETTER), ChatReply(LETTER)), tmp_path, clock=lambda: NOW
    )
    first = writer.write("roof", DocumentRequest())
    second = writer.write("roof again", DocumentRequest())
    assert first.path != second.path and second.path.name.endswith("(2).md")


def test_revise_updates_the_same_file(tmp_path: Path) -> None:
    shorter = "# Roof Repair\n\nDear landlord, the kitchen roof leaks. Please fix it this week.\n"
    model = ScriptedModel(ChatReply(LETTER), ChatReply(shorter))
    writer = Writer(model, tmp_path, clock=lambda: NOW)
    first = writer.write("roof", DocumentRequest("letter"))
    revised = writer.revise("make it much shorter")
    assert revised.path == first.path and first.path.read_text() == shorter
    assert "Instruction: make it much shorter" in str(model.requests[1][1]["content"])
    assert LETTER.strip() in str(model.requests[1][1]["content"])


def test_empty_model_output_is_an_error(tmp_path: Path) -> None:
    writer = Writer(ScriptedModel(ChatReply("")), tmp_path)
    with pytest.raises(ModelError):
        writer.write("something", DocumentRequest())


# -- assistant -------------------------------------------------------------------------------


def test_fast_phrase_starts_dictation(tmp_path: Path) -> None:
    assistant, _, model, _ = make(tmp_path)
    reply = assistant.handle("write a letter to my landlord about the leaking roof")
    assert reply.dictation == DocumentRequest("letter", "to my landlord about the leaking roof")
    assert reply.text.startswith("Okay. Tell me what the letter to my landlord")
    assert model.requests == []


def test_model_can_start_dictation(tmp_path: Path) -> None:
    assistant, _, _, _ = make(tmp_path, call("start_document", kind="cover letter"))
    reply = assistant.handle("I need something to send with my job application")
    assert reply.dictation == DocumentRequest("cover letter", "")


def test_write_document_saves_opens_and_remembers(tmp_path: Path) -> None:
    assistant, adapter, _, writer = make(tmp_path, ChatReply(LETTER))
    reply = assistant.write_document("the roof leaks, fix it", DocumentRequest("letter"))
    assert writer.last is not None and writer.last.path.exists()
    assert ("open_path", str(writer.last.path)) in adapter.calls
    assert "Request to Repair the Leaking Roof" in reply.text and "opened it" in reply.text
    assert assistant._history[-2]["content"].startswith("(I dictated a letter")


def test_failed_writing_keeps_the_dictation(tmp_path: Path) -> None:
    class Down(ScriptedModel):
        def chat(self, *args: object, **kwargs: object) -> ChatReply:
            raise ModelError("timed out")

    writer = Writer(Down(), tmp_path / "Hi-Puter", clock=lambda: NOW)
    assistant = Assistant(
        build_toolbox(FakeAdapter(), Config(), writer=writer),
        Down(),
        writer=writer,
        clock=lambda: NOW,
    )
    reply = assistant.write_document("my important words", DocumentRequest())
    assert "saved what you said" in reply.text
    saved = tmp_path / "Hi-Puter" / "2026-11-25 12-00 Dictation.md"
    assert "my important words" in saved.read_text()


def test_nothing_dictated(tmp_path: Path) -> None:
    assistant, _, model, _ = make(tmp_path)
    assert "didn't hear anything" in assistant.write_document("  ", DocumentRequest()).text
    assert model.requests == []


def test_revise_and_open_tools(tmp_path: Path) -> None:
    assistant, _, _, _ = make(tmp_path, ChatReply(LETTER), ChatReply(LETTER))
    toolbox = assistant.toolbox
    assert "no document" in toolbox.call("revise_document", {"instruction": "shorter"}).text
    assistant.write_document("roof", DocumentRequest("letter"))
    assert toolbox.call("revise_document", {"instruction": "more formal"}).text.startswith(
        "Updated Request to Repair"
    )
    assert toolbox.call("open_document", {}).ok


# -- voice -----------------------------------------------------------------------------------


def test_split_finished() -> None:
    assert split_finished("Done.") == (True, "")
    assert split_finished("and pay by Friday. I'm done.") == (True, "and pay by Friday")
    assert split_finished("the work is done") == (False, "the work is done")


def test_spoken_document_end_to_end(tmp_path: Path) -> None:
    assistant, _, model, writer = make(tmp_path, ChatReply(LETTER))
    source = FakeSource(
        "nova write a letter to my landlord",
        "the roof over the kitchen has been leaking",
        "since monday, please fix it this week",
        "done",
        None,
    )
    tts = RecordingTts()
    loop = VoiceLoop(
        source=source, stt=EchoStt(), tts=tts, assistant=assistant, wake_name="nova",
        wake_threshold=0.8, voice=VoiceConfig(), stop=Event(), dictation_pause_seconds=10,
    )  # fmt: skip
    loop.step()
    assert tts.said[0].startswith("Okay. Tell me what the letter to my landlord should say")
    assert tts.said[1] == "Got it. Writing your letter now; this can take a minute."
    assert tts.said[2].startswith("I wrote your letter, Request to Repair the Leaking Roof")
    dictated = str(model.requests[0][1]["content"])
    assert "leaking since monday, please fix it this week" in dictated
    assert "done" not in dictated.split("said:")[1]
    assert writer.last is not None


def test_silence_ends_dictation(tmp_path: Path) -> None:
    assistant, _, model, _ = make(tmp_path, ChatReply(LETTER))
    source = FakeSource("nova write a document", "remind the team about friday's demo", None)
    loop = VoiceLoop(
        source=source, stt=EchoStt(), tts=RecordingTts(), assistant=assistant, wake_name="nova",
        wake_threshold=0.8, voice=VoiceConfig(followup_seconds=0), stop=Event(),
        dictation_pause_seconds=7,
    )  # fmt: skip
    loop.step()
    assert source.timeouts[1:3] == [16.0, 7]  # time to start, then the pause that ends it
    assert "friday's demo" in str(model.requests[0][1]["content"])


def test_letters_lose_memo_headers_and_bold() -> None:
    raw = (
        "# Roof Repair\n**To:** [Landlord]\n**Date:** [Date]\n**Subject:** Roof\n\n"
        "Dear [Landlord],\n\nPlease fix it **this week**.\n\n*   Mornings before 11\n"
    )
    letter = tidy_for("letter", raw)
    assert "To:" not in letter and "Subject:" not in letter and "**" not in letter
    assert "Please fix it this week." in letter and "- Mornings before 11" in letter
    email = tidy_for("email", "# Hi\nSubject: Demo moved\n\n**Friday** at 3pm.\n")
    assert "Subject: Demo moved" in email and "**" not in email
    report = "# Q3\n\n**Revenue** grew.\n"
    assert tidy_for("report", report) == report  # other kinds keep their formatting
