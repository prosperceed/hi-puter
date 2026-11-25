"""Installing and starting Ollama, and choosing the model that fits this computer."""

import shutil
import subprocess
import sys
import time
from collections.abc import Callable

import psutil

from hi_puter.brain.llm import OllamaClient

SMALL_MODEL = "qwen3.5:2b"
LARGE_MODEL = "qwen3.5:4b"
LARGE_MODEL_MIN_RAM = 12 * 1024**3  # 16 GB machines report a little under 16 GiB
DOWNLOAD_SIZES = {SMALL_MODEL: "2.7 GB", LARGE_MODEL: "3.4 GB"}


def installed(which: Callable[[str], str | None] = shutil.which) -> bool:
    return which("ollama") is not None


def install_command(platform: str = sys.platform) -> list[str] | None:
    """Ollama's official installer for this platform (it asks for confirmation itself)."""
    if platform.startswith("linux"):
        return ["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"]
    if platform == "win32":
        return ["winget", "install", "--id", "Ollama.Ollama", "--exact"]
    return None


def recommended_model(total_memory: int | None = None) -> str:
    memory = total_memory if total_memory is not None else psutil.virtual_memory().total
    return LARGE_MODEL if memory >= LARGE_MODEL_MIN_RAM else SMALL_MODEL


def ensure_running(
    client: OllamaClient,
    *,
    start: Callable[[], object] | None = None,
    wait_seconds: float = 20.0,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """True once the Ollama server answers; starts `ollama serve` if it isn't running."""
    if client.version() is not None:
        return True
    if start is None:

        def start() -> object:
            return subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

    try:
        start()
    except OSError:
        return False
    waited = 0.0
    while waited < wait_seconds:
        sleep(1.0)
        waited += 1.0
        if client.version() is not None:
            return True
    return False
