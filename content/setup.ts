/**
 * Everything a user installs to get Hi-Puter working, in one place.
 * The landing page's install section and the full setup guide (/docs) both read from here,
 * so the two can never disagree. Keep it in sync with agent/README.md.
 */

export type Platform = "Linux" | "Windows";

export type SetupStep = {
  id: string;
  title: string;
  /** One sentence on why this step exists, in plain words. */
  why: string;
  commands: readonly string[];
  /** Extra guidance shown under the commands. */
  note?: string;
};

export const shells: Record<Platform, { label: string; prompt: string }> = {
  Linux: { label: "Terminal", prompt: "$" },
  Windows: { label: "PowerShell", prompt: "PS>" },
};

export const setupSteps: Record<Platform, readonly SetupStep[]> = {
  Linux: [
    {
      id: "system",
      title: "Install the system packages",
      why: "A voice for spoken replies, the audio library the microphone needs, and pipx to install Hi-Puter cleanly.",
      commands: ["sudo apt install pipx espeak-ng libportaudio2", "pipx ensurepath"],
      note: "Open a new terminal after pipx ensurepath. Fedora: sudo dnf install pipx espeak-ng portaudio. Arch: sudo pacman -S python-pipx espeak-ng portaudio.",
    },
    {
      id: "app",
      title: "Install Hi-Puter with speech",
      why: "The audio and speech extras add the microphone, voice detection and on-device speech recognition.",
      commands: ['pipx install "hi-puter[audio,speech]"'],
    },
    {
      id: "model",
      title: "Install the local AI",
      why: "Ollama runs the language model on your computer. It handles anything beyond simple commands, and nothing leaves your machine.",
      commands: ["curl -fsSL https://ollama.com/install.sh | sh", "ollama pull qwen3.5:4b"],
      note: "Have 8 GB of RAM? Pull qwen3.5:2b instead, then run hi-puter model qwen3.5:2b.",
    },
    {
      id: "check",
      title: "Set up and check",
      why: "Choose the name you'll call it by, then confirm every piece reports PASS.",
      commands: ["hi-puter setup", "hi-puter doctor"],
    },
    {
      id: "start",
      title: "Start talking",
      why: "Say your wake name and wait for “Listening”. The first start downloads the speech model, about 150 MB.",
      commands: ["hi-puter start"],
    },
  ],
  Windows: [
    {
      id: "system",
      title: "Install Python and pipx",
      why: "Hi-Puter needs Python 3.10 or newer, and pipx installs it in its own space.",
      commands: [
        "winget install Python.Python.3.12",
        "py -m pip install --user pipx",
        "py -m pipx ensurepath",
      ],
      note: "Open a new PowerShell window after ensurepath. Using the python.org installer instead? Tick “Add python.exe to PATH”.",
    },
    {
      id: "app",
      title: "Install Hi-Puter with speech",
      why: "The speech extras add the microphone and speech recognition; the windows extra adds Windows system access and voices.",
      commands: ['pipx install "hi-puter[audio,speech,windows]"'],
    },
    {
      id: "model",
      title: "Install the local AI",
      why: "Ollama runs the language model on your computer. It handles anything beyond simple commands, and nothing leaves your machine.",
      commands: ["winget install Ollama.Ollama", "ollama pull qwen3.5:4b"],
      note: "Have 8 GB of RAM? Pull qwen3.5:2b instead, then run hi-puter model qwen3.5:2b.",
    },
    {
      id: "check",
      title: "Set up and check",
      why: "Choose the name you'll call it by, then confirm every piece reports PASS.",
      commands: ["hi-puter setup", "hi-puter doctor"],
    },
    {
      id: "start",
      title: "Start talking",
      why: "Say your wake name and wait for “Listening”. The first start downloads the speech model, about 150 MB.",
      commands: ["hi-puter start"],
    },
  ],
};

/** Shown on the Windows tab: honest about what works today. */
export const windowsPreview =
  "Windows is in preview. Conversation, questions, opening and closing apps and websites, and writing documents work. Volume, lock, screenshots, screen recording and media controls are coming.";

export const requirements = [
  { label: "System", value: "Linux (GNOME tested) or Windows 10+" },
  { label: "Python", value: "3.10 or newer" },
  { label: "Memory", value: "8 GB RAM; 16 GB for the larger model" },
  { label: "Disk", value: "About 4 GB for the model and speech" },
  { label: "Microphone", value: "Built-in or headset" },
  { label: "Internet", value: "Only for the first downloads" },
] as const;

