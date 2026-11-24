"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

export function CopyButton({ value, iconOnly = false }: { value: string; iconOnly?: boolean }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  const Icon = copied ? Check : Copy;
  return (
    <button
      className={`copy-button${copied ? " copied" : ""}${iconOnly ? " icon-only" : ""}`}
      type="button"
      onClick={copy}
      aria-label={copied ? "Copied" : `Copy ${value}`}
      title={copied ? "Copied" : "Copy command"}
    >
      <Icon size={14} aria-hidden="true" />
      {!iconOnly && (copied ? "Copied" : "Copy")}
    </button>
  );
}
