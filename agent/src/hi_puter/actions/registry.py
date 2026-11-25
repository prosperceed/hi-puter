"""Maps the fast regex intents onto toolbox calls, so simple commands skip the language model."""

from typing import Any

from hi_puter.actions.base import ActionResult
from hi_puter.adapters.base import SystemAdapter
from hi_puter.core.config import Config
from hi_puter.nlu.catalog import SITES, Intent
from hi_puter.nlu.normalize import normalize

HELP = (
    "I can open apps and websites, search the web, change the volume, lock the screen, "
    "take screenshots, check the battery and time, save notes, and handle multi-step requests."
)


def intent_call(intent: Intent, text: str = "") -> tuple[str, dict[str, Any]] | None:
    """The tool name and arguments for an intent, or None for intents answered without a tool."""
    slots = intent.slots
    calls: dict[str, tuple[str, dict[str, Any]]] = {
        "open_app": ("open_app", {"app": slots.get("app", "")}),
        "close_app": ("close_app", {"app": slots.get("app", "")}),
        "open_site": (
            "open_website",
            {"url": SITES.get(slots.get("site", ""), slots.get("site", ""))},
        ),
        "search": ("web_search", {"query": slots.get("query", "")}),
        "volume_set": ("set_volume", {"level": int(slots.get("level", "50"))}),
        "volume_up": ("change_volume", {"delta": 10}),
        "volume_down": ("change_volume", {"delta": -10}),
        "mute": ("set_mute", {"muted": not normalize(text).startswith("unmute")}),
        "lock": ("lock_screen", {}),
        "screenshot": ("take_screenshot", {}),
        "battery": ("system_status", {}),
        "time": ("current_time", {}),
        "power": ("power", {"action": intent.id}),
    }
    if intent.action == "start_document":
        return (
            "start_document",
            {"kind": slots.get("kind", "document"), "topic": slots.get("topic", "")},
        )
    if intent.action == "start_recording":
        return ("start_recording", {"seconds": _seconds(slots.get("amount"), slots.get("unit"))})
    if intent.action in {"open_document", "stop_recording"}:
        return (intent.action, {})
    if intent.action == "screenshot_choose":
        return ("take_screenshot", {"mode": "choose"})
    if intent.action == "media":
        player = (slots.get("app") or slots.get("player") or "").strip() or None
        return ("media_control", {"action": intent.id.removeprefix("media_"), "app": player})
    return calls.get(intent.action)


NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30,
}  # fmt: skip


def _seconds(amount: str | None, unit: str | None) -> int | None:
    """("30", "seconds") -> 30, ("two", "minutes") -> 120, (None, None) -> None."""
    if not amount:
        return None
    number = int(amount) if amount.isdigit() else NUMBER_WORDS.get(amount, 0)
    return number * 60 if (unit or "").startswith("minute") else number or None


def execute(
    intent: Intent, adapter: SystemAdapter, config: Config | None = None, text: str = ""
) -> ActionResult:
    from hi_puter.brain.tools import build_toolbox

    call = intent_call(intent, text)
    if call is None:
        return ActionResult(True, "Okay." if intent.action == "stop" else HELP)
    toolbox = build_toolbox(adapter, config or Config())
    if call[0] not in toolbox:
        return ActionResult(False, "That action is not supported on this system.")
    outcome = toolbox.call(*call)
    return ActionResult(outcome.ok, outcome.text)
