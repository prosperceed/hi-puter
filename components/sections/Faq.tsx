import { Accordion } from "@/components/ui/Accordion";
import { Container } from "@/components/layout/Container";
import { SectionHeading } from "@/components/layout/Section";
import { faqItems } from "@/content/site";

export function Faq() {
  return (
    <section id="faq" className="section faq-section">
      <Container className="faq-layout">
        <SectionHeading
          eyebrow="Questions"
          title="Before you say hello."
          intro="Short answers to what people ask first."
        />
        <Accordion items={faqItems} />
      </Container>
    </section>
  );
}
