from pathlib import Path


def validate_wake_name(name: str, words_file: Path) -> tuple[bool, list[str]]:
    words = {
        line.split()[0].lower() for line in words_file.read_text().splitlines() if line.strip()
    }
    missing = [token for token in name.lower().split() if token not in words]
    return not missing, missing
