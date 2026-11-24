import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

export default function DownloadPlaceholder() {
  return (
    <main className="error-screen">
      <span className="icon-chip error-icon" aria-hidden="true"><Download size={26} /></span>
      <p className="eyebrow">Downloads / Coming soon</p>
      <h1>Releases will live here.</h1>
      <Link className="button button-secondary" href="/#install">
        <ArrowLeft size={17} aria-hidden="true" />
        Install from the terminal
      </Link>
    </main>
  );
}
