import type { Metadata } from "next";
import { Bricolage_Grotesque, Geist_Mono } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({ variable: "--font-display", subsets: ["latin"], display: "swap" });
const mono = Geist_Mono({ variable: "--font-mono", subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL("https://hi-puter.dev"),
  title: { default: "Hi-Puter | Your computer, at your command", template: "%s | Hi-Puter" },
  description: "A local voice assistant for Windows and Linux. Choose a name, say it, and get things done.",
  keywords: ["voice assistant", "Windows", "Linux", "local AI", "terminal"],
  openGraph: { title: "Hi-Puter | Your computer, at your command", description: "A local voice assistant for Windows and Linux.", type: "website", images: ["/opengraph-image"] },
  twitter: { card: "summary_large_image", title: "Hi-Puter", description: "Your computer, at your command." },
  icons: { icon: "/favicon-placeholder.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={`${display.variable} ${mono.variable}`}><body>{children}</body></html>;
}
