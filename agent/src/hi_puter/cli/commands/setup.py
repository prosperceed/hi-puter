import typer

from hi_puter.core.paths import get_paths


class TerminalConsole:
    """The wizard's view of the terminal."""

    def __init__(self) -> None:
        self._progress_shown = False

    def say(self, text: str = "") -> None:
        self.progress_done()
        typer.echo(text)

    def ask(self, question: str, default: str) -> str:
        return str(typer.prompt(question, default=default))

    def confirm(self, question: str, default: bool = True) -> bool:
        return typer.confirm(question, default=default)

    def progress(self, text: str) -> None:
        typer.echo("\r" + text.ljust(72), nl=False)
        self._progress_shown = True

    def progress_done(self) -> None:
        if self._progress_shown:
            typer.echo()
            self._progress_shown = False


def command(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Accept the recommended choices without asking."
    ),
    name: str = typer.Option(None, "--name", help="Wake name, e.g. Nova."),
) -> None:
    """Set up Hi-Puter: name, voice and microphone, local AI, model and speech."""
    from hi_puter.onboarding.wizard import Wizard

    paths = get_paths()
    paths.ensure()
    ok = Wizard(TerminalConsole(), paths, yes=yes, name=name).run_all()
    if not ok:
        raise typer.Exit(1)
