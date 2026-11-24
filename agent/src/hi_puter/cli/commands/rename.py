import dataclasses
import typer

from hi_puter.core.config import WakeConfig, load_config, save_config
from hi_puter.core.errors import ConfigError
from hi_puter.core.paths import get_paths


def command(name: str) -> None:
    """Change the wake name."""
    paths = get_paths()
    try:
        config = load_config(paths.config_file)
        save_config(paths.config_file, dataclasses.replace(config, wake=WakeConfig(name=name, threshold=config.wake.threshold, verify_with_stt=config.wake.verify_with_stt)))
    except ConfigError as exc: typer.echo(str(exc), err=True); raise typer.Exit(2) from exc
    typer.echo(f"Wake name changed to {name.lower()}.")
