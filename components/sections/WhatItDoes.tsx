import { AppWindow, AudioLines, BatteryMedium, Camera, Lock, Search, Volume2 } from "lucide-react";
import { Section } from "@/components/layout/Section";

const capabilities = [
  { label: "Open apps", icon: AppWindow },
  { label: "Volume", icon: Volume2 },
  { label: "Lock screen", icon: Lock },
  { label: "Screenshots", icon: Camera },
  { label: "Battery", icon: BatteryMedium },
  { label: "Web search", icon: Search },
] as const;

export function WhatItDoes() {
  return (
    <Section
      className="what-section"
      eyebrow="The idea"
      title="Less clicking. More doing."
      intro="Hi-Puter turns everyday system tasks into simple voice commands. Open apps, change volume, lock your screen, take screenshots, check battery, and search the web without leaving what you are doing."
    >
      <div className="statement-card card">
        <div>
          <span className="statement-label">
            <AudioLines size={14} aria-hidden="true" />
            AUDIO IN / ACTION OUT
          </span>
          <p>
            Say a name.
            <br />
            <strong>Your computer acts.</strong>
          </p>
        </div>
        <ul className="capability-grid">
          {capabilities.map(({ label, icon: Icon }) => (
            <li className="capability" key={label}>
              <span className="icon-chip sm" aria-hidden="true"><Icon size={17} /></span>
              {label}
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
