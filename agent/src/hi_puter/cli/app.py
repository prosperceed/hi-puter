import contextlib

import typer

from hi_puter.cli.commands import chat, doctor, lifecycle, rename, setup
from hi_puter.core.errors import ConfigError

app = typer.Typer(no_args_is_help=True, add_completion=False)
app.command("setup")(setup.command)
app.command("start")(lifecycle.start_command)
app.command("stop")(lifecycle.stop_command)
app.command("status")(lifecycle.status_command)
app.command("rename")(rename.command)
app.command("doctor")(doctor.command)
app.command("chat")(chat.command)


@app.command(hidden=True)
def dev_parse(text: str, run: bool = False) -> None:
    """Parse text with the fast matcher, without using a microphone or the language model."""
    from hi_puter.core.config import Config, load_config
    from hi_puter.core.paths import get_paths
    from hi_puter.nlu.matcher import match
    from hi_puter.speech.wake import match_wake

    config = Config()
    with contextlib.suppress(ConfigError):  # dev helper: fall back to defaults
        config = load_config(get_paths().config_file)
    wake = match_wake(text, config.wake.name, config.wake.threshold)
    if wake is not None:
        text = wake.remainder
    result = match(text)
    if result is None:
        typer.echo("No match")
        raise typer.Exit(1)
    typer.echo(f"{result.id}: action={result.action} slots={result.slots} risk={result.risk.value}")
    if run:
        if result.risk.value == "confirm":
            typer.echo(f"Confirmation required before running {result.id}.")
            raise typer.Exit(2)
        from hi_puter.actions.registry import execute
        from hi_puter.adapters.factory import get_adapter

        outcome = execute(result, get_adapter(), config, text)
        typer.echo(outcome.spoken)
        if not outcome.ok:
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
