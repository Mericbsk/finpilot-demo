import type { Metadata } from "next";
import { Source_Serif_4, JetBrains_Mono } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const ledgerSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const ledgerMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});


export const metadata: Metadata = {
  title: "FinPilot — Daily Market Reasoning",
  description:
    "A daily market research edition explaining what stood out, why it mattered, and what happened next. Education and research, not investment advice.",
  keywords: [
    "daily market research",
    "market reasoning",
    "financial research",
    "open scorecard",
    "financial education",
    "research methodology",
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
    title: "FinPilot — Daily Market Reasoning",
    description:
      "A daily market research edition explaining what stood out, why it mattered, and what happened next. Education and research, not investment advice.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "FinPilot — Daily Market Reasoning",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "FinPilot — Daily Market Reasoning",
    description:
      "A daily market research edition explaining what stood out, why it mattered, and what happened next. Education and research, not investment advice.",
    images: ["/og-image.png"],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "FinPilot",
  url: "https://finpilot.at",
  description:
    "Daily market research edition explaining what stood out, why it mattered, and what happened next. Education and research, not investment advice.",
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
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${ledgerSerif.variable} ${ledgerMono.variable}`}>
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
