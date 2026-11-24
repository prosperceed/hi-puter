"use client";

import { useEffect, useRef } from "react";

type VoiceOrbProps = { state?: "idle" | "listening" | "processing" | "done" };

export function VoiceOrb({ state = "idle" }: VoiceOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const shell = shellRef.current;
    if (!canvas || !shell) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    let width = 0;
    let height = 0;
    let frame = 0;
    let visible = true;
    let reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const root = document.documentElement;

    const resize = () => {
      const bounds = shell.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = bounds.width;
      height = bounds.height;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      draw(0);
    };

    const css = (name: string, fallback: string) => getComputedStyle(root).getPropertyValue(name).trim() || fallback;
    const draw = (time: number) => {
      if (!width || !height) return;
      context.clearRect(0, 0, width, height);
      const cx = width / 2;
      const cy = height / 2;
      const radius = Math.min(width, height) * 0.38;
      const phase = ((time % 4320) / 4320) * Math.PI * 2 * (state === "processing" ? 2 : 1);
      const amplitude = state === "listening" ? radius * 0.2 : state === "processing" ? radius * 0.1 : radius * 0.13;
      const start = cx - radius * 0.9;
      const end = cx + radius * 0.9;
      const points = 80;
      const top: Array<[number, number]> = [];
      const bottom: Array<[number, number]> = [];
      for (let index = 0; index <= points; index += 1) {
        const progress = index / points;
        const x = start + (end - start) * progress;
        const wave = Math.sin(progress * Math.PI * 2 + phase) * amplitude;
        const twist = Math.sin(progress * Math.PI * 3 + phase * 1.7) * radius * 0.05;
        const thickness = radius * (0.035 + 0.075 * Math.abs(Math.sin(progress * Math.PI * 2 + phase * 0.8)));
        top.push([x, cy + wave + twist - thickness]);
        bottom.push([x, cy + wave + twist + thickness]);
      }

      context.save();
      context.beginPath();
      context.arc(cx, cy, radius, 0, Math.PI * 2);
      context.clip();
      const ribbon = context.createLinearGradient(start, cy, end, cy);
      ribbon.addColorStop(0, css("--orb-ribbon-start", "rgb(153,165,197)"));
      ribbon.addColorStop(0.42, css("--orb-ribbon-mid", "rgb(87,160,251)"));
      ribbon.addColorStop(1, css("--orb-ribbon-end", "rgb(110,218,253)"));
      context.filter = "blur(2px)";
      context.beginPath();
      top.forEach(([x, y], index) => index === 0 ? context.moveTo(x, y) : context.lineTo(x, y));
      bottom.slice().reverse().forEach(([x, y]) => context.lineTo(x, y));
      context.closePath();
      context.fillStyle = ribbon;
      context.fill();
      context.filter = "none";
      for (let strand = 1; strand < 10; strand += 1) {
        const ratio = strand / 10;
        context.beginPath();
        top.forEach(([x, y], index) => {
          const lower = bottom[points - index];
          const strandY = y + (lower[1] - y) * ratio;
          if (index === 0) context.moveTo(x, strandY); else context.lineTo(x, strandY);
        });
        context.strokeStyle = css("--orb-strand", "rgba(255,255,255,.28)");
        context.lineWidth = 0.6;
        context.stroke();
      }
      const body = context.createRadialGradient(cx - radius * 0.28, cy - radius * 0.42, radius * 0.04, cx, cy, radius * 1.05);
      body.addColorStop(0, css("--orb-highlight", "rgba(255,255,255,.74)"));
      body.addColorStop(0.25, css("--orb-body", "rgba(213,219,238,.46)"));
      body.addColorStop(0.72, css("--orb-body", "rgba(213,219,238,.2)"));
      body.addColorStop(1, css("--orb-shade", "rgba(177,186,202,.38)"));
      context.fillStyle = body;
      context.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
      context.strokeStyle = css("--orb-rim", "rgba(255,255,255,.42)");
      context.lineWidth = 1;
      context.beginPath();
      context.arc(cx, cy, radius - 0.5, 0, Math.PI * 2);
      context.stroke();
      context.restore();
    };

    const animate = (time: number) => {
      if (visible && !document.hidden) {
        draw(reduced ? 0 : time);
      }
      if (!reduced) frame = requestAnimationFrame(animate);
    };
    const observer = new ResizeObserver(resize);
    const visibility = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; });
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const motionChange = () => { reduced = motion.matches; if (reduced) draw(0); };
    const themeObserver = new MutationObserver(() => draw(0));
    observer.observe(shell);
    visibility.observe(shell);
    motion.addEventListener("change", motionChange);
    themeObserver.observe(root, { attributes: true, attributeFilter: ["class"] });
    resize();
    frame = requestAnimationFrame(animate);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); visibility.disconnect(); themeObserver.disconnect(); motion.removeEventListener("change", motionChange); };
  }, [state]);

  return <div ref={shellRef} className={`voice-orb-shell orb-${state}`} role="img" aria-label="Animated frosted glass voice assistant orb"><canvas ref={canvasRef} aria-hidden="true" /></div>;
}
