"""Local language model client.

Talks to an Ollama server (https://ollama.com) over its HTTP API using only the standard
library. Ollama runs the model on this machine and supports native tool calling.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Protocol

from hi_puter.core.errors import ModelError

log = logging.getLogger("hi_puter")

Message = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ChatReply:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)

    def as_message(self) -> Message:
        """The assistant turn to append to the conversation before sending tool results."""
        message: Message = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            message["tool_calls"] = [
                {"function": {"name": call.name, "arguments": call.arguments}}
                for call in self.tool_calls
            ]
        return message


class ChatModel(Protocol):
    def chat(self, messages: list[Message], tools: list[dict[str, Any]]) -> ChatReply: ...


class OllamaClient:
    def __init__(
        self,
        host: str,
        model: str,
        *,
        temperature: float = 0.2,
        context_tokens: int = 4096,
        timeout: float = 90.0,
        keep_alive: str = "15m",
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.context_tokens = context_tokens
        self.timeout = timeout
        self.keep_alive = keep_alive
        # Thinking makes small models far slower on CPU and adds nothing to short spoken replies.
        self._send_think = True

    def chat(self, messages: list[Message], tools: list[dict[str, Any]]) -> ChatReply:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"temperature": self.temperature, "num_ctx": self.context_tokens},
        }
        if tools:
            body["tools"] = tools
        if self._send_think:
            body["think"] = False
        try:
            data = self._post("/api/chat", body)
        except ModelError as exc:
            # Older servers and non-thinking models reject the "think" field: retry without it.
            if self._send_think and "think" in str(exc).lower():
                self._send_think = False
                return self.chat(messages, tools)
            raise
        return parse_reply(data)

    def version(self) -> str | None:
        try:
            return str(self._get("/api/version").get("version", "unknown"))
        except ModelError:
            return None

    def has_model(self) -> bool:
        models = self._get("/api/tags").get("models", [])
        names = {str(item.get("name", "")) for item in models if isinstance(item, dict)}
        wanted = self.model if ":" in self.model else f"{self.model}:latest"
        return wanted in names or self.model in names

    def warm(self) -> None:
        """Load the model into memory so the first spoken request is not slowed by loading."""
        self._post(
            "/api/generate", {"model": self.model, "keep_alive": self.keep_alive, "stream": False}
        )

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.host}{path}"
        return self._request(urllib.request.Request(url, method="GET"))  # noqa: S310

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(  # noqa: S310 (scheme checked in _request)
            f"{self.host}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._request(request)

    def _request(self, request: urllib.request.Request) -> dict[str, Any]:
        if not request.full_url.startswith(("http://", "https://")):
            raise ModelError(f"Refusing to contact {request.full_url}")
        try:
            # Scheme checked above; the host is limited to localhost unless llm.allow_remote is set.
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                payload = json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            detail = _error_detail(exc)
            if exc.code == HTTPStatus.NOT_FOUND and "not found" in detail.lower():
                raise ModelError(
                    f"The model {self.model} is not downloaded. Run: ollama pull {self.model}"
                ) from exc
            raise ModelError(f"Ollama error {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ModelError(f"Cannot reach Ollama at {self.host}. Is it running? ({exc})") from exc
        except json.JSONDecodeError as exc:
            raise ModelError("Ollama returned an unreadable response.") from exc
        if not isinstance(payload, dict):
            raise ModelError("Ollama returned an unexpected response.")
        return payload


def parse_reply(data: dict[str, Any]) -> ChatReply:
    message = data.get("message") or {}
    calls: list[ToolCall] = []
    for raw in message.get("tool_calls") or []:
        function = raw.get("function") or {}
        name = str(function.get("name", "")).strip()
        arguments = function.get("arguments") or {}
        if isinstance(arguments, str):  # some servers send JSON text
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if name:
            calls.append(ToolCall(name, arguments if isinstance(arguments, dict) else {}))
    return ChatReply(str(message.get("content") or ""), calls)


def _error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(exc.read().decode() or "{}")
        return str(body.get("error", exc.reason))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return str(exc.reason)
