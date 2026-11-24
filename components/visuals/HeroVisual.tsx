"use client";

import { Mic } from "lucide-react";
import { VoiceOrb } from "./VoiceOrb";
import { GridBackdrop } from "./GridBackdrop";

export function HeroVisual() {
  return (
    <div className="hero-visual">
      <GridBackdrop />
      <VoiceOrb />
      <div className="orb-contact-shadow" aria-hidden="true" />
      <div className="orb-status">
        <span className="orb-status-icon" aria-hidden="true">
          <Mic size={13} strokeWidth={2.25} />
        </span>
        Listening for your name
        <span className="status-wave" aria-hidden="true"><i /><i /><i /><i /><i /></span>
      </div>
    </div>
  );
}
