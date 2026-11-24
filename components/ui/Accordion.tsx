"use client";

import { useState } from "react";

export function Accordion({ items }: { items: readonly { question: string; answer: string }[] }) {
  const [active, setActive] = useState<number | null>(null);
  return <div className="accordion">{items.map((item, index) => { const isOpen = active === index; return <div className="accordion-item" key={item.question}><button className="accordion-trigger" type="button" aria-expanded={isOpen} aria-controls={`faq-answer-${index}`} onClick={() => setActive(isOpen ? null : index)}><span>{item.question}</span><span className={isOpen ? "accordion-mark open" : "accordion-mark"} aria-hidden="true" /></button><div id={`faq-answer-${index}`} className={isOpen ? "accordion-answer is-open" : "accordion-answer"} role="region"><p>{item.answer}</p></div></div>; })}</div>;
}
