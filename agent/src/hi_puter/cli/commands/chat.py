import typer

from hi_puter.brain.assistant import is_yes
from hi_puter.core.config import load_config
from hi_puter.core.errors import ConfigError
from hi_puter.core.paths import get_paths
from hi_puter.runtime.voice_loop import split_finished


def command(
    speak: bool = typer.Option(False, "--speak", help="Also say replies out loud."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions instead of running them."),
) -> None:
    """Talk to the assistant by typing (no microphone needed)."""
    from hi_puter.adapters.factory import get_adapter
    from hi_puter.runtime.assemble import DryRunAdapter, build_assistant
    from hi_puter.speech.tts import ConsoleSynthesizer, make_synthesizer

    paths = get_paths()
    paths.ensure()
    try:
        config = load_config(paths.config_file)
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    adapter = DryRunAdapter() if dry_run else get_adapter()
    assistant = build_assistant(config, paths, adapter)
    name = config.wake.name.title()
    voice = (
        make_synthesizer(config.tts.engine, config.tts.rate, config.tts.voice) if speak else None
    )
    printer = ConsoleSynthesizer(name)
    model = config.llm.model if config.llm.enabled else "off"
    typer.echo(f"Chatting with {name} (model: {model}). Ctrl+D or 'exit' to quit.")

    def say(text: str) -> None:
        printer.speak(text)
        if voice is not None:
            voice.speak(text)

    while True:
        try:
            text = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("")
            break
        if text.lower() in {"exit", "quit"}:
            break
        if not text:
            continue
        reply = assistant.handle(text)
        say(reply.text)
        if reply.dictation is not None:
            words = _read_dictation()
            if words:
                typer.echo("  (writing; this can take a minute)")
            say(assistant.write_document(words, reply.dictation).text)
        if reply.pending is not None:
            try:
                answer = input("you: ")
            except (EOFError, KeyboardInterrupt):
                answer = "no"
            say(assistant.confirm(reply.pending, is_yes(answer)).text)


def _read_dictation() -> str:
    """Typed stand-in for dictation: lines until 'done' or an empty line."""
    typer.echo("  (type or paste it; finish with a line saying 'done' or an empty line)")
    lines: list[str] = []
    while True:
        try:
            line = input("  ... ")
        except (EOFError, KeyboardInterrupt):
            break
        finished, kept = split_finished(line) if line.strip() else (True, "")
        if kept:
            lines.append(kept)
        if finished:
            break
    return " ".join(lines)
