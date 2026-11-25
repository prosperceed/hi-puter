"""Wake-name detection on transcribed speech."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

GREETINGS = ("hey", "hi", "hello", "ok", "okay", "yo")


@dataclass(frozen=True)
class WakeMatch:
    score: float
    remainder: str  # whatever was said after the wake name, e.g. "open firefox"


def _words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9' -]", " ", text.lower()).split()


def match_wake(
    text: str, wake_name: str, threshold: float = 0.8, search_words: int = 3
) -> WakeMatch | None:
    """Find the wake name near the start of an utterance, tolerating small mis-hearings.

    "Hey Nova, open Firefox" -> WakeMatch(1.0, "open firefox"). Only the first few words are
    searched so the name mentioned mid-sentence does not trigger the assistant.
    """
    words = _words(text)
    name = _words(wake_name)
    if not words or not name:
        return None
    target = " ".join(name)
    best: WakeMatch | None = None
    for start in range(min(search_words, len(words))):
        if start and words[start - 1] not in GREETINGS:
            break
        for size in {len(name), len(name) + 1, max(1, len(name) - 1)}:
            heard = words[start : start + size]
            if not heard:
                continue
            score = SequenceMatcher(None, " ".join(heard), target).ratio()
            joined = SequenceMatcher(None, "".join(heard), target.replace(" ", "")).ratio()
            score = max(score, joined)
            if score >= threshold and (best is None or score > best.score):
                best = WakeMatch(round(score, 3), " ".join(words[start + size :]))
    return best


class WakeDetector:
    def __init__(self, wake_name: str, threshold: float = 0.8) -> None:
        self.wake_name = wake_name.lower()
        self.threshold = threshold

    def matches(self, text: str) -> WakeMatch | None:
        return match_wake(text, self.wake_name, self.threshold)
