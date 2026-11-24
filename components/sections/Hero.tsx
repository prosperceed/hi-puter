import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { HeroVisual } from "@/components/visuals/HeroVisual";
import { installCommands } from "@/content/site";

export function Hero() {
  return <section className="hero"><div className="container hero-grid"><div className="hero-copy"><p className="eyebrow"><span className="eyebrow-mark" /> A voice layer for your OS</p><h1>Your computer,<br /><em>at your command.</em></h1><p className="hero-subhead">Hi-Puter is a local voice assistant for Windows and Linux. Choose a name, say it, and get things done.</p><div className="hero-actions"><Button href="#install">Install Hi-Puter <span aria-hidden="true">↗</span></Button><Button href="#how-it-works" variant="secondary">See how it works</Button></div><div className="hero-install"><span className="terminal-mark" aria-hidden="true">$_</span><CodeBlock command={installCommands.install} label="Get started" /></div></div><HeroVisual /></div></section>;
}
