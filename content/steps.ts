import { HardDrive, ListChecks, MessageSquareWarning, Mic, PenLine, Power, Zap, type LucideIcon } from "lucide-react";

type Step = { number: string; title: string; body: string; icon: LucideIcon };
type PrivacyPoint = { label: string; detail: string; icon: LucideIcon };

export const howItWorks: readonly Step[] = [
  { number: "01", title: "Choose a name", body: "Give your assistant any wake name. Keep it personal.", icon: PenLine },
  { number: "02", title: "Say it", body: "Hi-Puter wakes when it hears your name, then waits for the request.", icon: Mic },
  { number: "03", title: "It acts", body: "Your words become a system action: an app opens, a volume changes, a screenshot lands.", icon: Zap },
  { number: "04", title: "It sleeps", body: "Deactivate it when you are done. No active listener, no processing.", icon: Power },
];

export const privacyPoints: readonly PrivacyPoint[] = [
  { label: "Local audio", detail: "Voice processing stays on your machine.", icon: HardDrive },
  { label: "Explicit activation", detail: "It only listens while you have it on.", icon: Power },
  { label: "Safe whitelist", detail: "Only supported computer actions can run.", icon: ListChecks },
  { label: "Confirmations", detail: "Destructive requests ask before they act.", icon: MessageSquareWarning },
];
