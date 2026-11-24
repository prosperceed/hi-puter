"use client";

import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const theme = resolvedTheme === "dark" ? "dark" : "light";

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark");
  }

  const nextLabel = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  return <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={nextLabel} aria-pressed={theme === "dark"} title={nextLabel}>{theme === "dark" ? <SunIcon /> : <MoonIcon />}</button>;
}

function SunIcon() {
  return <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" /></svg>;
}

function MoonIcon() {
  return <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.3A8.5 8.5 0 0 1 8.7 3.5 8.5 8.5 0 1 0 20.5 15.3Z" /></svg>;
}

