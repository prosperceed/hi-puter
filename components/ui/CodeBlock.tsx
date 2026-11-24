import { CopyButton } from "./CopyButton";

export function CodeBlock({ command, label = "Terminal" }: { command: string; label?: string }) {
  return <div className="code-block"><div className="code-top"><span><i className="status-dot" /> {label}</span><CopyButton value={command} /></div><code><span className="prompt">$</span> {command}</code></div>;
}
