"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

/**
 * The server cannot know the stored theme, so the markup is identical in both
 * themes and CSS (`.dark`) decides which icon is visible. This avoids a
 * hydration mismatch when the page loads in dark mode.
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      aria-label="Toggle dark mode"
      title="Toggle dark mode"
    >
      <Moon className="theme-icon-moon" size={16} aria-hidden="true" />
      <Sun className="theme-icon-sun" size={16} aria-hidden="true" />
    </button>
  );
}
