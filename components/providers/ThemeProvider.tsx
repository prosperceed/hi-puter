"use client";

import { ThemeProvider as NextThemeProvider } from "next-themes";
import type { ReactNode } from "react";
import { themeStorageKey } from "@/lib/theme";

export function ThemeProvider({ children }: { children: ReactNode }) {
  return <NextThemeProvider attribute="class" storageKey={themeStorageKey} defaultTheme="dark" enableSystem={false} disableTransitionOnChange>{children}</NextThemeProvider>;
}
