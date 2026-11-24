import re

FILLERS = re.compile(r"\b(?:please|can you|could you|hey|um)\b", re.I)


def normalize(text: str) -> str:
    clean = re.sub(r"[^\w\s%'-]", " ", text.lower())
    return re.sub(r"\s+", " ", FILLERS.sub(" ", clean)).strip()[:200]
