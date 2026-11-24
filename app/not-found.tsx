import Link from "next/link";

export default function NotFound() { return <main className="error-screen"><p className="eyebrow">404 / Not found</p><h1>This command does not exist.</h1><Link className="button button-primary" href="/">Back home</Link></main>; }
