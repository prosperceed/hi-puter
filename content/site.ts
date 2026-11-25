export const site = {
  name: "Hi-Puter",
  url: "https://hi-puter.dev",
  description: "A local voice assistant for Windows and Linux. Say a name. Your computer gets to work.",
} as const;

export const installCommands = {
  install: "pipx install hi-puter",
  setup: "hi-puter setup",
  start: "hi-puter start",
  stop: "hi-puter stop",
  status: "hi-puter status",
  rename: 'hi-puter rename "Nova"',
} as const;

// Absolute "/#..." links so they also work from the docs page.
export const navLinks = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Commands", href: "/#commands" },
  { label: "Install", href: "/#install" },
  { label: "Setup guide", href: "/docs" },
] as const;

export const faqItems = [
  {
    question: "What does Hi-Puter run on?",
    answer:
      "Linux, with GNOME as the tested desktop, and Windows 10 or later in preview. On Windows, conversation, opening and closing apps and websites, and writing documents work today; system controls like volume and screenshots are coming.",
  },
  {
    question: "What do I need to install?",
    answer:
      "Just Hi-Puter: pipx install hi-puter, then hi-puter setup. Setup adds the voice and audio libraries, Ollama and the right AI model for your computer, asking before each install, and checks everything works.",
  },
  {
    question: "Does it send my audio to the cloud?",
    answer:
      "No. Your voice is processed in memory on your computer and never saved or sent anywhere. The language model runs locally through Ollama too; the internet is only used for the first downloads.",
  },
  {
    question: "Is Hi-Puter always listening?",
    answer:
      "While it's running, it listens for its name and transcribes speech locally to spot it; nothing is kept. Run hi-puter stop to turn the microphone off completely.",
  },
  {
    question: "Do I need a powerful computer?",
    answer:
      "No graphics card is needed. 8 GB of RAM runs the smaller model; 16 GB runs the larger one, which is better at multi-step requests and writing. Simple commands like “volume up” are instant on any machine.",
  },
  {
    question: "Can I choose the wake name?",
    answer: "Yes. Pick any name during setup, or change it later with hi-puter rename \"Nova\".",
  },
  {
    question: "What if I say something destructive?",
    answer:
      "Shutting down, restarting or suspending is always read back as a question and only happens after you say yes. Hi-Puter can only close apps you actually name, and it never touches system processes.",
  },
] as const;
