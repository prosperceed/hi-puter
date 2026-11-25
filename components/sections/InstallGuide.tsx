import Link from "next/link";
import { ArrowRight, BookOpen } from "lucide-react";
import { Section } from "@/components/layout/Section";
import { SetupSteps } from "@/components/setup/SetupSteps";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { requirements } from "@/content/setup";
import { installCommands } from "@/content/site";

const afterCommands = [
  { label: "Stop listening", command: installCommands.stop },
  { label: "Check status", command: installCommands.status },
  { label: "Choose another name", command: installCommands.rename },
] as const;

export function InstallGuide() {
  return (
    <Section
      id="install"
      eyebrow="Start here"
      title="Five steps to your first “Nova”."
      intro="Hi-Puter, its ears and its brain all install on your computer. Allow about ten minutes, most of it downloading."
    >
      <div className="install-layout">
        <div className="install-main">
          <SetupSteps idPrefix="install" />
        </div>
        <aside className="install-aside">
          <h3>What you need</h3>
          <dl className="requirements">
            {requirements.map((item) => (
              <div key={item.label}>
                <dt>{item.label}</dt>
                <dd>{item.value}</dd>
              </div>
            ))}
          </dl>
          <h3 className="aside-heading">After that</h3>
          {afterCommands.map((item) => (
            <CodeBlock key={item.command} command={item.command} label={item.label} />
          ))}
          <Link className="guide-link" href="/docs">
            <BookOpen size={16} aria-hidden="true" />
            <span>
              Full setup guide
              <small>Models, troubleshooting, updating</small>
            </span>
            <ArrowRight className="icon-trail" size={16} aria-hidden="true" />
          </Link>
        </aside>
      </div>
    </Section>
  );
}
