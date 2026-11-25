import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Ear,
  HardDrive,
  type LucideIcon,
  MemoryStick,
  Mic,
  Monitor,
  SquareTerminal,
  Volume2,
  Wifi,
} from "lucide-react";
import { Mark } from "@/components/brand/Mark";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import { SetupSteps } from "@/components/setup/SetupSteps";
import { Accordion } from "@/components/ui/Accordion";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { Glow } from "@/components/visuals/Glow";
import {
  doctorOutput,
  firstRunTips,
  fromSource,
  maintenance,
  models,
  pieces,
  requirements,
  troubleshooting,
} from "@/content/setup";

export const metadata: Metadata = {
  title: "Setup guide",
  description:
    "Install Hi-Puter, its speech recognition and a local AI model, check everything works, and fix common problems.",
};

const contents = [
  { id: "requirements", label: "What you need" },
  { id: "pieces", label: "How it fits together" },
  { id: "install", label: "Install" },
  { id: "models", label: "Choose a model" },
  { id: "check", label: "Check everything" },
  { id: "first-run", label: "First run" },
  { id: "troubleshooting", label: "Troubleshooting" },
  { id: "maintenance", label: "Update or remove" },
  { id: "source", label: "From source" },
] as const;

const requirementIcons: Record<string, LucideIcon> = {
  System: Monitor,
  Python: SquareTerminal,
  Memory: MemoryStick,
  Disk: HardDrive,
  Microphone: Mic,
  Internet: Wifi,
};

const pieceIcons = [null, Ear, Volume2, Brain] as const;

function DocSection({
  id,
  title,
  intro,
  children,
}: {
  id: string;
  title: string;
  intro?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="doc-section" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>{title}</h2>
      {intro && <p className="doc-intro">{intro}</p>}
      {children}
    </section>
  );
}

export default function SetupGuide() {
  return (
    <>
      <div className="spectrum-bar" aria-hidden="true" />
      <div className="frame">
        <Navbar />
        <main className="docs">
          <header className="docs-hero">
            <Glow small />
            <p className="eyebrow">Docs / Setup guide</p>
            <h1>Set up Hi-Puter</h1>
            <p className="docs-lede">
              Everything Hi-Puter needs runs on your own computer: the assistant, the speech
              recognition that lets it hear you, a voice to answer with, and a local AI model to
              think with. This guide installs all four and checks they work together.
            </p>
          </header>

          <div className="docs-layout">
            <nav className="docs-toc" aria-label="On this page">
              <p className="eyebrow">On this page</p>
              <ol>
                {contents.map((item) => (
                  <li key={item.id}>
                    <a href={`#${item.id}`}>{item.label}</a>
                  </li>
                ))}
              </ol>
            </nav>

            <div className="docs-content">
              <DocSection id="requirements" title="What you need">
                <ul className="requirement-grid">
                  {requirements.map((item) => {
                    const Icon = requirementIcons[item.label] ?? Monitor;
                    return (
                      <li key={item.label}>
                        <Icon size={18} strokeWidth={1.75} aria-hidden="true" />
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </li>
                    );
                  })}
                </ul>
              </DocSection>

              <DocSection
                id="pieces"
                title="How it fits together"
                intro="Hi-Puter is made of four parts. The install steps add them in this order, and hi-puter doctor checks each one."
              >
                <ol className="piece-grid">
                  {pieces.map((piece, index) => {
                    const Icon = pieceIcons[index];
                    return (
                      <li key={piece.name}>
                        <span className="icon-mark" aria-hidden="true">
                          {Icon ? <Icon size={18} strokeWidth={1.75} /> : <Mark size={20} />}
                        </span>
                        <span className="piece-role">{piece.role}</span>
                        <strong>{piece.name}</strong>
                        <p>{piece.detail}</p>
                      </li>
                    );
                  })}
                </ol>
              </DocSection>

              <DocSection
                id="install"
                title="Install"
                intro="Run each step in a terminal. Copy buttons give you the exact command."
              >
                <div className="doc-panel">
                  <SetupSteps idPrefix="guide" />
                </div>
              </DocSection>

              <DocSection
                id="models"
                title="Choose a model"
                intro="The model is Hi-Puter's brain. Bigger models understand more but need more memory; pick by how much RAM your computer has."
              >
                <div className="model-table" role="table" aria-label="Models by memory">
                  <div className="model-row model-head" role="row">
                    <span role="columnheader">Your memory</span>
                    <span role="columnheader">Model</span>
                    <span role="columnheader">Download</span>
                    <span role="columnheader">Good for</span>
                  </div>
                  {models.map((item) => (
                    <div className="model-row" role="row" key={item.model}>
                      <span role="cell">{item.memory}</span>
                      <span role="cell">
                        <code>{item.model}</code>
                      </span>
                      <span role="cell">{item.download}</span>
                      <span role="cell">{item.fit}</span>
                    </div>
                  ))}
                </div>
                <p className="doc-note">
                  You can keep both and switch any time, for example after a RAM upgrade:
                </p>
                <CodeBlock command="hi-puter model qwen3.5:4b" label="Switch models" />
              </DocSection>

              <DocSection
                id="check"
                title="Check everything"
                intro="hi-puter doctor checks each piece. On a working setup every line says PASS:"
              >
                <pre className="doctor-output" aria-label="Example output of hi-puter doctor">
                  {doctorOutput.split("\n").map((line) => (
                    <span key={line}>
                      <b className={line.startsWith("PASS") ? "pass" : "warn"}>{line.slice(0, 4)}</b>
                      {line.slice(4)}
                      {"\n"}
                    </span>
                  ))}
                </pre>
                <p className="doc-note">
                  A FAIL or WARN line names what is missing.{" "}
                  <a href="#troubleshooting">Troubleshooting</a> has the fix for each one.
                </p>
              </DocSection>

              <DocSection id="first-run" title="First run">
                <ul className="tip-grid">
                  {firstRunTips.map((tip) => (
                    <li key={tip.title}>
                      <strong>{tip.title}</strong>
                      <p>{tip.body}</p>
                    </li>
                  ))}
                </ul>
              </DocSection>

              <DocSection id="troubleshooting" title="Troubleshooting">
                <Accordion items={troubleshooting} idPrefix="trouble" openFirst={false} />
              </DocSection>

              <DocSection id="maintenance" title="Update or remove">
                <div className="command-grid">
                  {maintenance.map((item) => (
                    <CodeBlock key={item.command} command={item.command} label={item.label} />
                  ))}
                </div>
              </DocSection>

              <DocSection
                id="source"
                title="From source"
                intro="For contributors, or to try changes that aren't released yet."
              >
                <div className="command-stack">
                  {fromSource.map((command) => (
                    <CodeBlock key={command} command={command} />
                  ))}
                </div>
              </DocSection>

              <div className="docs-end">
                <p>Set up and listening?</p>
                <Link className="button button-primary" href="/#commands">
                  See what to say
                  <ArrowRight className="icon-trail" size={16} aria-hidden="true" />
                </Link>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
