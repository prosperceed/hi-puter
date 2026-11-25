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

## Setup

```bash
cd agent
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,audio,speech]'
.venv/bin/hi-puter setup          # pick a wake name
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
.venv/bin/hi-puter model                 # current model and everything Ollama has downloaded
.venv/bin/hi-puter model qwen3.5:4b      # switch (restart Hi-Puter to apply)
```

Without Ollama the assistant still handles simple commands and says so when a request needs the model.

### Check everything

```bash
.venv/bin/hi-puter doctor
```

It reports the speech packages, microphones, voice, whether Ollama is running and whether the model is downloaded.

## Running

```bash
.venv/bin/hi-puter start --foreground   # see logs in the terminal
.venv/bin/hi-puter start                # run in the background
.venv/bin/hi-puter status
.venv/bin/hi-puter stop
```

Try the assistant without a microphone:

```bash
.venv/bin/hi-puter chat --dry-run       # type requests; actions are printed, not performed
.venv/bin/hi-puter chat --speak         # real actions, replies spoken aloud
```

## What it can do

Open apps and websites, search the web, set/raise/lower/mute the volume, lock the screen, take screenshots, report battery/CPU/memory/disk, tell the time, save notes (to `notes.md` in the data folder), and shut down/restart/suspend with confirmation. The model can combine these ("open YouTube and set the volume to 20") and answer general questions from its own knowledge.

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

[apps.aliases]
browser = "firefox"
editor = "code"
```

## Privacy

- Audio is processed in memory and never written to disk or sent anywhere.
- Transcripts go only to the model host, which must be `localhost` unless `llm.allow_remote = true`.
- Transcripts are not logged unless `logging.log_transcripts = true`.

## Development

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
.venv/bin/mypy
```

The voice loop, assistant, tools and Ollama client are tested with fakes, so the suite needs no microphone, speech models or Ollama. Real microphone, speaker and Windows behavior are not covered by the tests.
