import { Section } from "@/components/layout/Section";
import { howItWorks } from "@/content/steps";
import { MotionReveal } from "@/components/ui/MotionReveal";

export function HowItWorks() {
  return (
    <Section
      id="how-it-works"
      eyebrow="The loop"
      title="A small loop with a clear off switch."
      intro="Hi-Puter is quiet by default. You decide when it is active and what it is allowed to do."
    >
      <MotionReveal className="steps-grid">
        {howItWorks.map(({ number, title, body, icon: Icon }) => (
          <article className="step-card" key={number}>
            <div className="step-head">
              <span className="icon-mark" aria-hidden="true"><Icon size={18} strokeWidth={1.75} /></span>
              <span className="step-number">{number}</span>
            </div>
            <h3>{title}</h3>
            <p>{body}</p>
          </article>
        ))}
      </MotionReveal>
    </Section>
  );
}
