export type CommandGroup = {
  label: string;
  examples: string[];
};

export const commandGroups: CommandGroup[] = [
  { label: "Open & search", examples: ["Open Firefox", "Search the web for local-first apps", "Open my downloads folder"] },
  { label: "Control", examples: ["Turn the volume down", "Lock my screen", "Take a screenshot"] },
  { label: "Check", examples: ["How much battery do I have?", "Is Wi-Fi connected?", "What time is it?"] },
];
