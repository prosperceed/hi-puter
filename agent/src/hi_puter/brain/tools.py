"""Actions the assistant can take, described so a language model can call them.

Each tool returns a short sentence that is spoken back or fed to the model as the result.
Tools marked CONFIRM are never run until the user says yes.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import psutil

from hi_puter.adapters.base import SystemAdapter
from hi_puter.core.config import Config
from hi_puter.nlu.catalog import Risk

log = logging.getLogger("hi_puter")

Args = dict[str, Any]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[Args], str]
    risk: Risk = Risk.SAFE
    # Spoken question for CONFIRM tools, e.g. "Shut down the computer?"
    question: Callable[[Args], str] | None = None

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    text: str


class ToolBox:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    def call(self, name: str, args: Args) -> ToolOutcome:
        tool = self._tools.get(name)
        if tool is None:
            return ToolOutcome(False, f"There is no tool called {name}.")
        try:
            return ToolOutcome(True, tool.handler(args))
        except NotImplementedError:
            return ToolOutcome(False, "That isn't supported on this computer yet.")
        except (KeyError, ValueError, TypeError) as exc:
            return ToolOutcome(False, f"Invalid request for {name}: {exc}")
        except Exception as exc:  # an action failing must never crash the assistant
            log.warning("Tool %s failed: %s", name, exc)
            return ToolOutcome(False, f"That didn't work: {exc}")


def _schema(
    properties: dict[str, Any] | None = None, required: list[str] | None = None
) -> dict[str, Any]:
    return {"type": "object", "properties": properties or {}, "required": required or []}


def _clamp_int(value: Any, low: int, high: int) -> int:
    return max(low, min(high, round(float(value))))


def normalize_url(raw: str) -> str:
    url = raw.strip()
    if "://" not in url:
        # Refuse other schemes ("javascript:", "mailto:") but allow "localhost:3000".
        if re.match(r"^[a-z][a-z0-9+.-]*:(?!\d)", url, re.I):
            raise ValueError(f"not a web address: {raw}")
        url = f"https://{url}"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or " " in parsed.netloc:
        raise ValueError(f"not a web address: {raw}")
    return url


def build_toolbox(  # noqa: PLR0915 (one closure per tool reads better than a class each)
    adapter: SystemAdapter,
    config: Config,
    *,
    notes_file: Path | None = None,
    clock: Callable[[], datetime] = datetime.now,
) -> ToolBox:
    caps = adapter.capabilities()
    tools: list[Tool] = []

    def open_app(args: Args) -> str:
        spoken = str(args["app"]).strip()
        target = config.apps_aliases.get(spoken.lower(), spoken)
        adapter.open_app(target)
        return f"Opening {spoken}."

    def open_website(args: Args) -> str:
        url = normalize_url(str(args["url"]))
        adapter.open_url(url)
        return f"Opened {urlparse(url).netloc}."

    def web_search(args: Args) -> str:
        query = str(args["query"]).strip()
        if not query:
            raise ValueError("empty search")
        adapter.open_url(config.search_url_template.format(query=quote_plus(query)))
        return f"Searching the web for {query}."

    def set_volume(args: Args) -> str:
        level = _clamp_int(args["level"], 0, 100)
        adapter.volume_set(level)
        return f"Volume set to {level} percent."

    def change_volume(args: Args) -> str:
        delta = _clamp_int(args.get("delta", 10), -100, 100)
        adapter.volume_change(delta)
        return "Volume up." if delta > 0 else "Volume down."

    def set_mute(args: Args) -> str:
        muted = bool(args.get("muted", True))
        adapter.set_mute(muted)
        return "Muted." if muted else "Unmuted."

    def lock_screen(_args: Args) -> str:
        adapter.lock()
        return "Screen locked."

    def take_screenshot(_args: Args) -> str:
        path = adapter.screenshot()
        return f"Screenshot saved to {path.parent.name}/{path.name}."

    def system_status(_args: Args) -> str:
        parts: list[str] = []
        battery = psutil.sensors_battery()
        if battery is not None:
            state = "charging" if battery.power_plugged else "on battery"
            parts.append(f"Battery is at {round(battery.percent)} percent and {state}")
        parts.append(f"CPU is at {round(psutil.cpu_percent(interval=0.3))} percent")
        parts.append(f"memory is {round(psutil.virtual_memory().percent)} percent used")
        disk = psutil.disk_usage(str(Path.home()))
        parts.append(f"{round(disk.free / 1e9)} gigabytes of disk free")
        return ", ".join(parts) + "."

    def current_time(_args: Args) -> str:
        now = clock()
        hour = now.strftime("%I").lstrip("0") or "12"
        return f"It's {hour}:{now:%M %p} on {now:%A, %B} {now.day}."

    def write_note(args: Args) -> str:
        if notes_file is None:
            raise NotImplementedError
        text = " ".join(str(args["text"]).split())
        if not text:
            raise ValueError("empty note")
        notes_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with notes_file.open("a", encoding="utf-8") as handle:
            handle.write(f"- {clock():%Y-%m-%d %H:%M} {text}\n")
        return "Saved the note."

    def power(args: Args) -> str:
        action = str(args["action"])
        if action not in POWER_WORDS:
            raise ValueError(f"unknown power action {action}")
        adapter.power(action)
        return f"{POWER_WORDS[action][1]}."

    if "apps" in caps:
        tools.append(
            Tool(
                "open_app",
                "Open an application installed on this computer, by name.",
                _schema(
                    {"app": {"type": "string", "description": "App name, e.g. firefox"}}, ["app"]
                ),
                open_app,
            )
        )
    if "web" in caps:
        tools.append(
            Tool(
                "open_website",
                "Open a website in the default browser.",
                _schema(
                    {"url": {"type": "string", "description": "Address, e.g. youtube.com"}}, ["url"]
                ),
                open_website,
            )
        )
        tools.append(
            Tool(
                "web_search",
                "Search the web in the default browser.",
                _schema({"query": {"type": "string"}}, ["query"]),
                web_search,
            )
        )
    if "volume" in caps:
        tools.append(
            Tool(
                "set_volume",
                "Set the speaker volume to an exact percentage.",
                _schema({"level": {"type": "integer", "minimum": 0, "maximum": 100}}, ["level"]),
                set_volume,
            )
        )
        tools.append(
            Tool(
                "change_volume",
                "Raise or lower the volume by a number of percentage points.",
                _schema(
                    {
                        "delta": {
                            "type": "integer",
                            "description": "Positive is louder, e.g. 10 or -10",
                        }
                    },
                    ["delta"],
                ),
                change_volume,
            )
        )
        tools.append(
            Tool(
                "set_mute",
                "Mute or unmute the speakers.",
                _schema({"muted": {"type": "boolean"}}, ["muted"]),
                set_mute,
            )
        )
    if "lock" in caps:
        tools.append(Tool("lock_screen", "Lock the screen.", _schema(), lock_screen))
    if "screenshot" in caps:
        tools.append(
            Tool(
                "take_screenshot",
                "Take a screenshot of the whole screen.",
                _schema(),
                take_screenshot,
            )
        )
    tools.append(
        Tool(
            "system_status",
            "Report battery, CPU, memory and free disk space.",
            _schema(),
            system_status,
        )
    )
    tools.append(Tool("current_time", "Get the current time and date.", _schema(), current_time))
    if notes_file is not None:
        tools.append(
            Tool(
                "write_note",
                "Save a short note or reminder for the user to read later.",
                _schema({"text": {"type": "string"}}, ["text"]),
                write_note,
            )
        )
    if "power" in caps:
        tools.append(
            Tool(
                "power",
                "Shut down, restart, or suspend the computer. The user is asked to confirm.",
                _schema({"action": {"type": "string", "enum": list(POWER_WORDS)}}, ["action"]),
                power,
                Risk.CONFIRM,
                question=lambda args: (
                    f"{POWER_WORDS.get(str(args.get('action')), ('Do that', ''))[0]}?"
                ),
            )
        )
    return ToolBox(tools)


# action -> (confirmation question, result)
POWER_WORDS = {
    "shutdown": ("Shut down the computer", "Shutting down"),
    "restart": ("Restart the computer", "Restarting"),
    "suspend": ("Put the computer to sleep", "Going to sleep"),
}
