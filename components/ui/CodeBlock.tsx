import { SquareTerminal } from "lucide-react";
import { CopyButton } from "./CopyButton";

type CodeBlockProps = {
  command: string;
  label?: string;
  prompt?: string;
  variant?: "block" | "inline";
};

export function CodeBlock({ command, label = "Terminal", prompt = "$", variant = "block" }: CodeBlockProps) {
  if (variant === "inline") {
    return (
      <div className="code-inline">
        <span className="prompt" aria-hidden="true">{prompt}</span>
        <code>{command}</code>
        <CopyButton value={command} iconOnly />
      </div>
    );
  }

  return (
    <div className="code-block">
      <div className="code-top">
        <span className="code-label">
          <SquareTerminal size={13} aria-hidden="true" />
          {label}
        </span>
        <CopyButton value={command} />
      </div>
      <code>
        <span className="prompt" aria-hidden="true">{prompt}</span>
        <span>{command}</span>
      </code>
    </div>
  );
}
