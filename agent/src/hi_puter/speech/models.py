import hashlib
import zipfile
from pathlib import Path

from hi_puter.core.errors import ModelError


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ModelError(f"Checksum mismatch for {path.name}.")


def safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as file:
        root = destination.resolve()
        for member in file.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ModelError("Archive contains an unsafe path.")
        file.extractall(destination)
