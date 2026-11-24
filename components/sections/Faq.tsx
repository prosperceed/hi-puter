import { Accordion } from "@/components/ui/Accordion";
import { Section } from "@/components/layout/Section";
import { faqItems } from "@/content/site";

export function Faq() {
  return <Section className="faq-section" eyebrow="Questions" title="Before you say hello."><Accordion items={faqItems} /></Section>;
}
