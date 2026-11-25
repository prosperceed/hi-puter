from collections import deque
from pathlib import Path
from typing import Any

from hi_puter.brain.llm import ChatReply, Message, ToolCall


class FakeAdapter:
    def __init__(self, caps: frozenset[str] | None = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._caps = caps or frozenset({"volume", "lock", "screenshot", "apps", "web", "power"})

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

    def screenshot(self) -> Path:
        raise NotImplementedError

    def open_app(self, name: str) -> None:
        self.calls.append(("open_app", name))

    def open_url(self, url: str) -> None:
        self.calls.append(("open_url", url))

    def power(self, kind: str) -> None:
        self.calls.append(("power", kind))


class ScriptedModel:
    """Returns queued replies and records every request."""

    def __init__(self, *replies: ChatReply) -> None:
        self.replies = deque(replies)
        self.requests: list[list[Message]] = []

    def chat(self, messages: list[Message], tools: list[dict[str, Any]]) -> ChatReply:
        self.requests.append([dict(message) for message in messages])
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
