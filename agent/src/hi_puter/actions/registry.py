from hi_puter.adapters.base import SystemAdapter
from hi_puter.actions.base import ActionResult
from hi_puter.nlu.catalog import Intent


def execute(intent: Intent, adapter: SystemAdapter) -> ActionResult:
    if intent.action not in adapter.capabilities() and intent.action not in {"help", "time", "battery", "stop"}:
        return ActionResult(False, "That action is not supported on this system.")
    if intent.action == "open_app": adapter.open_app(intent.slots["app"]); return ActionResult(True, "Opening it.")
    if intent.action == "volume_set": adapter.volume_set(int(intent.slots["level"])); return ActionResult(True, "Volume updated.")
    if intent.action == "volume_up": adapter.volume_change(10); return ActionResult(True, "Volume up.")
    if intent.action == "volume_down": adapter.volume_change(-10); return ActionResult(True, "Volume down.")
    if intent.action == "mute": adapter.set_mute(True); return ActionResult(True, "Muted.")
    if intent.action == "lock": adapter.lock(); return ActionResult(True, "Screen locked.")
    if intent.action == "power": adapter.power(intent.id); return ActionResult(True, "Power command sent.")
    return ActionResult(True, "I can open apps, control volume, lock the screen, take screenshots, and search the web.")
