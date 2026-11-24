"use client";

import { useEffect, useState } from "react";
import { ArrowUp, AudioLines, Check, Loader, Mic } from "lucide-react";

const exchanges = [
  { say: "Nova, open Firefox and search for local-first apps.", reply: "Opened Firefox with your search" },
  { say: "Nova, turn the volume down a little.", reply: "Volume set to 40%" },
  { say: "Nova, how much battery do I have?", reply: "82% — about three hours left" },
  { say: "Nova, take a screenshot.", reply: "Saved to Pictures/Screenshots" },
] as const;

const phases = ["Listening", "Working", "Done"] as const;
const tickMs = 1400;

/** Demo of a voice exchange: each command steps through listening → working → done. */
export function VoiceConsole() {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setTick((value) => value + 1), tickMs);
    return () => window.clearInterval(id);
  }, []);

  const exchange = exchanges[Math.floor(tick / phases.length) % exchanges.length];
  const phase = phases[tick % phases.length];

  return (
    <div className="console" role="img" aria-label="Example: saying “Nova, open Firefox” and Hi-Puter opening it">
      <div className="console-label" aria-hidden="true">
        <strong>
          <AudioLines size={13} />
          Nova
        </strong>
        <span>On-device</span>
      </div>
      <div className="console-body" aria-hidden="true">
        <p className="console-say console-fade" key={exchange.say}>“{exchange.say}”</p>
        {phase === "Done" && (
          <p className="console-reply console-fade">
            <Check size={15} />
            {exchange.reply}
          </p>
        )}
      </div>
      <div className="console-bar" aria-hidden="true">
        <span className="console-icon-btn"><Mic size={16} /></span>
        <span className="console-chip">
          {phase === "Listening" && <span className="mini-wave"><i /><i /><i /><i /></span>}
          {phase === "Working" && <Loader className="spin" size={15} />}
          {phase === "Done" && <Check size={15} />}
          <span className="chip-text">{phase}</span>
        </span>
        <span className="console-send"><ArrowUp size={16} /></span>
      </div>
    </div>
  );
}
