import { ArrowRight, Monitor, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { HeroVisual } from "@/components/visuals/HeroVisual";
import { installCommands } from "@/content/site";

export function Hero() {
  return (
    <section className="hero">
      <div className="container hero-grid">
        <div className="hero-copy">
          <p className="badge">
            <span className="badge-dot" aria-hidden="true" />
            A voice layer for your OS
          </p>
          <h1>
            Your computer,
            <br />
            <em>at your command.</em>
          </h1>
          <p className="hero-subhead">
            Hi-Puter is a local voice assistant for Windows and Linux. Choose a name, say it, and get things done.
          </p>
          <div className="hero-actions">
            <Button href="#install">
              Install Hi-Puter
              <ArrowRight className="icon-trail" size={17} aria-hidden="true" />
            </Button>
            <Button href="#how-it-works" variant="secondary">
              See how it works
            </Button>
          </div>
          <div className="hero-install">
            <CodeBlock command={installCommands.install} variant="inline" />
          </div>
          <ul className="hero-meta">
            <li><Monitor size={15} aria-hidden="true" />Windows &amp; Linux</li>
            <li><ShieldCheck size={15} aria-hidden="true" />Processed locally</li>
            <li><Sparkles size={15} aria-hidden="true" />Free to use</li>
          </ul>
        </div>
        <HeroVisual />
      </div>
    </section>
  );
}
