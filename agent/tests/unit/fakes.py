from collections import deque
from pathlib import Path
from typing import Any

from hi_puter.brain.llm import ChatReply, Message, ToolCall


class FakeAdapter:
    def __init__(self, caps: frozenset[str] | None = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._caps = caps or frozenset(
            {"volume", "lock", "screenshot", "recording", "apps", "web", "power", "media", "files"}
        )
        self.running = {"firefox", "spotify"}

    def capabilities(self) -> frozenset[str]:
        return self._caps

    def volume_get(self) -> int:
        return 50

    def volume_set(self, level: int) -> None:
        self.calls.append(("volume_set", level))

    def volume_change(self, delta: int) -> None:
        self.calls.append(("volume_change", delta))

    def set_mute(self, muted: bool) -> None:
        self.calls.append(("set_mute", muted))

    def lock(self) -> None:
        self.calls.append(("lock", None))

    def screenshot(self, interactive: bool = False) -> Path | None:
        self.calls.append(("screenshot", interactive))
        return None if interactive else Path("/home/me/Pictures/Screenshots/shot.png")

    def start_recording(self, seconds: float | None) -> Path:
        self.calls.append(("start_recording", seconds))
        self.recording = True
        return Path("/home/me/Videos/Screencasts/rec.webm")

    def stop_recording(self) -> Path | None:
        self.calls.append(("stop_recording", None))
        was, self.recording = getattr(self, "recording", False), False
        return Path("/home/me/Videos/Screencasts/rec.webm") if was else None

    def open_path(self, path: Path) -> None:
        self.calls.append(("open_path", str(path)))

    def open_app(self, name: str) -> None:
        self.calls.append(("open_app", name))

    def open_url(self, url: str) -> None:
        self.calls.append(("open_url", url))

    def close_app(self, name: str) -> int:
        self.calls.append(("close_app", name))
        return 1 if name.lower() in self.running else 0

    def media(self, action: str, app: str | None) -> str:
        self.calls.append(("media", (action, app)))
        return (app or "Spotify").title()

    def power(self, kind: str) -> None:
        self.calls.append(("power", kind))


class ScriptedModel:
    """Returns queued replies and records every request."""

    def __init__(self, *replies: ChatReply) -> None:
        self.replies = deque(replies)
        self.requests: list[list[Message]] = []
        self.max_tokens: list[int | None] = []

    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatReply:
        self.requests.append([dict(message) for message in messages])
        self.max_tokens.append(max_tokens)
        return self.replies.popleft()


def call(name: str, **arguments: Any) -> ChatReply:
    return ChatReply("", [ToolCall(name, arguments)])


class FakeSource:
    """Utterances are plain strings encoded as bytes; None simulates a timeout."""

    def __init__(self, *utterances: str | None) -> None:
        self.utterances = deque(utterances)
        self.timeouts: list[float | None] = []
        self.flushes = 0

    def next_utterance(self, start_timeout: float | None = None) -> bytes | None:
        self.timeouts.append(start_timeout)
        if not self.utterances:
            return None
        item = self.utterances.popleft()
        return None if item is None else item.encode()

    def flush(self) -> None:
        self.flushes += 1


class EchoStt:
    def transcribe(self, audio: bytes) -> str:
        return audio.decode()


class RecordingTts:
    def __init__(self) -> None:
        self.said: list[str] = []

    def speak(self, text: str) -> None:
        self.said.append(text)

    def close(self) -> None:
        return None
