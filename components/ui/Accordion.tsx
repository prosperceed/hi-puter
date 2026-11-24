"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

type AccordionItem = { question: string; answer: string };

export function Accordion({ items }: { items: readonly AccordionItem[] }) {
  const [active, setActive] = useState<number | null>(0);

  return (
    <div className="accordion">
      {items.map((item, index) => {
        const isOpen = active === index;
        return (
          <div className="accordion-item" key={item.question}>
            <button
              id={`faq-trigger-${index}`}
              className="accordion-trigger"
              type="button"
              aria-expanded={isOpen}
              aria-controls={`faq-answer-${index}`}
              onClick={() => setActive(isOpen ? null : index)}
            >
              <span>{item.question}</span>
              <span className="accordion-icon" aria-hidden="true">
                <Plus size={16} />
              </span>
            </button>
            <div
              id={`faq-answer-${index}`}
              className={isOpen ? "accordion-answer is-open" : "accordion-answer"}
              role="region"
              aria-labelledby={`faq-trigger-${index}`}
            >
              <div>
                <p>{item.answer}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
