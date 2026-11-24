"use client";

import Link from "next/link";
import { useState } from "react";
import { navLinks } from "@/content/site";
import { Wordmark } from "@/components/brand/Wordmark";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function Navbar() {
  const [open, setOpen] = useState(false);
  return <header className="navbar"><div className="container nav-inner"><Wordmark /><nav className={open ? "nav-links is-open" : "nav-links"} aria-label="Primary navigation">{navLinks.map((link) => <Link key={link.href} href={link.href} onClick={() => setOpen(false)}>{link.label}</Link>)}<ThemeToggle /><Link className="button button-small button-primary nav-cta" href="#install" onClick={() => setOpen(false)}>Install <span aria-hidden="true">↗</span></Link></nav><button className="menu-button" type="button" aria-expanded={open} aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((value) => !value)}><span className={open ? "menu-glyph close" : "menu-glyph"} aria-hidden="true" /><span className="sr-only">{open ? "Close menu" : "Open menu"}</span></button></div></header>;
}
