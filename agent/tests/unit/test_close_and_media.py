import os

import psutil
import pytest
from fakes import FakeAdapter

from hi_puter.actions.registry import intent_call
from hi_puter.adapters import processes
from hi_puter.adapters.linux import mpris
from hi_puter.brain.tools import build_toolbox
from hi_puter.core.config import Config
from hi_puter.core.errors import ActionError
from hi_puter.nlu.matcher import match

SPOTIFY = "org.mpris.MediaPlayer2.spotify"
FIREFOX = "org.mpris.MediaPlayer2.firefox.instance_1_42"


# -- phrases ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "call"),
    [
        ("close firefox", ("close_app", {"app": "firefox"})),
        ("please close spotify for me", ("close_app", {"app": "spotify"})),
        ("quit the spotify app", ("close_app", {"app": "spotify"})),
        ("exit visual studio code", ("close_app", {"app": "visual studio code"})),
        ("pause", ("media_control", {"action": "pause", "app": None})),
        ("stop the music", ("media_control", {"action": "pause", "app": None})),
        ("put my music on hold", ("media_control", {"action": "pause", "app": None})),
        ("pause spotify", ("media_control", {"action": "pause", "app": "spotify"})),
        ("resume", ("media_control", {"action": "play", "app": None})),
        ("play the music on spotify", ("media_control", {"action": "play", "app": "spotify"})),
        ("next song", ("media_control", {"action": "next", "app": None})),
        ("skip this song", ("media_control", {"action": "next", "app": None})),
        ("next track on spotify", ("media_control", {"action": "next", "app": "spotify"})),
        ("go back a song", ("media_control", {"action": "previous", "app": None})),
        ("previous track", ("media_control", {"action": "previous", "app": None})),
    ],
)
def test_close_and_media_phrases(text: str, call: tuple[str, dict[str, object]]) -> None:
    intent = match(text)
    assert intent is not None, text
    assert intent_call(intent, text) == call


def test_phrases_that_must_keep_their_meaning() -> None:
    shutdown = match("shut down the computer")
    stop = match("stop")
    assert shutdown is not None and shutdown.id == "shutdown"
    assert stop is not None and stop.id == "stop"
    # Not instant: these go to the model, which should say it can't (no "close everything").
    assert match("close all my apps") is None
    assert match("play some jazz") is None


# -- tools -----------------------------------------------------------------------------------


def test_close_and_media_tools() -> None:
    adapter = FakeAdapter()
    toolbox = build_toolbox(adapter, Config())
    assert toolbox.call("close_app", {"app": "Spotify"}).text == "Closed Spotify."
    assert toolbox.call("close_app", {"app": "gimp"}).text == "gimp isn't running."
    assert toolbox.call("media_control", {"action": "next"}).text == "Next track on Spotify."
    assert not toolbox.call("media_control", {"action": "rewind"}).ok
    assert adapter.calls[:3] == [
        ("close_app", "Spotify"),
        ("close_app", "gimp"),
        ("media", ("next", None)),
    ]


def test_media_tool_is_hidden_without_media_support() -> None:
    names = build_toolbox(FakeAdapter(frozenset({"apps"})), Config()).names()
    assert "close_app" in names and "media_control" not in names


# -- closing processes -----------------------------------------------------------------------


def test_process_names_from_speech_and_programs() -> None:
    assert processes.process_names("the Chrome browser", ["google-chrome-stable"]) == {
        "chrome",
        "google-chrome-stable",
    }
    assert "code" in processes.process_names("visual studio code", ["/usr/share/code/code"])
    assert processes.process_names("the app") == set()


def test_never_targets_its_own_process_chain() -> None:
    me = psutil.Process()
    own = {me.name().lower()} | {parent.name().lower() for parent in me.parents()}
    found = processes.find_app_processes(own)
    chain = {me.pid} | {parent.pid for parent in me.parents()}
    assert not {process.pid for process in found} & chain
    assert all(process.uids().real == os.getuid() for process in found)


def test_protected_processes_are_never_matched() -> None:
    found = processes.find_app_processes({"systemd", "gnome-shell", "pipewire", "ollama"})
    assert found == []


def test_close_needs_an_app_name() -> None:
    with pytest.raises(ActionError, match="Which app"):
        processes.close_app("the app")


