import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap { return [{ url: "https://hi-puter.dev", lastModified: new Date("2026-11-24"), changeFrequency: "monthly", priority: 1 }]; }
