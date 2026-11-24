# Hi-Puter

Hi-Puter is an offline-first voice-assistant project with a Next.js landing page and a Python agent. The agent is designed to listen for a wake name, understand short system prompts, and run safe local actions.

## Run the website

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Start the Python agent

The Python agent has its own virtual environment under `agent/`. From the repository root:

```bash
cd agent
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,audio]'
```

Create the local configuration, then start the background daemon:

```bash
.venv/bin/hi-puter setup
.venv/bin/hi-puter start
.venv/bin/hi-puter status
```

Useful lifecycle commands:

```bash
.venv/bin/hi-puter stop
.venv/bin/hi-puter rename Nova
.venv/bin/hi-puter doctor
```

Use `start --foreground` while developing the daemon:

```bash
.venv/bin/hi-puter start --foreground
```

## Test prompts without a microphone

The hidden development command parses a prompt without accessing audio hardware. It normalizes the text, removes the configured wake name, and prints the matched intent, slots, and risk level:

```bash
.venv/bin/python -m hi_puter dev-parse "Nova open Firefox"
.venv/bin/python -m hi_puter dev-parse "set volume to 40"
.venv/bin/python -m hi_puter dev-parse "search for Linux audio tools"
.venv/bin/python -m hi_puter dev-parse "shut down"
```

You can also use the installed command entry point:

```bash
.venv/bin/hi-puter dev-parse "Nova open Firefox"
```

Add `--run` to exercise the development execution path. Risky prompts remain marked for confirmation:

```bash
.venv/bin/hi-puter dev-parse "lock the screen" --run
.venv/bin/hi-puter dev-parse "restart" --run
```

The current agent foundation reports the selected action through `dev-parse`; full microphone capture, speech models, and end-to-end action execution are still being integrated.

## Development checks

Run the web checks from the repository root:

```bash
pnpm exec tsc --noEmit
pnpm lint
pnpm build
```

Run Python checks from `agent/`:

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src tests
PYTHONPATH=src .venv/bin/python -m pytest -q
```

See the Python-specific notes in [agent/README.md](./agent/README.md).
