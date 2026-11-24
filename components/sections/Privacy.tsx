import { Section } from "@/components/layout/Section";
import { privacyPoints } from "@/content/steps";

export function Privacy() {
  return <Section id="privacy" className="privacy-section" eyebrow="The control layer" title="Useful, without giving up control." intro="Hi-Puter is built around a simple promise: your voice should operate your computer without leaving it." ><div className="privacy-layout"><div className="privacy-badge"><span className="privacy-signal" aria-hidden="true"><i /><i /><i /><i /></span><span>Local-first<br /><strong>by design</strong></span></div><div className="privacy-points">{privacyPoints.map((point) => <div className="privacy-point" key={point.label}><span className="check-mark">✦</span><div><h3>{point.label}</h3><p>{point.detail}</p></div></div>)}</div></div></Section>;
}
