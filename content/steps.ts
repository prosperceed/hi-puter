export const howItWorks = [
  { number: "01", title: "Choose a name", body: "Give your assistant any wake name. Keep it personal." },
  { number: "02", title: "Say it", body: "Hi-Puter wakes when it hears your name, then waits for the request." },
  { number: "03", title: "It acts", body: "Your words become a system action: an app opens, a volume changes, a screenshot lands." },
  { number: "04", title: "It sleeps", body: "Deactivate it when you are done. No active listener, no processing." },
] as const;

export const privacyPoints = [
  { label: "Local audio", detail: "Voice processing stays on your machine." },
  { label: "Explicit activation", detail: "It only listens while you have it on." },
  { label: "Safe whitelist", detail: "Only supported computer actions can run." },
  { label: "Confirmations", detail: "Destructive requests ask before they act." },
] as const;
