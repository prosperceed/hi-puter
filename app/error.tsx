"use client";

import { Glow } from "@/components/visuals/Glow";
import { RotateCcw, TriangleAlert } from "lucide-react";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="error-screen">
      <Glow />
      <span className="icon-mark error-icon" aria-hidden="true"><TriangleAlert size={26} /></span>
      <p className="eyebrow">Something went quiet</p>
      <h1>Hi-Puter needs a restart.</h1>
      <button className="button button-primary" type="button" onClick={() => reset()}>
        <RotateCcw size={17} aria-hidden="true" />
        Try again
      </button>
    </main>
  );
}