/** The four pieces Hi-Puter is made of, for the "how it fits together" overview. */
export const pieces = [
  { name: "Hi-Puter", role: "The assistant", detail: "Listens for its name, runs actions and speaks results." },
  { name: "Speech extras", role: "Its ears", detail: "Microphone, voice detection and Whisper speech recognition." },
  { name: "Voice", role: "Its voice", detail: "espeak-ng on Linux, built-in voices on Windows." },
  { name: "Ollama + model", role: "Its brain", detail: "A local language model for questions and multi-step requests." },
] as const;

export const models = [
  { memory: "8 GB RAM", model: "qwen3.5:2b", download: "2.7 GB", fit: "Quick and light. Best for most laptops." },
  { memory: "16 GB RAM or more", model: "qwen3.5:4b", download: "3.4 GB", fit: "Smarter at multi-step requests and writing. The default." },
] as const;

/** Real output of a healthy `hi-puter doctor`, for comparison. */
export const doctorOutput = `PASS  Python           3.12.3
PASS  Config           ~/.config/hi-puter/config.toml
PASS  Speech packages  sounddevice, webrtcvad, faster-whisper
PASS  Microphone       4 input device(s), e.g. HDA Intel PCH
PASS  Voice            espeak-ng
PASS  Ollama           version 0.40.2 at http://127.0.0.1:11434
PASS  Language model   qwen3.5:4b`;

export const firstRunTips = [
  {
    title: "Start it from your own terminal",
    body: "Apps installed as snaps, like Spotify, only accept media controls from regular programs. Started from inside another tool, Hi-Puter will say the app blocked it.",
  },
  {
    title: "Give the model room",
    body: "Replies come in seconds when the model has memory to spare. Close heavy browser tabs and plug in your laptop; power-saving mode can make replies several times slower.",
  },
  {
    title: "Allow screenshots once",
    body: "On GNOME, the first silent screenshot may ask for permission. If it's refused, Hi-Puter opens the screenshot tool so you can pick what to capture.",
  },
  {
    title: "Speak naturally",
    body: "Say the name and your request in one go, like “Nova, open Firefox”, or say the name, wait for “Listening”, then speak.",
  },
] as const;

export const troubleshooting = [
  {
    question: "doctor says “Speech packages: missing”",
    answer: 'Hi-Puter was installed without its speech extras. Reinstall it with them: pipx install --force "hi-puter[audio,speech]".',
  },
  {
    question: "doctor says “Microphone: no input devices”",
    answer: "Plug in or enable a microphone and allow access in your system's privacy settings. On Linux, also make sure libportaudio2 is installed.",
  },
  {
    question: "doctor says “Ollama: not reachable”",
    answer: "Ollama isn't running. Start it from your apps menu, or run ollama serve in a terminal, then check again.",
  },
  {
    question: "doctor says “Language model: not downloaded”",
    answer: "Download the model it names, for example ollama pull qwen3.5:4b, or switch to one you have with hi-puter model.",
  },
  {
    question: "“hi-puter: command not found”",
    answer: "pipx's folder isn't on your PATH yet. Run pipx ensurepath, then open a new terminal.",
  },
  {
    question: "It doesn't react to its name",
    answer: "Check that hi-puter status says running, speak a little closer to the microphone, and try the name on its own first. You can pick a name that's easier to hear with hi-puter rename.",
  },
  {
    question: "Replies are slow",
    answer: "Close memory-heavy apps, plug in your laptop, and on 8 GB of RAM use the smaller model: hi-puter model qwen3.5:2b. Simple commands like “volume up” are always instant.",
  },
  {
    question: "“Spotify blocked the request”",
    answer: "Start Hi-Puter from your own terminal rather than from inside another app. Snap apps only accept media controls from regular programs.",
  },
] as const;

export const maintenance = [
  { label: "Update Hi-Puter", command: "pipx upgrade hi-puter" },
  { label: "Switch models", command: "hi-puter model qwen3.5:2b" },
  { label: "Uninstall", command: "pipx uninstall hi-puter" },
  { label: "Remove a model", command: "ollama rm qwen3.5:4b" },
] as const;

export const fromSource = [
  "git clone https://github.com/prosperceed/hi-puter.git",
  "cd hi-puter/agent",
  "python3 -m venv .venv",
  ".venv/bin/pip install -e '.[audio,speech]'",
  ".venv/bin/hi-puter setup",
] as const;
