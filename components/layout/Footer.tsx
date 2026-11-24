import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Wordmark } from "@/components/brand/Wordmark";

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <Wordmark />
          <p className="footer-copy">Voice control for the computer you already use.</p>
        </div>
        <nav className="footer-links" aria-label="Footer">
          <Link href="#how-it-works">How it works</Link>
          <Link href="#commands">Commands</Link>
          <Link href="#privacy">Privacy</Link>
          <Link href="#install">Install</Link>
        </nav>
        <p className="footer-meta">
          <ShieldCheck size={15} aria-hidden="true" />
          Windows + Linux · Built local-first
        </p>
      </div>
    </footer>
  );
}
