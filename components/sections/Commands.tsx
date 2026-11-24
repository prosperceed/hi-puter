"use client";

import { useState } from "react";
import { Section } from "@/components/layout/Section";
import { commandGroups } from "@/content/commands";
import { motion } from "framer-motion";

export function Commands() {
  const [active, setActive] = useState(0);
  return <Section id="commands" className="commands-section" eyebrow="The vocabulary" title="Say what you mean." intro="A few useful things to say on day one. No special syntax to learn."><div className="commands-panel"><div className="command-tabs" role="tablist" aria-label="Command categories">{commandGroups.map((group, index) => <button key={group.label} type="button" role="tab" aria-selected={active === index} className={active === index ? "active" : ""} onClick={() => setActive(index)}>{group.label}</button>)}</div><div className="command-list">{commandGroups[active].examples.map((example, index) => <motion.div className="command-row" key={example} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.08 }} whileHover={{ x: 8, backgroundColor: "rgba(184,255,61,.04)" }}><span className="command-orb" aria-hidden="true" /><span className="command-quote">“</span><p>{example}</p><span className="command-wave" aria-hidden="true"><i /><i /><i /></span></motion.div>)}</div></div></Section>;
}
