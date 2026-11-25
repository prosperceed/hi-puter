import re

FILLERS = re.compile(r"\b(?:please|can you|could you|hey|um)\b", re.I)


def normalize(text: str) -> str:
    # Whisper writes "30%"; the command patterns expect "30 percent".
    clean = re.sub(r"(\d)\s*%", r"\1 percent", text.lower())
    clean = re.sub(r"[^\w\s'-]", " ", clean)
    return re.sub(r"\s+", " ", FILLERS.sub(" ", clean)).strip()[:200]
