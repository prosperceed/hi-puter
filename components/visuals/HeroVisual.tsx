"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Waveform } from "./Waveform";

export function HeroVisual() {
  const reducedMotion = useReducedMotion();
  const bars = [0.34, 0.52, 0.76, 0.94, 0.67, 0.48, 0.82, 0.58, 0.38, 0.7, 0.91, 0.55, 0.4, 0.72, 0.47, 0.83, 0.61, 0.37];
  return <div className="hero-visual" aria-label="Animated voice assistant orb"><div className="hero-grid" /><motion.div className="hero-glow" animate={reducedMotion ? undefined : { scale: [1, 1.12, 1], opacity: [0.22, 0.34, 0.22] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} /><motion.div className="voice-orb" animate={reducedMotion ? undefined : { scale: [1, 1.035, 1], rotate: [0, 2, -2, 0] }} transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}><div className="orb-core" /><div className="orb-halo halo-a" /><div className="orb-halo halo-b" /><div className="orb-bars" aria-hidden="true">{bars.map((height, index) => <motion.i key={index} animate={reducedMotion ? undefined : { height: [`${height * 28}px`, `${Math.max(10, height * 58)}px`, `${height * 28}px`] }} transition={{ duration: 1.8 + (index % 4) * 0.18, repeat: Infinity, ease: "easeInOut", delay: index * 0.04 }} />)}</div></motion.div><motion.div className="hero-signal signal-one" animate={reducedMotion ? undefined : { y: [0, -10, 0] }} transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}>voice</motion.div><motion.div className="hero-signal signal-two" animate={reducedMotion ? undefined : { y: [0, 9, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}>local</motion.div><div className="waveform-wrap"><Waveform /><span>listening for your name</span></div></div>;
}
