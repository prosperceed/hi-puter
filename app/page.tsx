import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import { Commands } from "@/components/sections/Commands";
import { Faq } from "@/components/sections/Faq";
import { FinalCta } from "@/components/sections/FinalCta";
import { Hero } from "@/components/sections/Hero";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { InstallGuide } from "@/components/sections/InstallGuide";
import { Privacy } from "@/components/sections/Privacy";
import { WakeName } from "@/components/sections/WakeName";
import { WhatItDoes } from "@/components/sections/WhatItDoes";
import { BackgroundField } from "@/components/visuals/BackgroundField";

export default function Home() {
  const structuredData = { "@context": "https://schema.org", "@type": "SoftwareApplication", name: "Hi-Puter", applicationCategory: "UtilitiesApplication", operatingSystem: "Windows, Linux", description: "A local voice assistant for Windows and Linux.", offers: { "@type": "Offer", price: "0", priceCurrency: "USD" } };
  return <><BackgroundField /><Navbar /><main><Hero /><WhatItDoes /><HowItWorks /><Commands /><WakeName /><Privacy /><InstallGuide /><Faq /><FinalCta /></main><Footer /><script type="application/ld+json">{JSON.stringify(structuredData)}</script></>;
}
