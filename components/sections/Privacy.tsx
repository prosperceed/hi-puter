import { ShieldCheck } from "lucide-react";
import { Section } from "@/components/layout/Section";
import { Glow } from "@/components/visuals/Glow";
import { privacyPoints } from "@/content/steps";

export function Privacy() {
  return (
    <Section
      id="privacy"
      eyebrow="The control layer"
      title="Useful, without giving up control."
      intro="Hi-Puter is built around a simple promise: your voice should operate your computer without leaving it."
    >
      <div className="privacy-layout">
        <div className="privacy-badge">
          <Glow small />
          <span className="privacy-badge-icon" aria-hidden="true">
            <ShieldCheck size={24} strokeWidth={1.75} />
          </span>
          <span>
            Local-first
            <strong>by design</strong>
          </span>
        </div>
        <div className="privacy-points">
          {privacyPoints.map(({ label, detail, icon: Icon }) => (
            <div className="privacy-point" key={label}>
              <span className="icon-mark" aria-hidden="true"><Icon size={18} strokeWidth={1.75} /></span>
              <div>
                <h3>{label}</h3>
                <p>{detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
