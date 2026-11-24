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
.venv/bin/python -m pip install --timeout 180 --retries 10 -e '.[dev,audio]'
```

Install the larger speech stack separately. Some of its wheels are large, so the extended timeout and retries are intentional:

```bash
.venv/bin/python -m pip install --timeout 180 --retries 10 -e '.[speech]'
```

If the speech install still times out, install the packages one at a time so completed downloads are kept:

```bash
for package in vosk webrtcvad-wheels pyttsx3 faster-whisper; do
  .venv/bin/python -m pip install --timeout 180 --retries 10 "$package" || break
done
```

The `ReadTimeoutError` from `files.pythonhosted.org` means the package download stalled. It is a network transfer problem, not a missing Hi-Puter package. Retry on a stable connection or configure pip to use your organization’s package mirror if one is available.

### Make the microphone available

On Linux, install the PortAudio runtime and ALSA utilities if they are not already present:

```bash
sudo apt update
sudo apt install libportaudio2 portaudio19-dev alsa-utils
```

Then install the microphone capture extra inside the agent environment. This is enough to access the microphone; the larger `speech` extra is only needed for wake-word detection, transcription, and spoken replies:

```bash
.venv/bin/python -m pip install -e '.[audio]'
```

Confirm that Python can see the input devices:

```bash
.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
arecord -l
wpctl status
```

If no input device appears, check the desktop microphone permission and the input profile in your system sound settings. With PipeWire or PulseAudio, make sure an input source is available and not muted. You can inspect and unmute sources with:

```bash
pactl list short sources
pactl set-source-mute @DEFAULT_SOURCE@ 0
```

Finally, run the agent in the foreground. This keeps the microphone error visible if PortAudio cannot open the selected device:

```bash
.venv/bin/hi-puter setup
.venv/bin/hi-puter start --foreground
```

`Hi-Puter: Microphone is unavailable` means the Python audio package, PortAudio backend, or selected device still needs attention. `sounddevice` is imported only when the daemon starts, so prompt parsing continues to work without microphone access.

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

The saved wake name is used automatically. If you configured `puter`, use `puter open Firefox`; the parser also accepts the `Nova` examples above as convenient prompt-test input. The `audio` extra installs microphone capture; add the `speech` extra for Vosk, VAD, Whisper, and TTS support.

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
