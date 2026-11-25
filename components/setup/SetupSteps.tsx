"use client";

import { useState, useSyncExternalStore } from "react";
import { FlaskConical, Info } from "lucide-react";
import { FaLinux, FaWindows } from "react-icons/fa6";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { type Platform, setupSteps, shells, windowsPreview } from "@/content/setup";

const platforms: { name: Platform; icon: typeof FaLinux; note: string }[] = [
  { name: "Linux", icon: FaLinux, note: "Ubuntu, Debian, Fedora or Arch with Python 3.10+" },
  { name: "Windows", icon: FaWindows, note: "Windows 10 or later" },
];

const noSubscription = () => () => {};
const browserPlatform = (): Platform => (/windows/i.test(navigator.userAgent) ? "Windows" : "Linux");
const serverPlatform = (): Platform => "Linux";

/** The install path for each platform: what to run, and why each step is there. */
export function SetupSteps({ idPrefix = "setup" }: { idPrefix?: string }) {
  // The server renders Linux; after hydration the visitor's own platform is pre-selected.
  const detected = useSyncExternalStore(noSubscription, browserPlatform, serverPlatform);
  const [chosen, setPlatform] = useState<Platform | null>(null);
  const platform = chosen ?? detected;

  const shell = shells[platform];
  const current = platforms.find((item) => item.name === platform) ?? platforms[0];

  return (
    <div className="setup-steps">
      <div className="tabs" role="tablist" aria-label="Choose your platform">
        {platforms.map(({ name, icon: Icon }) => (
          <button
            key={name}
            id={`${idPrefix}-tab-${name}`}
            type="button"
            role="tab"
            aria-selected={platform === name}
            aria-controls={`${idPrefix}-panel`}
            className={platform === name ? "active" : ""}
            onClick={() => setPlatform(name)}
          >
            <Icon size={15} aria-hidden="true" />
            {name}
          </button>
        ))}
      </div>
      <div id={`${idPrefix}-panel`} role="tabpanel" aria-labelledby={`${idPrefix}-tab-${platform}`}>
        <p className="platform-note">
          <Info size={16} aria-hidden="true" />
          {current.note}
        </p>
        {platform === "Windows" && (
          <p className="callout">
            <FlaskConical size={16} aria-hidden="true" />
            <span>{windowsPreview}</span>
          </p>
        )}
        <ol className="install-steps">
          {setupSteps[platform].map((step, index) => (
            <li className="install-step" key={`${platform}-${step.id}`}>
              <span className="install-step-number" aria-hidden="true">{index + 1}</span>
              <div className="install-step-body">
                <h4>{step.title}</h4>
                <p className="step-why">{step.why}</p>
                <div className="step-commands">
                  {step.commands.map((command) => (
                    <CodeBlock key={command} command={command} label={shell.label} prompt={shell.prompt} />
                  ))}
                </div>
                {step.note && <p className="step-note">{step.note}</p>}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
