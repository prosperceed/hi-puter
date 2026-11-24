# Hi-Puter agent

The agent is an offline-first Python daemon with a typed CLI, validated TOML configuration, process lifecycle controls, normalized intent matching, and lazy audio/model integration points.

```bash
cd agent
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,audio]'
.venv/bin/hi-puter setup
.venv/bin/hi-puter start
.venv/bin/hi-puter status
```

The microphone and speech-model extras are intentionally optional for installation and status checks. Real Windows hardware is not verified in this environment.
