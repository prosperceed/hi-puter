import io
import json
import urllib.error
from typing import Any

import pytest

from hi_puter.brain import llm
from hi_puter.brain.llm import ChatReply, OllamaClient, ToolCall, parse_reply
from hi_puter.core.errors import ModelError


class FakeResponse(io.BytesIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def http_error(code: int, message: str) -> urllib.error.HTTPError:
    body = io.BytesIO(json.dumps({"error": message}).encode())
    return urllib.error.HTTPError("http://x", code, message, {}, body)  # type: ignore[arg-type]


def test_parse_reply_handles_dict_and_json_arguments() -> None:
    reply = parse_reply(
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "set_volume", "arguments": {"level": 30}}},
                    {"function": {"name": "web_search", "arguments": '{"query": "cats"}'}},
                    {"function": {"name": "", "arguments": {}}},
                ],
            }
        }
    )
    assert reply.tool_calls == [
        ToolCall("set_volume", {"level": 30}),
        ToolCall("web_search", {"query": "cats"}),
    ]


def test_tool_call_round_trip_message() -> None:
    message = ChatReply("", [ToolCall("lock_screen", {})]).as_message()
    assert message == {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "lock_screen", "arguments": {}}}],
    }


def test_chat_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, Any]] = []

    def urlopen(request: Any, timeout: float) -> FakeResponse:
        sent.append(json.loads(request.data))
        return FakeResponse(json.dumps({"message": {"content": "Hi."}}).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    client = OllamaClient("http://127.0.0.1:11434", "qwen3.5:4b")
    assert client.chat([{"role": "user", "content": "hi"}], [{"type": "function"}]).content == "Hi."
    body = sent[0]
    assert body["model"] == "qwen3.5:4b" and body["stream"] is False and body["think"] is False
    assert body["tools"] == [{"type": "function"}]


def test_retries_without_think_when_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    bodies: list[dict[str, Any]] = []

    def urlopen(request: Any, timeout: float) -> FakeResponse:
        body = json.loads(request.data)
        bodies.append(body)
        if "think" in body:
            raise http_error(400, "model does not support thinking")
        return FakeResponse(b'{"message": {"content": "ok"}}')

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    client = OllamaClient("http://127.0.0.1:11434", "llama3.2:3b")
    assert client.chat([], []).content == "ok"
    assert client.chat([], []).content == "ok"
    assert ["think" in body for body in bodies] == [True, False, False]


def test_missing_model_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen(request: Any, timeout: float) -> FakeResponse:
        raise http_error(404, "model 'qwen3.5:4b' not found")

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    with pytest.raises(ModelError, match=r"ollama pull qwen3\.5:4b"):
        OllamaClient("http://127.0.0.1:11434", "qwen3.5:4b").chat([], [])


def test_server_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen(request: Any, timeout: float) -> FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    client = OllamaClient("http://127.0.0.1:11434", "qwen3.5:4b")
    with pytest.raises(ModelError, match="Is it running"):
        client.chat([], [])
    assert client.version() is None


def test_has_model(monkeypatch: pytest.MonkeyPatch) -> None:
    tags = {"models": [{"name": "qwen3.5:4b"}, {"name": "llama3.2:latest"}]}
    monkeypatch.setattr(
        llm.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(json.dumps(tags).encode()),
    )
    assert OllamaClient("http://localhost:11434", "qwen3.5:4b").has_model()
    assert OllamaClient("http://localhost:11434", "llama3.2").has_model()
    assert not OllamaClient("http://localhost:11434", "qwen3.5:2b").has_model()
