from threading import Event

from fakes import EchoStt, FakeAdapter, FakeSource, RecordingTts, ScriptedModel, call

from hi_puter.brain.assistant import Assistant
from hi_puter.brain.llm import ChatReply
from hi_puter.brain.tools import build_toolbox
from hi_puter.core.config import Config, VoiceConfig
from hi_puter.runtime.voice_loop import WAKE_WINDOW_BYTES, VoiceLoop


def make_loop(*utterances: str | None, model: object = None, voice: VoiceConfig | None = None):  # type: ignore[no-untyped-def]
    adapter = FakeAdapter()
    assistant = Assistant(build_toolbox(adapter, Config()), model, name="nova")  # type: ignore[arg-type]
    chimes: list[int] = []
    source = FakeSource(*utterances)
    tts = RecordingTts()
    loop = VoiceLoop(
        source=source,
        stt=EchoStt(),
        tts=tts,
        assistant=assistant,
        wake_name="nova",
        wake_threshold=0.8,
        voice=voice or VoiceConfig(),
        stop=Event(),
        chime=lambda: chimes.append(1),
    )
    return loop, tts, adapter, source, chimes


def test_wake_name_then_request() -> None:
    loop, tts, adapter, source, chimes = make_loop("Nova", "open firefox", None)
    loop.step()
    assert chimes == [1]
    assert tts.said == ["Listening.", "Opening firefox."]
    assert adapter.calls == [("open_app", "firefox")]
    assert source.timeouts == [None, 8.0, 6.0]  # passive, request, follow-up


def test_request_in_one_breath_skips_listening() -> None:
    loop, tts, adapter, _, chimes = make_loop("hey nova, volume up", None)
    loop.step()
    assert chimes == [] and tts.said == ["Volume up."]
    assert adapter.calls == [("volume_change", 10)]


def test_other_speech_is_ignored() -> None:
    loop, tts, adapter, _, _ = make_loop("I think nova is a nice name")
    loop.step()
    assert tts.said == [] and adapter.calls == []


def test_silence_after_wake_name_returns_to_passive() -> None:
    loop, tts, adapter, _, _ = make_loop("nova", None)
    loop.step()
    assert tts.said == ["Listening."] and adapter.calls == []


def test_follow_up_without_wake_name() -> None:
    loop, tts, adapter, _, _ = make_loop("nova open firefox", "and mute", "set volume to 20", None)
    loop.step()
    # "and mute" is not a simple command and there is no model, so it gets the fallback reply.
    assert tts.said[0] == "Opening firefox."
    assert tts.said[-1] == "Volume set to 20 percent."
    assert ("volume_set", 20) in adapter.calls


def test_model_request_says_working_first() -> None:
    model = ScriptedModel(call("set_volume", level=25), ChatReply("Volume is at 25 percent."))
    loop, tts, _, _, _ = make_loop(
        "nova", "make it a bit quieter, like a quarter", None, model=model
    )
    loop.step()
    assert tts.said == ["Listening.", "On it.", "Volume is at 25 percent."]


def test_confirmation_by_voice() -> None:
    loop, tts, adapter, _, _ = make_loop("nova", "shut down", "yes", None)
    loop.step()
    assert tts.said[1:] == ["Shut down the computer? Say yes to confirm.", "Shutting down."]
    assert adapter.calls == [("power", "shutdown")]


def test_no_answer_cancels_confirmation() -> None:
    loop, tts, adapter, _, _ = make_loop("nova shut down", None)
    loop.step()
    assert tts.said[-1] == "Okay, I won't." and adapter.calls == []


def test_stop_ends_session_but_keeps_the_conversation_for_the_cache() -> None:
    model = ScriptedModel(ChatReply("Hi!"))
    loop, tts, _, source, _ = make_loop(
        "nova say hello to me", "stop listening", "volume up", model=model
    )
    loop.step()
    assert tts.said == ["On it.", "Hi!", "Okay."]
    assert source.utterances[0] == "volume up"  # not consumed by the ended session
    assert [m["content"] for m in loop.assistant._history][:2] == ["say hello to me", "Hi!"]


def test_own_voice_is_flushed_after_speaking() -> None:
    loop, tts, _, source, _ = make_loop("nova", "volume down", None)
    loop.step()
    assert source.flushes == len(tts.said)


def test_follow_up_can_be_disabled() -> None:
    voice = VoiceConfig(followup_seconds=0)
    loop, _, _, source, _ = make_loop("nova volume up", "volume up", voice=voice)
    loop.step()
    assert source.utterances[0] == "volume up"


def test_background_talk_is_only_transcribed_at_the_start() -> None:
    class CountingStt:
        def __init__(self) -> None:
            self.lengths: list[int] = []

        def transcribe(self, audio: bytes) -> str:
            self.lengths.append(len(audio))
            return "so anyway we went to the market"

    loop, tts, _, source, _ = make_loop()
    stt = CountingStt()
    loop.stt = stt
    source.utterances.append("x" * 400_000)  # ~12 s of someone else talking
    loop.step()
    assert stt.lengths == [WAKE_WINDOW_BYTES] and tts.said == []


def test_long_request_after_wake_name_is_fully_transcribed() -> None:
    class HeadOrFull:
        def transcribe(self, audio: bytes) -> str:
            return "nova" if len(audio) <= WAKE_WINDOW_BYTES else "nova volume up"

    loop, _, adapter, source, _ = make_loop()
    loop.stt = HeadOrFull()
    source.utterances.append("x" * 200_000)
    loop.step()
    assert adapter.calls == [("volume_change", 10)]
