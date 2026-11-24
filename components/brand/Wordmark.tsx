import Link from "next/link";
import { AudioLines } from "lucide-react";

export function Wordmark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="wordmark" aria-label="Hi-Puter home">
      <span className="wordmark-mark" aria-hidden="true">
        <AudioLines size={16} strokeWidth={2.25} />
      </span>
      <span>
        Hi<span className="wordmark-dash">-</span>Puter
      </span>
    </Link>
  );
}
