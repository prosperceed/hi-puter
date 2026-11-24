"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Section } from "@/components/layout/Section";
import { VoiceOrb } from "@/components/visuals/VoiceOrb";

const fallbackName = "Nova";

export function WakeName() {
  const [name, setName] = useState(fallbackName);
  const safeName = name.trim().replace(/[^a-zA-Z0-9 ]/g, "").slice(0, 20) || fallbackName;
  return <Section className="wake-section" eyebrow="Make it yours" title="Your name, your assistant." intro="Pick a wake name that feels natural. See how it sounds before you install."><div className="wake-demo"><div className="wake-input-wrap"><label htmlFor="wake-name">Wake name</label><input id="wake-name" value={name} onChange={(event) => setName(event.target.value.replace(/[^a-zA-Z0-9 ]/g, "").slice(0, 20))} maxLength={20} autoComplete="off" /><span>{safeName.length}/20</span></div><motion.div className="wake-output"><VoiceOrb state="listening" /><span className="wake-prompt">Try saying</span><p>“<strong>{safeName}</strong>, open Firefox.”</p><div className="wake-pulse" /></motion.div></div></Section>;
}
