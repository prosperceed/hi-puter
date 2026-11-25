"""Downloading the speech recognition model ahead of the first start."""

import os
from pathlib import Path


def use_plain_downloads() -> None:
    """Prefer plain HTTPS over Hugging Face's Xet transfer, which can stall on slow links."""
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")


def download_speech_model(name: str = "base.en") -> Path:
    """Fetch the faster-whisper model into the shared cache (shows its own progress bar)."""
    use_plain_downloads()
    from faster_whisper import download_model

    return Path(download_model(name))
