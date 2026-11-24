import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Glow } from "@/components/visuals/Glow";
import { VoiceConsole } from "@/components/visuals/VoiceConsole";

export function Hero() {
  return (
    <section className="hero">
      <Glow />
      <p className="badge">
        <span className="live-dot" aria-hidden="true" />
        Local voice assistant for Windows &amp; Linux
      </p>
      <h1>Your computer, at your command.</h1>
      <p className="hero-subhead">Choose a name, say it, and get things done. Hi-Puter runs on your machine, not in the cloud.</p>
      <div className="hero-actions">
        <Button href="#install">
          Install Hi-Puter
          <ArrowRight className="icon-trail" size={17} aria-hidden="true" />
        </Button>
        <Button href="#how-it-works" variant="secondary">
          See how it works
        </Button>
      </div>
      <div className="hero-console">
        <VoiceConsole />
      </div>
    </section>
  );
}
