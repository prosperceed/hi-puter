import type { ReactNode } from "react";
import { Container } from "./Container";

type SectionProps = {
  id?: string;
  eyebrow?: string;
  title?: string;
  intro?: string;
  children?: ReactNode;
  className?: string;
};

export function SectionHeading({ eyebrow, title, intro }: Pick<SectionProps, "eyebrow" | "title" | "intro">) {
  return (
    <div className="section-heading">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      {title && <h2>{title}</h2>}
      {intro && <p className="section-intro">{intro}</p>}
    </div>
  );
}

export function Section({ id, eyebrow, title, intro, children, className = "" }: SectionProps) {
  return (
    <section id={id} className={`section ${className}`}>
      <Container>
        {(eyebrow || title || intro) && <SectionHeading eyebrow={eyebrow} title={title} intro={intro} />}
        {children}
      </Container>
    </section>
  );
}
