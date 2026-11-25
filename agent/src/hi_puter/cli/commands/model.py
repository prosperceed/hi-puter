import dataclasses
import json
import urllib.error
import urllib.request

import typer

from hi_puter.core.config import load_config, save_config
from hi_puter.core.errors import ConfigError
from hi_puter.core.paths import get_paths


def _downloaded(host: str) -> list[str] | None:
    """Model names Ollama has downloaded, or None if Ollama is not reachable."""
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=10) as response:  # noqa: S310
            data = json.loads(response.read().decode() or "{}")
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    return sorted(
        str(item.get("name", "")) for item in data.get("models", []) if isinstance(item, dict)
    )


def command(
    name: str = typer.Argument(None, help="Model to switch to, e.g. qwen3.5:4b. Omit to list."),
) -> None:
    """Show or change the language model."""
    paths = get_paths()
    try:
        config = load_config(paths.config_file)
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    models = _downloaded(config.llm.host)

    if name is None:
        typer.echo(f"Current model: {config.llm.model}")
        if models is None:
            typer.echo(f"Ollama is not reachable at {config.llm.host}.")
            return
        for model in models:
            typer.echo(f"  {'*' if model == config.llm.model else ' '} {model}")
        return

    name = name.strip()
    if models is not None and name not in models and f"{name}:latest" not in models:
        typer.echo(f"{name} is not downloaded. Run: ollama pull {name}", err=True)
        raise typer.Exit(1)
    try:
        llm = dataclasses.replace(config.llm, model=name)
        save_config(paths.config_file, dataclasses.replace(config, llm=llm))
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"Model set to {name}. Restart Hi-Puter (hi-puter stop, then start) to use it.")
