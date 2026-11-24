"use client";

import { useEffect, useSyncExternalStore } from "react";

type Theme = "dark" | "light";

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getTheme, getServerTheme);

  useEffect(() => {
    const saved = window.localStorage.getItem("hi-puter-theme");
    const nextTheme: Theme = saved === "light" || saved === "dark" ? saved : "dark";
    document.documentElement.dataset.theme = nextTheme;
    window.dispatchEvent(new Event("hi-puter-theme-change"));
  }, []);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    window.localStorage.setItem("hi-puter-theme", nextTheme);
    window.dispatchEvent(new Event("hi-puter-theme-change"));
  }

  const nextLabel = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  return <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={nextLabel} title={nextLabel}>{theme === "dark" ? <SunIcon /> : <MoonIcon />}</button>;
}

function SunIcon() {
  return <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" /></svg>;
}

function MoonIcon() {
  return <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.3A8.5 8.5 0 0 1 8.7 3.5 8.5 8.5 0 1 0 20.5 15.3Z" /></svg>;
}

function getTheme(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function getServerTheme(): Theme {
  return "dark";
}

function subscribe(callback: () => void) {
  window.addEventListener("hi-puter-theme-change", callback);
  return () => window.removeEventListener("hi-puter-theme-change", callback);
}
