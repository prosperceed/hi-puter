import typer

from hi_puter.core.errors import LifecycleError
from hi_puter.core.paths import get_paths
from hi_puter.runtime.lifecycle import is_running, start, stop


def start_command(foreground: bool = typer.Option(False, "--foreground", help="Run in the current terminal.")) -> None:
    """Start the Hi-Puter daemon."""
    paths = get_paths(); paths.ensure()
    try: pid = start(paths.pid_file, foreground)
    except LifecycleError as exc: typer.echo(str(exc), err=True); raise typer.Exit(1) from exc
    typer.echo(f"Hi-Puter started (pid {pid}).")


def stop_command() -> None:
    """Stop the Hi-Puter daemon."""
    try: stop(get_paths().pid_file)
    except LifecycleError as exc: typer.echo(str(exc), err=True); raise typer.Exit(1) from exc
    typer.echo("Hi-Puter stopped.")


def status_command() -> None:
    """Show daemon status."""
    paths = get_paths(); running = is_running(paths.pid_file)
    if running: typer.echo(f"running (pid {paths.pid_file.read_text().strip()})")
    else: typer.echo("stopped")
