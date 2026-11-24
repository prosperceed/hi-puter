import Link from "next/link";
import { ArrowLeft, Compass } from "lucide-react";

export default function NotFound() {
  return (
    <main className="error-screen">
      <span className="icon-chip error-icon" aria-hidden="true"><Compass size={26} /></span>
      <p className="eyebrow">404 / Not found</p>
      <h1>This command does not exist.</h1>
      <Link className="button button-primary" href="/">
        <ArrowLeft size={17} aria-hidden="true" />
        Back home
      </Link>
    </main>
  );
}
