import type { ReactNode } from "react";
import { Container } from "./Container";

export function Section({ id, eyebrow, title, intro, children, className = "" }: { id?: string; eyebrow?: string; title?: string; intro?: string; children?: ReactNode; className?: string }) {
  return <section id={id} className={`section ${className}`}><Container>{(eyebrow || title || intro) && <div className="section-heading">{eyebrow && <p className="eyebrow">{eyebrow}</p>}{title && <h2>{title}</h2>}{intro && <p className="section-intro">{intro}</p>}</div>}{children}</Container></section>;
}
