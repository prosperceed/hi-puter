import Link from "next/link";
import { Wordmark } from "@/components/brand/Wordmark";

export function Footer() {
  return (
    <footer className="footer ticked">
      <div className="container footer-grid">
        <div>
          <Wordmark />
          <p className="footer-copy">Voice control for the computer you already use.</p>
        </div>
        <nav className="footer-links" aria-label="Footer">
          <Link href="/#how-it-works">How it works</Link>
          <Link href="/#commands">Commands</Link>
          <Link href="/#privacy">Privacy</Link>
          <Link href="/#install">Install</Link>
          <Link href="/docs">Setup guide</Link>
        </nav>
        <p className="footer-meta">
          Windows + Linux · Built local-first
        </p>
      </div>
    </footer>
  );
}
