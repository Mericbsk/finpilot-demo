import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "404 — Page Not Found | FinPilot",
  description: "The page you are looking for does not exist.",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--background)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "var(--font-geist-sans), sans-serif",
        textAlign: "center",
      }}
    >
      <p
        style={{
          fontSize: "0.875rem",
          fontWeight: 600,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--accent-cyan)",
          marginBottom: "1rem",
        }}
      >
        404
      </p>

      <h1
        style={{
          fontSize: "clamp(2rem, 5vw, 3.5rem)",
          fontWeight: 700,
          color: "var(--text-primary)",
          lineHeight: 1.1,
          marginBottom: "1rem",
        }}
      >
        Page not found
      </h1>

      <p
        style={{
          fontSize: "1.125rem",
          color: "var(--text-secondary)",
          maxWidth: "400px",
          marginBottom: "2.5rem",
          lineHeight: 1.6,
        }}
      >
        This page doesn't exist or has been moved.
      </p>

      <Link
        href="/"
        style={{
          display: "inline-block",
          padding: "0.75rem 1.75rem",
          borderRadius: "9999px",
          backgroundColor: "var(--accent-cyan)",
          color: "#000",
          fontWeight: 600,
          fontSize: "0.9375rem",
          textDecoration: "none",
          transition: "opacity 0.2s",
        }}
      >
        Back to home
      </Link>
    </div>
  );
}
