import {
  BatteryMedium,
  Camera,
  Clock,
  FolderOpen,
  Gauge,
  Globe,
  Lock,
  Search,
  SlidersHorizontal,
  Volume1,
  Wifi,
  type LucideIcon,
} from "lucide-react";

export type CommandExample = { phrase: string; icon: LucideIcon };

export type CommandGroup = {
  label: string;
  icon: LucideIcon;
  examples: CommandExample[];
};

export const commandGroups: CommandGroup[] = [
  {
    label: "Open & search",
    icon: Search,
    examples: [
      { phrase: "Open Firefox", icon: Globe },
      { phrase: "Search the web for local-first apps", icon: Search },
      { phrase: "Open my downloads folder", icon: FolderOpen },
    ],
  },
  {
    label: "Control",
    icon: SlidersHorizontal,
    examples: [
      { phrase: "Turn the volume down", icon: Volume1 },
      { phrase: "Lock my screen", icon: Lock },
      { phrase: "Take a screenshot", icon: Camera },
    ],
  },
  {
    label: "Check",
    icon: Gauge,
    examples: [
      { phrase: "How much battery do I have?", icon: BatteryMedium },
      { phrase: "Is Wi-Fi connected?", icon: Wifi },
      { phrase: "What time is it?", icon: Clock },
    ],
  },
];
