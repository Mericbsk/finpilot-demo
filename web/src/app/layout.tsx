import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinPilot — AI-Powered Stock Intelligence",
  description:
    "Scans 1,500+ stocks daily with 12 trained reinforcement learning models. Clear buy/hold/sell signals, built-in risk management, and walk-forward backtesting. Not an LLM wrapper — real AI.",
  keywords: [
    "stock scanner",
    "AI trading",
    "reinforcement learning",
    "DRL",
    "risk management",
    "fintech",
    "backtest",
    "ensemble voting",
    "stock analysis",
    "AI stock picks",
    "algorithmic trading",
  ],
  metadataBase: new URL("https://finpilot.at"),
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-snippet": -1,
      "max-image-preview": "large",
      "max-video-preview": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://finpilot.at",
    siteName: "FinPilot",
    title: "FinPilot — AI-Powered Stock Intelligence",
    description:
      "Scans 1,500+ stocks daily with 12 trained reinforcement learning models. Clear buy/hold/sell signals, built-in risk management, and walk-forward backtesting.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "FinPilot — AI-Powered Stock Intelligence",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "FinPilot — AI-Powered Stock Intelligence",
    description:
      "Scans 1,500+ stocks daily with 12 trained reinforcement learning models. Clear buy/hold/sell signals, built-in risk management.",
    images: ["/og-image.png"],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "FinPilot",
  url: "https://finpilot.at",
  description:
    "AI-powered stock scanner that analyzes 1,500+ stocks daily using 12 trained reinforcement learning models.",
  applicationCategory: "FinanceApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "EUR",
  },
  author: {
    "@type": "Organization",
    name: "FinPilot",
    url: "https://finpilot.at",
    address: {
      "@type": "PostalAddress",
      addressLocality: "Vienna",
      addressCountry: "AT",
    },
  },
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.8",
    ratingCount: "120",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        {process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN && (
          <script
            defer
            data-domain={process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN}
            src="https://plausible.io/js/script.js"
          />
        )}
      </head>
      <body className="font-sans antialiased">
        {children}
        <Toaster
          theme="dark"
          position="bottom-right"
          richColors
          toastOptions={{
            style: {
              background: "rgba(17,17,24,0.95)",
              border: "1px solid rgba(255,255,255,0.12)",
              backdropFilter: "blur(20px)",
              color: "#f5f5f7",
            },
          }}
        />
      </body>
    </html>
  );
}
