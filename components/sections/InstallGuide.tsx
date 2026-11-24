"use client";

import { useState } from "react";
import { ChevronDown, Info, Wrench } from "lucide-react";
import { FaLinux, FaWindows } from "react-icons/fa6";
import { Section } from "@/components/layout/Section";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { installCommands } from "@/content/site";

const platforms = {
  Windows: { icon: FaWindows, shell: "PowerShell", prompt: "PS>", note: "Windows 10 or later with Python 3.10+" },
  Linux: { icon: FaLinux, shell: "Terminal", prompt: "$", note: "A recent Linux distribution with Python 3.10+" },
} as const;

type Platform = keyof typeof platforms;

const steps = [
  { title: "Install the package", command: installCommands.install },
  { title: "Run setup once", command: installCommands.setup },
  { title: "Start listening", command: installCommands.start },
] as const;

const afterCommands = [
  { label: "Stop listening", command: installCommands.stop },
  { label: "Check status", command: installCommands.status },
  { label: "Choose another name", command: installCommands.rename },
] as const;

export function InstallGuide() {
  const [platform, setPlatform] = useState<Platform>("Windows");
  const current = platforms[platform];

  return (
    <Section
      id="install"
      eyebrow="Start here"
      title="Install once. Talk to your computer."
      intro="Hi-Puter lives in your terminal. Setup takes a minute, then it is ready when you are."
    >
      <div className="install-layout">
        <div className="install-main">
          <div className="tabs" role="tablist" aria-label="Choose your platform">
            {(Object.keys(platforms) as Platform[]).map((item) => {
              const Icon = platforms[item].icon;
              return (
                <button
                  key={item}
                  type="button"
                  role="tab"
                  aria-selected={platform === item}
                  className={platform === item ? "active" : ""}
                  onClick={() => setPlatform(item)}
                >
                  <Icon size={15} aria-hidden="true" />
                  {item}
                </button>
              );
            })}
          </div>
          <div role="tabpanel">
            <p className="platform-note">
              <Info size={16} aria-hidden="true" />
              {current.note}
            </p>
            <ol className="install-steps">
              {steps.map((step, index) => (
                <li className="install-step" key={step.command}>
                  <span className="install-step-number" aria-hidden="true">{index + 1}</span>
                  <div>
                    <h4>{step.title}</h4>
                    <CodeBlock command={step.command} label={current.shell} prompt={current.prompt} />
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
        <aside className="install-aside">
          <h3>After that</h3>
          {afterCommands.map((item) => (
            <CodeBlock key={item.command} command={item.command} label={item.label} prompt={current.prompt} />
          ))}
          <details>
            <summary>
              <Wrench size={15} aria-hidden="true" />
              Troubleshooting
              <ChevronDown className="chevron" size={16} aria-hidden="true" />
            </summary>
            <p>Allow microphone access when your OS asks. On Linux, install PortAudio if setup reports a missing audio library.</p>
          </details>
        </aside>
      </div>
    </Section>
  );
}
