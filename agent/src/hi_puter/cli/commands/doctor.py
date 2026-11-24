import shutil
import sys
import typer

from hi_puter.core.config import load_config
from hi_puter.core.paths import get_paths


def command() -> None:
    """Check the local Hi-Puter installation."""
    paths = get_paths(); paths.ensure(); checks = [("Python", sys.version_info >= (3, 10)), ("Config", True)]
    try: load_config(paths.config_file)
    except Exception: checks[-1] = ("Config", False)
    for label, ok in checks: typer.echo(f"{'PASS' if ok else 'FAIL'}  {label}")
    typer.echo(f"INFO  ffmpeg-free runtime; microphone packages are optional")
    if not shutil.which("python3"): raise typer.Exit(1)
