import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Methodology — How FinPilot Works",
  description:
    "How we scan, grade, verify and score — transparently. Education and analysis, not investment advice.",
  robots: { index: true, follow: true },
};

function H2({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-2 mt-10 text-xl font-semibold" style={{ color: "var(--ledger-ink, #1a1a1a)" }}>
      {children}
    </h2>
  );
}

function P({ children }: { children: ReactNode }) {
  return <p className="mb-3" style={{ color: "var(--ledger-ink-soft, #444)" }}>{children}</p>;
}

// Level B — kamuya açık metodoloji iddiası. Tavsiye-dili YOK; "past performance" uyarısı zorunlu.
export default function Methodology() {
  return (
    <main className="ledger">
      <div className="mx-auto max-w-[780px] px-6 py-16 leading-relaxed">
      <h1 className="mb-2 text-3xl font-bold">How FinPilot works</h1>
      <p className="mb-8 text-sm italic" style={{ color: "var(--ledger-ink-soft, #666)" }}>
        Transparency is the product. This page explains how we scan, grade, verify and score —
        and why we show our misses, not just our wins.
      </p>

      <H2>1 · The daily scan</H2>
      <P>Every trading day we scan a broad universe of US equities. A multi-factor engine evaluates
      each name against a strict data contract, with integrity gates that block any signal without
      clear provenance. Market data comes from institutional bar sources with a per-symbol fallback;
      missing or invalid data is skipped — never guessed or filled in.</P>

      <H2>2 · Grading (A / B / C)</H2>
      <P>Only candidates that pass eligibility, executability and position-cap checks receive a single
      Grade (A, B or C) plus a calibrated probability band. We deliberately surface a small,
      high-conviction shortlist — most days that is a handful of names, and some days it is zero.
      &ldquo;No candidate today&rdquo; is a valid, honest outcome.</P>
      <P>A Grade is an <strong>educational conviction label, not a recommendation</strong>. We publish
      research context only: no transaction instructions and no performance claims.</P>

      <H2>3 · Research models</H2>
      <P>Three PPO research models explore momentum, trend and conservative scenarios. They are
      maintained as research artifacts, validated before use, and are not represented as active inputs
      to the current daily Grade.</P>

      <H2>4 · How we verify</H2>
      <P><strong>Locked out-of-sample:</strong> parameters are frozen before evaluation — no hindsight
      fitting. <strong>Triple-barrier resolution:</strong> outcomes are decided by predefined upper,
      lower and time barriers, not naïve returns. <strong>Precision ≠ P&amp;L:</strong> we
      measure expectancy and calibration, not vanity hit-rates.</P>

      <H2>5 · The open scorecard</H2>
      <P>Every published pick is tracked — <strong>including the misses</strong>. We report expectancy
      (the average outcome per pick), not a cherry-picked win-rate. A maturity gate means a pick only
      counts once its barrier window has had time to resolve, so fresh, still-open picks never
      flatter the record.</P>
      <P>A low hit-rate can be by design: positive outcomes can remain open longer than negative
      outcomes, so the average pick can still be positive. See the live scorecard on the{" "}
      <a href="/demo" className="underline">demo page</a>.</P>

      <H2>6 · Education, not advice</H2>
      <P>FinPilot provides education and analysis only — it is not investment advice and not portfolio
      management. Our lessons are generated from cited sources and passed through a
      factual-consistency and compliance check before publishing.</P>

      <p className="mt-10 text-xs" style={{ color: "var(--ledger-ink-soft, #888)" }}>
        Past performance does not guarantee future results. FinPilot is a research and education tool
        and does not provide investment advice.
      </p>
      </div>
    </main>
  );
}
