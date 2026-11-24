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
    if result is None and len(text.split()) > 1:
        result = match(text.split(" ", 1)[1])
    if result is None: typer.echo("No match"); raise typer.Exit(1)
    typer.echo(f"{result.id}: action={result.action} slots={result.slots} risk={result.risk.value}")
    if run:
        if result.risk.value == "confirm":
            typer.echo(f"Confirmation required before running {result.id}.")
            raise typer.Exit(2)
        from hi_puter.actions.registry import execute
        from hi_puter.adapters.factory import get_adapter
        try:
            outcome = execute(result, get_adapter())
        except Exception as exc:
            typer.echo(f"Action failed: {exc}", err=True)
            raise typer.Exit(1) from exc
        typer.echo(outcome.spoken)
        if not outcome.ok: raise typer.Exit(1)


if __name__ == "__main__": app()
