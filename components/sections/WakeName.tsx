"use client";

import { useState } from "react";
import { AtSign, AudioLines } from "lucide-react";
import { Section } from "@/components/layout/Section";
import { Glow } from "@/components/visuals/Glow";

const fallbackName = "Nova";
const maxLength = 20;
const sanitize = (value: string) => value.replace(/[^a-zA-Z0-9 ]/g, "").slice(0, maxLength);

export function WakeName() {
  const [name, setName] = useState(fallbackName);
  const safeName = sanitize(name.trim()) || fallbackName;

  return (
    <Section
      eyebrow="Make it yours"
      title="Your name, your assistant."
      intro="Pick a wake name that feels natural. See how it sounds before you install."
    >
      <div className="wake-demo">
        <div className="wake-input-wrap">
          <label className="field-label" htmlFor="wake-name">
            <AtSign size={14} aria-hidden="true" />
            Wake name
          </label>
          <input
            id="wake-name"
            value={name}
            onChange={(event) => setName(sanitize(event.target.value))}
            maxLength={maxLength}
            autoComplete="off"
            spellCheck={false}
          />
          <div className="wake-meta">
            <span>Letters, numbers, spaces</span>
            <span>{name.length}/{maxLength}</span>
          </div>
        </div>
        <div className="wake-output">
          <Glow small />
          <span className="field-label">
            <AudioLines size={14} aria-hidden="true" />
            Try saying
          </span>
          <p>“{safeName}, open Firefox.”</p>
        </div>
      </div>
    </Section>
  );
}
