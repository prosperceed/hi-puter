import Link from "next/link";
import { Glow } from "@/components/visuals/Glow";
import { ArrowLeft } from "lucide-react";
import { Mark } from "@/components/brand/Mark";

export default function DocsPlaceholder() {
  return (
    <main className="error-screen">
      <Glow />
      <Mark size={56} />
      <p className="eyebrow">Docs / Coming soon</p>
      <h1>Documentation is on its way.</h1>
      <Link className="button button-secondary" href="/">
        <ArrowLeft size={17} aria-hidden="true" />
        Back home
      </Link>
    </main>
  );
}
