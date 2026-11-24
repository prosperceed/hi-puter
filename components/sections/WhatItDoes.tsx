import { AppWindow, ArrowRight, BatteryMedium, Camera, Lock, Search, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/Button";

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
    <section className="split ticked" aria-labelledby="what-title">
      <div className="split-copy">
        <p className="eyebrow">The idea</p>
        <h2 id="what-title">Less clicking. More doing.</h2>
        <p>
          Everyday system tasks become simple voice commands, so you never have to leave what you are doing.
        </p>
        <Button href="#commands" variant="soft">
          See what to say
          <ArrowRight className="icon-trail" size={16} aria-hidden="true" />
        </Button>
      </div>
      <ul className="capabilities">
        {capabilities.map(({ label, icon: Icon }) => (
          <li className="capability" key={label}>
            <Icon size={22} strokeWidth={1.75} aria-hidden="true" />
            {label}
          </li>
        ))}
      </ul>
    </section>
  );
}
