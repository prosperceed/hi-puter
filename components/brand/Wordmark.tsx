import Link from "next/link";

export function Wordmark({ href = "/" }: { href?: string }) {
  return <Link href={href} className="wordmark" aria-label="Hi-Puter home">Hi<span>-</span>Puter</Link>;
}
