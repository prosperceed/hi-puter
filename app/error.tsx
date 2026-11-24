"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <main className="error-screen"><p className="eyebrow">Something went quiet</p><h1>Hi-Puter needs a restart.</h1><button className="button button-primary" type="button" onClick={() => reset()}>Try again</button></main>; }
