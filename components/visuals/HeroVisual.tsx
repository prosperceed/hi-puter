"use client";

import { VoiceOrb } from "./VoiceOrb";
import { GridBackdrop } from "./GridBackdrop";

export function HeroVisual() {
  return <div className="hero-visual"><GridBackdrop /><VoiceOrb /><div className="orb-contact-shadow" aria-hidden="true" /><div className="orb-status"><span className="status-wave" aria-hidden="true"><i /><i /><i /><i /><i /></span> Listening for your name</div></div>;
}
