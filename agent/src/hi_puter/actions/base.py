from dataclasses import dataclass
from typing import Protocol

from hi_puter.adapters.base import SystemAdapter
from hi_puter.nlu.catalog import Risk


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    spoken: str


class Action(Protocol):
    id: str
    risk: Risk
    def run(self, slots: dict[str, str], adapter: SystemAdapter) -> ActionResult: ...
