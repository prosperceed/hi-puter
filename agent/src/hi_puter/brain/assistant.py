"""Turns a transcribed request into actions and a spoken reply.

Simple commands go through the regex matcher and run instantly. Everything else goes to the
local language model, which can call several tools in a row before answering.
"""

import logging
import platform
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from hi_puter.actions.registry import HELP, intent_call
from hi_puter.brain.llm import ChatModel, Message
from hi_puter.brain.tools import ToolBox
from hi_puter.core.errors import ModelError
from hi_puter.nlu.catalog import Intent, Risk
from hi_puter.nlu.matcher import match
from hi_puter.nlu.normalize import normalize

log = logging.getLogger("hi_puter")

NO_MODEL = "I can only do simple commands right now, because the language model isn't running."
MODEL_FAILED = "I couldn't reach the language model. Simple commands still work."
TOO_MANY_STEPS = "That took more steps than I'm allowed. Try breaking it into smaller requests."
MAX_QUICK_WORDS = 4  # longer app names or queries are probably sentences: let the model read them
COMPOUND = re.compile(r"\b(?:and|then|also|after that|plus)\b")
YES_WORDS = frozenset({"yes", "yeah", "yep", "sure", "confirm", "do it", "go ahead", "ok", "okay"})
MAX_SPOKEN_CHARS = 420


@dataclass(frozen=True)
class Pending:
    tool: str
    args: dict[str, Any]
    question: str


@dataclass(frozen=True)
class Reply:
    text: str
    pending: Pending | None = None
    end_session: bool = False
    actions: list[str] = field(default_factory=list)


class Assistant:
    def __init__(
        self,
        toolbox: ToolBox,
        model: ChatModel | None,
        *,
        name: str = "Nova",
        max_steps: int = 5,
        history_turns: int = 6,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.toolbox = toolbox
        self.model = model
        self.name = name.title()
        self.max_steps = max_steps
        self.history_turns = history_turns
        self.clock = clock
        self._history: list[Message] = []

    def reset(self) -> None:
        """Forget the conversation (called when a voice session ends)."""
        self._history.clear()

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
        intent = self._quick_intent(text)
        if intent is not None:
            reply = self._run_intent(intent.action, intent_call(intent, text))
        elif self.model is None:
            reply = Reply(NO_MODEL)
        else:
            reply = self._think(text)
        self._remember(text, reply.text)
        return reply

    def confirm(self, pending: Pending, approved: bool) -> Reply:
        if not approved:
            reply = Reply("Okay, I won't.")
        else:
            outcome = self.toolbox.call(pending.tool, pending.args)
            reply = Reply(outcome.text, actions=[pending.tool])
        self._remember("yes" if approved else "no", reply.text)
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

    def _think(self, text: str) -> Reply:
        if self.model is None:
            return Reply(NO_MODEL)
        messages: list[Message] = [{"role": "system", "content": self._system_prompt()}]
        messages += self._history
        messages.append({"role": "user", "content": text})
        schemas = self.toolbox.schemas()
        done: list[str] = []
        try:
            for _ in range(self.max_steps):
                reply = self.model.chat(messages, schemas)
                if not reply.tool_calls:
                    return Reply(speakable(reply.content) or "Done.", actions=done)
                messages.append(reply.as_message())
                for call in reply.tool_calls:
                    tool = self.toolbox.get(call.name)
                    if tool is not None and tool.risk is Risk.CONFIRM:
                        question = (
                            tool.question(call.arguments) if tool.question else f"Run {call.name}?"
                        )
                        return Reply(
                            f"{question} Say yes to confirm.",
                            pending=Pending(call.name, call.arguments, question),
                            actions=done,
                        )
                    outcome = self.toolbox.call(call.name, call.arguments)
                    log.info("tool %s %s -> %s", call.name, call.arguments, outcome.text)
                    if outcome.ok:
                        done.append(call.name)
                    messages.append(
                        {"role": "tool", "tool_name": call.name, "content": outcome.text}
                    )
        except ModelError as exc:
            log.warning("Language model failed: %s", exc)
            return Reply(MODEL_FAILED, actions=done)
        return Reply(TOO_MANY_STEPS, actions=done)

    def _system_prompt(self) -> str:
        now = self.clock()
        return (
            f"You are {self.name}, a voice assistant running entirely on the user's "
            f"{platform.system() or 'desktop'} computer. "
            f"Today is {now:%A, %B} {now.day}, {now:%Y}, and the time is {now:%H:%M}.\n"
            "Your replies are spoken aloud, so answer in one or two short, natural sentences. "
            "Never use markdown, lists, code, emojis or URLs in replies.\n"
            "Use the tools to act on the computer. For requests with several parts, call the tools "
            "one after another until everything is done, then confirm briefly what you did. "
            "Only say an action happened if its tool result says it worked. If something can't be "
            "done with the tools, say so plainly. For general questions, answer from your own "
            "knowledge without calling tools. If the request is unclear, ask one short question."
        )

    def _remember(self, user: str, assistant: str) -> None:
        self._history += [
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
        self._history = self._history[-2 * self.history_turns :]


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


def is_yes(text: str | None) -> bool:
    if not text:
        return False
    words = normalize(text)
    return words in YES_WORDS or any(words.startswith(f"{word} ") for word in YES_WORDS)
