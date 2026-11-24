import { Section } from "@/components/layout/Section";
import { howItWorks } from "@/content/steps";
import { MotionReveal } from "@/components/ui/MotionReveal";

export function HowItWorks() {
  return <Section id="how-it-works" className="how-section" eyebrow="The loop" title="A small loop with a clear off switch." intro="Hi-Puter is quiet by default. You decide when it is active and what it is allowed to do."><MotionReveal className="steps-grid">{howItWorks.map((step) => <article className="step-card" key={step.number}><span className="step-spark" aria-hidden="true">✦</span><div><h3>{step.title}</h3><p>{step.body}</p></div></article>)}</MotionReveal></Section>;
}
