import re

from hi_puter.nlu.catalog import PATTERNS, Intent
from hi_puter.nlu.normalize import normalize


def match(text: str) -> Intent | None:
    value = normalize(text)
    for intent_id, pattern, action, risk in PATTERNS:
        found = re.fullmatch(pattern, value)
        if found:
            slots = {key: item for key, item in found.groupdict().items() if item is not None}
            if "level" in slots:
                slots["level"] = str(max(0, min(100, int(slots["level"]))))
            return Intent(intent_id, action, slots, risk)
    return None
