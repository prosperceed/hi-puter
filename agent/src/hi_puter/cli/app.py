import typer

from hi_puter.cli.commands import doctor, lifecycle, rename, setup

app = typer.Typer(no_args_is_help=True, add_completion=False)
app.command("setup")(setup.command)
app.command("start")(lifecycle.start_command)
app.command("stop")(lifecycle.stop_command)
app.command("status")(lifecycle.status_command)
app.command("rename")(rename.command)
app.command("doctor")(doctor.command)


@app.command(hidden=True)
def dev_parse(text: str, run: bool = False) -> None:
    """Parse text without using a microphone."""
    from hi_puter.nlu.matcher import match
    from hi_puter.core.config import load_config
    from hi_puter.core.paths import get_paths
    try:
        wake_name = load_config(get_paths().config_file).wake.name
        if text.lower().startswith(wake_name.lower()): text = text[len(wake_name):].strip(" ,")
    except Exception:
        pass
    result = match(text)
    if result is None: typer.echo("No match"); raise typer.Exit(1)
    typer.echo(f"{result.id}: action={result.action} slots={result.slots} risk={result.risk.value}")
    if run: typer.echo("Action execution is available only through the daemon adapter.")


if __name__ == "__main__": app()
