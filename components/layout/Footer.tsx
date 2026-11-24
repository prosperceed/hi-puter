import Link from "next/link";
import { Wordmark } from "@/components/brand/Wordmark";

export function Footer() {
  return <footer className="footer"><div className="container footer-grid"><div><Wordmark /><p className="footer-copy">Voice control for the computer you already use.</p></div><div className="footer-links"><Link href="#how-it-works">How it works</Link><Link href="#privacy">Privacy</Link><Link href="#install">Install</Link></div><p className="footer-meta">Windows + Linux · Built local-first</p></div></footer>;
}
