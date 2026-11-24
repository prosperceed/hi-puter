import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { installCommands } from "@/content/site";

export function FinalCta() {
  return (
    <section className="final-cta">
      <div className="container">
        <div className="final-cta-card card">
          <p className="eyebrow">One command away</p>
          <h2>
            Give your computer
            <br />
            <em>a voice.</em>
          </h2>
          <p className="final-cta-copy">Install Hi-Puter and choose a name that feels like yours.</p>
          <div className="final-cta-actions">
            <Button href="#install">
              Get started
              <ArrowRight className="icon-trail" size={17} aria-hidden="true" />
            </Button>
            <CodeBlock command={installCommands.install} variant="inline" />
          </div>
        </div>
      </div>
    </section>
  );
}
