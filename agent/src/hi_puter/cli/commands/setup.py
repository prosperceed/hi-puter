import typer

from hi_puter.core.config import Config, WakeConfig, save_config
from hi_puter.core.paths import get_paths


def command() -> None:
    """Create the Hi-Puter configuration."""
    paths = get_paths()
    paths.ensure()
    name = typer.prompt("Wake name", default="Nova").strip().lower()
    config = Config(wake=WakeConfig(name=name))
    try:
        save_config(paths.config_file, config)
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"Saved configuration to {paths.config_file}")
