import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";

export default function DocsPlaceholder() {
  return (
    <main className="error-screen">
      <span className="icon-chip error-icon" aria-hidden="true"><BookOpen size={26} /></span>
      <p className="eyebrow">Docs / Coming soon</p>
      <h1>Documentation is on its way.</h1>
      <Link className="button button-secondary" href="/">
        <ArrowLeft size={17} aria-hidden="true" />
        Back home
      </Link>
    </main>
  );
}
