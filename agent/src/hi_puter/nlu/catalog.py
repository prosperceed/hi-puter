from dataclasses import dataclass
from enum import Enum
import re


class Risk(str, Enum): SAFE = "safe"; CONFIRM = "confirm"


@dataclass(frozen=True)
class Intent:
    id: str
    action: str
    slots: dict[str, str]
    risk: Risk = Risk.SAFE


PATTERNS: tuple[tuple[str, str, str, Risk], ...] = (
    ("shutdown", r"^(?:shut down|shutdown)$", "power", Risk.CONFIRM),
    ("restart", r"^restart$", "power", Risk.CONFIRM),
    ("suspend", r"^(?:suspend|sleep)$", "power", Risk.CONFIRM),
    ("open_app", r"^(?:open|launch) (?P<app>.+)$", "open_app", Risk.SAFE),
    ("search", r"^(?:search for|google) (?P<query>.+)$", "search", Risk.SAFE),
    ("volume_set", r"^(?:set |turn )?(?:the )?volume (?:to|at) (?P<level>\d{1,3})(?: percent)?$", "volume_set", Risk.SAFE),
    ("volume_up", r"^(?:volume )?up$", "volume_up", Risk.SAFE),
    ("volume_down", r"^(?:volume )?down$", "volume_down", Risk.SAFE),
    ("mute", r"^(?:mute|unmute)$", "mute", Risk.SAFE),
    ("lock", r"^lock (?:the )?screen$", "lock", Risk.SAFE),
    ("screenshot", r"^(?:take a )?screenshot$", "screenshot", Risk.SAFE),
    ("battery", r"^(?:battery|battery level|how much battery)$", "battery", Risk.SAFE),
    ("time", r"^(?:what time is it|time)$", "time", Risk.SAFE),
    ("stop", r"^(?:go to sleep|stop listening)$", "stop", Risk.SAFE),
    ("help", r"^(?:help|what can you do)$", "help", Risk.SAFE),
)
