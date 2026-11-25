import Link from "next/link";
import { Mark } from "@/components/brand/Mark";

export function Wordmark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="wordmark" aria-label="Hi-Puter home">
      <Mark />
      <span>Hi-Puter</span>
    </Link>
  );
}
