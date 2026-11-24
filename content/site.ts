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

export const navLinks = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Commands", href: "#commands" },
  { label: "Privacy", href: "#privacy" },
  { label: "Install", href: "#install" },
] as const;

export const faqItems = [
  { question: "What does Hi-Puter run on?", answer: "Hi-Puter runs on Windows and Linux. Install it with pipx from your terminal, then run setup once." },
  { question: "Does it send my audio to the cloud?", answer: "No. Audio is processed locally on your computer. Hi-Puter does not need a cloud account to hear your wake name or act on a command." },
  { question: "Can I choose the wake name?", answer: "Yes. Pick any name you like during setup, or change it later with hi-puter rename \"Nova\"." },
  { question: "Is Hi-Puter always listening?", answer: "It only listens while you activate it. Stop it at any time with hi-puter stop. When stopped, it does not process audio." },
  { question: "What if I say something destructive?", answer: "Destructive actions require confirmation. Hi-Puter also limits actions to a safe command whitelist." },
] as const;
