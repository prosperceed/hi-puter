"use client";

import { useState } from "react";

export function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(value); setCopied(true); window.setTimeout(() => setCopied(false), 1600); } catch { setCopied(false); }
  }
  return <button className="copy-button" type="button" onClick={copy} aria-label={`Copy ${value}`} title={copied ? "Copied" : "Copy command"}><span className={copied ? "copy-mark copied" : "copy-mark"} aria-hidden="true" />{copied ? "Done" : "Copy"}</button>;
}
