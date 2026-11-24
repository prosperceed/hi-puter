"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { CornerDownLeft } from "lucide-react";
import { Section } from "@/components/layout/Section";
import { commandGroups } from "@/content/commands";

export function Commands() {
  const [active, setActive] = useState(0);

  return (
    <Section
      id="commands"
      className="commands-section"
      eyebrow="The vocabulary"
      title="Say what you mean."
      intro="A few useful things to say on day one. No special syntax to learn."
    >
      <div className="commands-panel card">
        <div className="tabs" role="tablist" aria-label="Command categories">
          {commandGroups.map(({ label, icon: Icon }, index) => (
            <button
              key={label}
              type="button"
              role="tab"
              id={`command-tab-${index}`}
              aria-selected={active === index}
              aria-controls="command-panel"
              className={active === index ? "active" : ""}
              onClick={() => setActive(index)}
            >
              <Icon size={15} aria-hidden="true" />
              {label}
            </button>
          ))}
        </div>
        <div className="command-list" id="command-panel" role="tabpanel" aria-labelledby={`command-tab-${active}`}>
          {commandGroups[active].examples.map(({ phrase, icon: Icon }, index) => (
            <motion.div
              className="command-row"
              key={phrase}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06, duration: 0.25, ease: "easeOut" }}
            >
              <span className="icon-chip sm" aria-hidden="true"><Icon size={17} /></span>
              <p>
                <span className="quote">“</span>
                {phrase}
                <span className="quote">”</span>
              </p>
              <span className="command-hint" aria-hidden="true">
                say it <CornerDownLeft size={13} />
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </Section>
  );
}
