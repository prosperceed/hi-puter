import Link from "next/link";
import { Glow } from "@/components/visuals/Glow";
import { ArrowLeft } from "lucide-react";
import { Mark } from "@/components/brand/Mark";

export default function DownloadPlaceholder() {
  return (
    <main className="error-screen">
      <Glow />
      <Mark size={56} />
      <p className="eyebrow">Downloads / Coming soon</p>
      <h1>Releases will live here.</h1>
      <Link className="button button-secondary" href="/#install">
        <ArrowLeft size={17} aria-hidden="true" />
        Install from the terminal
      </Link>
    </main>
  );
}
