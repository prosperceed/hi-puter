"""Turns a transcribed request into actions and a spoken reply.

Simple commands go through the regex matcher and run instantly. Everything else goes to the
local language model, which can call several tools in a row before answering.
"""

import json
import logging
import platform
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

from hi_puter.actions.registry import HELP, intent_call
from hi_puter.brain.llm import ChatModel, ChatReply, Message, ToolCall
from hi_puter.brain.tools import ToolBox
from hi_puter.core.errors import ModelError
from hi_puter.nlu.catalog import Intent, Risk
from hi_puter.nlu.matcher import match
from hi_puter.nlu.normalize import normalize

log = logging.getLogger("hi_puter")

NO_MODEL = "I can only do simple commands right now, because the language model isn't running."
MODEL_FAILED = "I couldn't reach the language model. Simple commands still work."
NOT_RUN = "Not run: waiting for the user to confirm an earlier action."
ALREADY_DONE = "Already done; don't repeat it. Do the part of the request that is left."
TOO_MANY_STEPS = "That took more steps than I'm allowed. Try breaking it into smaller requests."
MAX_QUICK_WORDS = 4  # longer app names or queries are probably sentences: let the model read them
COMPOUND = re.compile(r"\b(?:and|then|also|after that|plus)\b")
YES_WORDS = frozenset({"yes", "yeah", "yep", "sure", "confirm", "do it", "go ahead", "ok", "okay"})
MAX_SPOKEN_CHARS = 420
GREETING = "Hello, are you ready?"
# Conversation kept after the system prompt (~1,100 tokens with tools). About 4 characters a
# token, so this stays well inside a 4,096-token context.
MEMORY_CHARS = 6000
IDLE_FORGET = timedelta(minutes=30)


@dataclass(frozen=True)
class Pending:
    tool: str
    args: dict[str, Any]
    question: str
    from_model: bool = False  # the model's tool call is waiting for this result


@dataclass(frozen=True)
class Reply:
    text: str
    pending: Pending | None = None
    end_session: bool = False
    actions: list[str] = field(default_factory=list)


