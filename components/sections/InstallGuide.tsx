"use client";

import { useState } from "react";
import { Section } from "@/components/layout/Section";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { installCommands } from "@/content/site";

const platforms = { Windows: { prompt: "PS C:\\Users\\you>", note: "Windows 10 or later with Python 3.10+" }, Linux: { prompt: "$", note: "A recent Linux distribution with Python 3.10+" } } as const;

export function InstallGuide() {
  const [platform, setPlatform] = useState<keyof typeof platforms>("Windows");
  const install = installCommands.install;
  return <Section id="install" className="install-section" eyebrow="Start here" title="Install once. Talk to your computer." intro="Hi-Puter lives in your terminal. Setup takes a minute, then it is ready when you are."><div className="install-layout"><div className="install-main"><div className="platform-tabs" role="tablist" aria-label="Choose your platform">{(Object.keys(platforms) as Array<keyof typeof platforms>).map((item) => <button key={item} type="button" role="tab" aria-selected={platform === item} className={platform === item ? "active" : ""} onClick={() => setPlatform(item)}><span className={item === "Windows" ? "platform-mark windows" : "platform-mark linux"} aria-hidden="true">{item === "Windows" ? "W" : "L"}</span>{item}</button>)}</div><p className="platform-note"><span className="note-mark" aria-hidden="true">+</span> {platforms[platform].note}</p><CodeBlock command={install} label={platforms[platform].prompt} /><div className="install-steps"><CodeBlock command={installCommands.setup} label="Setup" /><CodeBlock command={installCommands.start} label="Start" /></div></div><aside className="install-aside"><h3>After that</h3><CodeBlock command={installCommands.stop} label="Stop listening" /><CodeBlock command={installCommands.status} label="Check status" /><CodeBlock command={installCommands.rename} label="Choose another name" /><details><summary>Troubleshooting</summary><p>Allow microphone access when your OS asks. On Linux, install PortAudio if setup reports a missing audio library.</p></details></aside></div></Section>;
}
