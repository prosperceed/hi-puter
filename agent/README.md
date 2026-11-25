# Hi-Puter agent

An offline-first voice assistant daemon for Windows and Linux. Say its name, it answers "Listening.", you say what you want, and it does it and tells you what happened. Simple commands run instantly; anything more involved goes to a local language model that can chain several actions. Audio and transcripts never leave the machine.

## How a conversation works

```
"Nova"                 -> chime, "Listening."
"Open Firefox, search for local-first apps and turn the volume down to 30"
                       -> "On it."  (opens Firefox, runs the search, sets the volume)
                       -> "Firefox is open with your search, and the volume is at 30 percent."
"and mute it"          -> follow-up within 6 s, no wake name needed -> "Muted."
(silence)              -> back to waiting for "Nova"
```

- **One breath:** "Nova, lock the screen" skips the "Listening." step.
- **Risky actions** (shut down, restart, suspend) are always read back as a question and only run after a spoken "yes".
- **"Stop listening"** ends the conversation; memory of it is cleared.

## Install

```bash
pipx install "hi-puter[audio,speech]"     # or: pip install "hi-puter[audio,speech]"
hi-puter setup                            # pick a wake name
```

The `audio` and `speech` extras add the microphone, voice detection and speech recognition. On Linux, replies are spoken with `espeak-ng` (`sudo apt install espeak-ng`). The commands below are written as `hi-puter ...`; from a source checkout, use `.venv/bin/hi-puter ...`.

### From source

```bash
git clone https://github.com/prosperceed/hi-puter.git
cd hi-puter/agent
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,audio,speech]'
.venv/bin/hi-puter setup
```

### Language model (for anything beyond simple commands)

The assistant uses [Ollama](https://ollama.com) to run a model locally. Install it, then pull a model:

```bash
ollama pull qwen3.5:4b            # default
```

| Model | Download | Use when |
| --- | --- | --- |
| `qwen3.5:4b` (default) | ~3.4 GB | Best small model for tool calling; needs ~5 GB of free RAM on CPU. |
| `qwen3.5:2b` | smaller | Laptops with 8 GB RAM or less, or when replies feel slow. |
| `qwen3.5:9b` | larger | A GPU or 16 GB+ RAM; noticeably smarter on multi-step requests. |

You can keep several models downloaded and switch between them at any time:

```bash
hi-puter model                 # current model and everything Ollama has downloaded
hi-puter model qwen3.5:4b      # switch (restart Hi-Puter to apply)
```

Without Ollama the assistant still handles simple commands and says so when a request needs the model.

### Check everything

```bash
hi-puter doctor
```

It reports the speech packages, microphones, voice, whether Ollama is running and whether the model is downloaded.

## Running

```bash
hi-puter start --foreground   # see logs in the terminal
hi-puter start                # run in the background
hi-puter status
hi-puter stop
```

Try the assistant without a microphone:

```bash
hi-puter chat --dry-run       # type requests; actions are printed, not performed
hi-puter chat --speak         # real actions, replies spoken aloud
```

## What it can do

Open and close apps ("close Spotify", "quit VS Code"), open websites, search the web, play, pause, skip or go back in music and video apps ("pause Spotify", "next song", "go back a song"), set/raise/lower/mute the volume, lock the screen, take screenshots, report battery/CPU/memory/disk, tell the time, save notes (to `notes.md` in the data folder), and shut down/restart/suspend with confirmation. The model can combine these ("open YouTube and set the volume to 20") and answer general questions from its own knowledge.

- **Closing** asks the app to quit normally, like clicking its close button; it never force-kills, never touches system processes, and won't close the terminal Hi-Puter runs in. The model can only close apps you actually named, so "close all my apps" gets a "which app?" instead.
- **Media control** works with any app that supports MPRIS (Spotify, VLC, Rhythmbox, browsers playing media). Name the app, or leave it out to control whatever is playing.
- **Screenshots**: "take a screenshot" saves the whole screen to `~/Pictures/Screenshots`; "screenshot of a window" (or an area) opens the desktop's screenshot tool so you pick. On GNOME, a silent capture needs a one-time permission; if it's refused, the screenshot tool opens instead.
- **Screen recording**: "start recording" / "record my screen for 30 seconds" / "bring up the screen recorder", then "stop recording". Uses GNOME's built-in recorder and saves to `~/Videos/Screencasts` (recordings stop after an hour if forgotten).
- **Writing documents**: "write a letter to my landlord about the roof", "help me draft an email", or just "write a document". Then explain what you want in your own words, as long as you need, and say "done" (or pause for 10 seconds). Hi-Puter writes it up properly: it keeps every point, fact and name you gave, fixes misheard words and self-corrections, follows the form (letter, email, report, essay...) and never invents details, using `[placeholders]` for anything missing. It saves Markdown to `~/Documents/Hi-Puter` and opens it. Then say "make it shorter", "more formal" or "add a closing paragraph" to revise it, or "open the document". Writing takes about a minute and a half on a laptop CPU; if it fails, what you said is saved so nothing is lost.
- **Start Hi-Puter from a normal terminal.** Apps installed as snaps (Spotify, Firefox) only accept media controls from regular programs; started from inside a sandboxed tool, Hi-Puter will say the app blocked the request.

## Configuration

`config.toml` lives in the platform config folder (`~/.config/hi-puter/` on Linux). Every key is optional.

```toml
[wake]
name = "nova"
threshold = 0.8              # how closely speech must match the name (0-1)

[stt]
model = "base.en"            # faster-whisper: tiny.en (fastest), base.en, small.en (most accurate)

[tts]
engine = "auto"              # auto | espeak | pyttsx3 | console
rate = 175

[voice]
listening_phrase = "Listening."
working_phrase = "On it."    # said before requests that need the model; "" to disable
chime = true
followup_seconds = 6.0       # 0 to require the wake name every time
prompt_timeout_seconds = 8.0
end_silence_ms = 700         # pause that ends your request

[llm]
enabled = true
model = "qwen3.5:4b"
host = "http://127.0.0.1:11434"
max_steps = 5                # most tool calls per request
temperature = 0.2
allow_remote = false         # must be true to use a model server on another machine

[documents]
folder = "~/Documents/Hi-Puter"
open_after_writing = true
pause_seconds = 10.0         # silence that ends a dictation
model = ""                   # e.g. "qwen3.5:4b" for better writing (needs more RAM)

[apps.aliases]
browser = "firefox"
editor = "code"
```

## Privacy

- Audio is processed in memory and never written to disk or sent anywhere.
- Transcripts go only to the model host, which must be `localhost` unless `llm.allow_remote = true`.
- Transcripts are not logged unless `logging.log_transcripts = true`.

## Releasing

A GitHub workflow (`.github/workflows/agent.yml`) tests, builds and publishes the package to PyPI when a version tag is pushed:

1. Bump `__version__` in `src/hi_puter/__init__.py` and commit it.
2. Tag and push: `git tag v0.1.1 && git push origin v0.1.1`.

The workflow refuses to publish if the tag doesn't match `__version__`. It can also be run by hand from the Actions tab to publish to TestPyPI first.

## Development

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
.venv/bin/mypy
```

The voice loop, assistant, tools and Ollama client are tested with fakes, so the suite needs no microphone, speech models or Ollama. Real microphone, speaker and Windows behavior are not covered by the tests.
