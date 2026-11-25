import Link from "next/link";
import { Glow } from "@/components/visuals/Glow";
import { ArrowLeft } from "lucide-react";
import { Mark } from "@/components/brand/Mark";

export default function NotFound() {
  return (
    <main className="error-screen">
      <Glow />
      <Mark size={56} />
      <p className="eyebrow">404 / Not found</p>
      <h1>This command does not exist.</h1>
      <Link className="button button-primary" href="/">
        <ArrowLeft size={17} aria-hidden="true" />
        Back home
      </Link>
    </main>
  );
}