# -- media over MPRIS ------------------------------------------------------------------------


def test_choose_player() -> None:
    both = [SPOTIFY, FIREFOX]
    assert mpris.choose_player(both, "Spotify", []) == SPOTIFY
    assert mpris.choose_player(both, "firefox", []) == FIREFOX
    assert mpris.choose_player(both, "vlc", []) is None
    assert mpris.choose_player(both, None, [FIREFOX]) == FIREFOX  # whatever is playing
    assert mpris.choose_player([SPOTIFY], None, []) == SPOTIFY  # the only one open
    assert mpris.choose_player(both, None, []) is None  # ambiguous: ask


class FakeBus:
    def __init__(self, deny: bool = False) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.deny = deny

    def __call__(self, *args: str) -> str:
        self.calls.append(args)
        method = args[args.index("--method") + 1]
        if method == "org.freedesktop.DBus.ListNames":
            return f"(['org.freedesktop.DBus', '{SPOTIFY}', '{FIREFOX}'],)"
        if method == "org.freedesktop.DBus.Properties.Get":
            return "(<'Playing'>,)" if args[1] == SPOTIFY else "(<'Paused'>,)"
        if self.deny:
            raise ActionError("GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: AppArmor")
        return "()"


def test_control_sends_the_mpris_method_to_the_named_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bus = FakeBus()
    monkeypatch.setattr(mpris, "_gdbus", bus)
    assert mpris.control("next", "spotify") == "Spotify"
    sent = bus.calls[-1]
    assert sent[sent.index("--dest") + 1] == SPOTIFY
    assert sent[sent.index("--method") + 1] == "org.mpris.MediaPlayer2.Player.Next"


def test_control_without_an_app_uses_the_one_playing(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = FakeBus()
    monkeypatch.setattr(mpris, "_gdbus", bus)
    assert mpris.control("pause") == "Spotify"
    assert bus.calls[-1][bus.calls[-1].index("--method") + 1].endswith(".Pause")


def test_sandbox_denial_explains_how_to_fix_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mpris, "_gdbus", FakeBus(deny=True))
    with pytest.raises(ActionError, match="Start Hi-Puter from a normal terminal"):
        mpris.control("play", "spotify")


def test_missing_app_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mpris, "_gdbus", FakeBus())
    with pytest.raises(ActionError, match="Vlc isn't open"):
        mpris.control("play", "vlc")


# -- the model may only close apps the user named -------------------------------------------


def _assistant(*replies: object):  # type: ignore[no-untyped-def]
    from fakes import ScriptedModel

    from hi_puter.brain.assistant import Assistant

    adapter = FakeAdapter()
    model = ScriptedModel(*replies)  # type: ignore[arg-type]
    return Assistant(build_toolbox(adapter, Config()), model, name="nova"), adapter, model


def test_model_cannot_close_apps_the_user_never_named() -> None:
    from hi_puter.brain.llm import ChatReply, ToolCall

    guesses = ChatReply(
        "", [ToolCall("close_app", {"app": app}) for app in ("firefox", "code", "gnome-terminal")]
    )
    assistant, adapter, _ = _assistant(guesses)
    reply = assistant.handle("close all my apps")
    assert reply.text == "Which app should I close?"
    assert adapter.calls == []


def test_model_can_close_an_app_named_now_or_just_before() -> None:
    from fakes import call

    from hi_puter.brain.llm import ChatReply

    assistant, adapter, _ = _assistant(
        ChatReply("Spotify is a music app."),
        call("close_app", app="Spotify"),
        ChatReply("Spotify is closed."),
    )
    assistant.handle("what is spotify exactly")
    reply = assistant.handle("I'm done with it, get rid of it")  # "it" = the previous request
    assert reply.text == "Spotify is closed."
    assert adapter.calls == [("close_app", "Spotify")]


def test_a_refused_guess_stays_quiet_when_the_named_app_was_closed() -> None:
    from hi_puter.brain.llm import ChatReply, ToolCall

    both = ChatReply(
        "", [ToolCall("close_app", {"app": "spotify"}), ToolCall("close_app", {"app": "firefox"})]
    )
    assistant, adapter, _ = _assistant(both)
    reply = assistant.handle("I'm done with spotify get rid of it")
    assert reply.text == "Closed spotify."
    assert adapter.calls == [("close_app", "spotify")]