class Assistant:
    """Answers requests, keeping one continuous conversation with the model.

    The conversation is append-only on purpose. Small hybrid models (qwen3.5) can only reuse
    their prompt cache when a request extends the previous one exactly; anything else makes
    Ollama re-read the whole ~1,100-token prompt, which takes 20-80 s on a laptop CPU. So every
    exchange is recorded exactly as the model saw it, and memory is trimmed only when it grows
    too long or after a long idle period.
    """

    def __init__(
        self,
        toolbox: ToolBox,
        model: ChatModel | None,
        *,
        name: str = "Nova",
        max_steps: int = 5,
        memory_chars: int = MEMORY_CHARS,
        idle_forget: timedelta = IDLE_FORGET,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.toolbox = toolbox
        self.model = model
        self.name = name.title()
        self.max_steps = max_steps
        self.memory_chars = memory_chars
        self.idle_forget = idle_forget
        self.clock = clock
        self._history: list[Message] = []  # exact transcript after the system prompt
        self._last_used: datetime | None = None
        self._lock = Lock()

    def reset(self) -> None:
        """Forget the conversation."""
        with self._lock:
            self._history.clear()

    def prime(self, timeout: float | None = None) -> None:
        """Load the model and hold the first exchange, so the first real request is quick.

        The greeting stays as the first turn: the model has already processed the system prompt
        and tools for it, and the next request extends it instead of starting over.
        """
        if self.model is None:
            return
        warm = getattr(self.model, "warm", None)
        if warm is not None:
            warm()
        with self._lock:
            self._history.clear()
            self._think(GREETING, timeout=timeout)

    def is_quick(self, text: str) -> bool:
        """True when the request is handled by the regex matcher without the model."""
        return self.model is None or self._quick_intent(text) is not None

    def _quick_intent(self, text: str) -> Intent | None:
        intent = match(text)
        if intent is None or self.model is None:
            return intent
        # "open firefox and search for cats" matches `open (.+)` but is really two requests.
        words = normalize(text)
        free_text = intent.slots.get("app") or intent.slots.get("query") or ""
        if (
            COMPOUND.search(words)
            or "," in text
            or ";" in text
            or len(free_text.split()) > MAX_QUICK_WORDS
        ):
            return None
        return intent

    def handle(self, text: str) -> Reply:
        text = text.strip()
        if not text:
            return Reply("I didn't catch that.")
        with self._lock:
            now = self.clock()
            if self._last_used is not None and now - self._last_used > self.idle_forget:
                self._history.clear()
            self._last_used = now
            intent = self._quick_intent(text)
            if intent is not None:
                reply = self._run_intent(intent.action, intent_call(intent, text))
            elif self.model is None:
                reply = Reply(NO_MODEL)
            else:
                return self._think(text)
            self._note(text, reply.text)
            return reply

    def confirm(self, pending: Pending, approved: bool) -> Reply:
        with self._lock:
            if approved:
                outcome = self.toolbox.call(pending.tool, pending.args)
                reply = Reply(outcome.text, actions=[pending.tool] if outcome.ok else [])
            else:
                reply = Reply("Okay, I won't.")
            if pending.from_model:
                # Answer the model's open tool call so the transcript stays a valid continuation.
                result = reply.text if approved else "The user said no, so it was not done."
                self._history.append({"role": "tool", "tool_name": pending.tool, "content": result})
            else:
                self._note("yes" if approved else "no", reply.text)
            self._trim()
            return reply

    # -- fast path ---------------------------------------------------------------------------

    def _run_intent(self, action: str, call: tuple[str, dict[str, Any]] | None) -> Reply:
        if action == "stop":
            return Reply("Okay.", end_session=True)
        if call is None:
            return Reply(HELP)
        return self._invoke(*call)

    def _invoke(self, name: str, args: dict[str, Any]) -> Reply:
        tool = self.toolbox.get(name)
        if tool is None:
            return Reply("That isn't supported on this computer.")
        if tool.risk is Risk.CONFIRM:
            question = tool.question(args) if tool.question else f"Run {name}?"
            return Reply(f"{question} Say yes to confirm.", pending=Pending(name, args, question))
        outcome = self.toolbox.call(name, args)
        return Reply(outcome.text, actions=[name])

    # -- language model ----------------------------------------------------------------------

    def _think(self, text: str, timeout: float | None = None) -> Reply:  # noqa: PLR0911
        if self.model is None:
            return Reply(NO_MODEL)
        messages: list[Message] = [{"role": "system", "content": self._system_prompt()}]
        messages += self._history
        messages.append({"role": "user", "content": text})
        schemas = self.toolbox.schemas()
        parts = count_parts(text)
        done: list[str] = []
        results: list[str] = []
        seen: set[str] = set()
        repeats = 0

        def finish(reply: Reply) -> Reply:
            self._history = messages[1:]
            self._trim()
            return reply

        try:
            for _ in range(self.max_steps):
                reply = self._chat(messages, schemas, timeout)
                if not reply.tool_calls:
                    messages.append(reply.as_message())  # raw, exactly as generated
                    return finish(
                        Reply(
                            speakable(reply.content) or join_results(results) or "Done.",
                            actions=done,
                        )
                    )
                messages.append(reply.as_message())
                fresh = [call for call in reply.tool_calls if _call_key(call) not in seen]
                if not fresh:
                    # Small models sometimes re-issue calls that already ran. Point it at what is
                    # left once; if it repeats again, what has been done is the answer.
                    repeats += 1
                    messages += [_tool_result(call, ALREADY_DONE) for call in reply.tool_calls]
                    if repeats > 1:
                        return finish(Reply(join_results(results) or "Done.", actions=done))
                    continue
                for index, call in enumerate(reply.tool_calls):
                    if call not in fresh:
                        messages.append(_tool_result(call, ALREADY_DONE))
                        continue
                    seen.add(_call_key(call))
                    tool = self.toolbox.get(call.name)
                    if tool is not None and tool.risk is Risk.CONFIRM:
                        question = (
                            tool.question(call.arguments) if tool.question else f"Run {call.name}?"
                        )
                        later = reply.tool_calls[index + 1 :]
                        messages += [_tool_result(other, NOT_RUN) for other in later]
                        prefix = join_results(results)
                        return finish(
                            Reply(
                                f"{prefix} {question} Say yes to confirm.".strip(),
                                pending=Pending(call.name, call.arguments, question, True),
                                actions=done,
                            )
                        )
                    outcome = self.toolbox.call(call.name, call.arguments)
                    log.info("tool %s %s -> %s", call.name, call.arguments, outcome.text)
                    results.append(outcome.text)
                    if outcome.ok:
                        done.append(call.name)
                    messages.append(_tool_result(call, outcome.text))
                if len(seen) >= parts:
                    # Every part of the request has had an action. The tool results are already
                    # short spoken sentences, so skip a whole model round spent summarizing them.
                    return finish(Reply(join_results(results), actions=done))
        except ModelError as exc:
            log.warning("Language model failed: %s", exc)
            # The model's cache no longer matches a clean transcript: start over next time.
            self._history = []
            return Reply(join_results(results) or MODEL_FAILED, actions=done)
        return finish(Reply(join_results(results) or TOO_MANY_STEPS, actions=done))

    def _chat(
        self, messages: list[Message], schemas: list[dict[str, Any]], timeout: float | None
    ) -> ChatReply:
        if self.model is None:
            raise ModelError("No language model")
        if timeout is None:
            return self.model.chat(messages, schemas)
        return self.model.chat(messages, schemas, timeout=timeout)

    def _system_prompt(self) -> str:
        # Keep this text fixed (no clock): Ollama reuses its cache only while the prompt
        # prefix is identical, and re-reading it costs over a minute on a slow CPU.
        return (
            f"You are {self.name}, a voice assistant on the user's "
            f"{platform.system() or 'desktop'} computer. Replies are spoken: one or two short "
            "sentences, no markdown, lists, emojis or links.\n"
            "Use tools to act on the computer. If a request needs several actions, call all of "
            "them in one reply. Never repeat an action that already ran. Only claim an action "
            "worked if its result says so. Use current_time for the date or time.\n"
            "Answer questions yourself, in words, without tools, unless the user asks you to "
            "search. If a request is unclear, ask one short question."
        )

    def _note(self, user: str, assistant: str) -> None:
        """Record an exchange the model did not take part in, so it still has the context."""
        self._history += [
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
        self._trim()

    def _trim(self) -> None:
        """Drop the oldest turns once memory is too long (costs one full prompt re-read)."""
        if _size(self._history) <= self.memory_chars:
            return
        while self._history and (
            _size(self._history) > self.memory_chars // 2 or self._history[0]["role"] != "user"
        ):
            self._history.pop(0)


def speakable(text: str) -> str:
    """Strip reasoning tags and markdown, and keep replies short enough to listen to."""
    text = re.sub(r"<think>.*?</think>", " ", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"[*_#`>|]+", " ", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.M)
    text = " ".join(text.split())
    if len(text) <= MAX_SPOKEN_CHARS:
        return text
    cut = text[:MAX_SPOKEN_CHARS]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    # Prefer ending on a full sentence, unless that would leave almost nothing.
    return cut[: end + 1] if end > MAX_SPOKEN_CHARS // 5 else cut.rsplit(" ", 1)[0] + "."


def count_parts(text: str) -> int:
    """How many separate things a request asks for: "open x, search y and mute" -> 3."""
    clauses = re.split(r",|;|\b(?:and then|and|then|also|after that|plus)\b", text.lower())
    return max(1, sum(1 for clause in clauses if re.search(r"[a-z0-9]", clause)))


def join_results(results: list[str]) -> str:
    return " ".join(dict.fromkeys(result for result in results if result))


def _tool_result(call: ToolCall, content: str) -> Message:
    return {"role": "tool", "tool_name": call.name, "content": content}


def _size(messages: list[Message]) -> int:
    return sum(len(str(m.get("content", ""))) + len(str(m.get("tool_calls", ""))) for m in messages)


def _call_key(call: ToolCall) -> str:
    return f"{call.name}:{json.dumps(call.arguments, sort_keys=True, default=str).lower()}"


def is_yes(text: str | None) -> bool:
    if not text:
        return False
    words = normalize(text)
    return words in YES_WORDS or any(words.startswith(f"{word} ") for word in YES_WORDS)
