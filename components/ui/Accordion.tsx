"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

type AccordionItem = { question: string; answer: string };

export function Accordion({
  items,
  idPrefix = "faq",
  openFirst = true,
}: {
  items: readonly AccordionItem[];
  idPrefix?: string;
  openFirst?: boolean;
}) {
  const [active, setActive] = useState<number | null>(openFirst ? 0 : null);

  return (
    <div className="accordion">
      {items.map((item, index) => {
        const isOpen = active === index;
        return (
          <div className="accordion-item" key={item.question}>
            <button
              id={`${idPrefix}-trigger-${index}`}
              className="accordion-trigger"
              type="button"
              aria-expanded={isOpen}
              aria-controls={`${idPrefix}-answer-${index}`}
              onClick={() => setActive(isOpen ? null : index)}
            >
              <span>{item.question}</span>
              <span className="accordion-icon" aria-hidden="true">
                <Plus size={16} />
              </span>
            </button>
            <div
              id={`${idPrefix}-answer-${index}`}
              className={isOpen ? "accordion-answer is-open" : "accordion-answer"}
              role="region"
              aria-labelledby={`${idPrefix}-trigger-${index}`}
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
