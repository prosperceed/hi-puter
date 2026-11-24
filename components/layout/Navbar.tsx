"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Menu, X } from "lucide-react";
import { navLinks } from "@/content/site";
import { Wordmark } from "@/components/brand/Wordmark";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function Navbar() {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  return (
    <header className="navbar">
      <div className="nav-inner">
        <Wordmark />
        <nav id="primary-nav" className={open ? "nav-links is-open" : "nav-links"} aria-label="Primary navigation">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href} onClick={close}>
              {link.label}
            </Link>
          ))}
          <span className="desktop-theme-toggle">
            <ThemeToggle />
          </span>
          <Link className="button button-small button-primary nav-cta" href="#install" onClick={close}>
            Install
            <ArrowRight className="icon-trail" size={15} aria-hidden="true" />
          </Link>
        </nav>
        <span className="mobile-theme-toggle">
          <ThemeToggle />
        </span>
        <button
          className="menu-button"
          type="button"
          aria-expanded={open}
          aria-controls="primary-nav"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
        </button>
      </div>
    </header>
  );
}
