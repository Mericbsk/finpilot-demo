"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

/* ── Apple-style typing animation for terminal mockup ── */
const terminalLines = [
  { text: "$ finpilot analyze NVDA", style: "tertiary", delay: 0 },
  { text: "⚡ Analyzing NVIDIA Corp (NVDA)...", style: "cyan", delay: 600 },
  {
    text: "■ RSI: 78.4 (Overbought) — Historically, NVDA pulls back 3-5% within 2 weeks.",
    style: "red-lead",
    delay: 1400,
  },
  {
    text: "■ MACD: Bullish crossover — Underlying trend remains strong despite short-term heat.",
    style: "green-lead",
    delay: 2200,
  },
  {
    text: "→ Hold position. Avoid adding here. Alert set at $118 for re-entry.",
    style: "cyan",
    delay: 3000,
  },
  {
    text: "Confidence: 82% | Model: PPO-v3 | Updated: now",
    style: "tertiary",
    delay: 3600,
  },
];

function TerminalMockup() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const timers = terminalLines.map((line, i) =>
      setTimeout(() => setVisibleCount(i + 1), line.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  const styleMap: Record<string, string> = {
    tertiary: "text-[var(--text-tertiary)]",
    cyan: "text-[var(--accent-cyan)]",
    "red-lead": "text-[var(--text-secondary)]",
    "green-lead": "text-[var(--text-secondary)]",
  };

  return (
    <div className="glow-cyan rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5 sm:p-6">
      {/* Window chrome */}
      <div className="mb-4 flex items-center gap-2">
        <div className="h-2.5 w-2.5 rounded-full bg-[var(--accent-red)]" />
        <div className="h-2.5 w-2.5 rounded-full bg-yellow-500" />
        <div className="h-2.5 w-2.5 rounded-full bg-[var(--accent-green)]" />
        <span className="ml-3 text-[10px] tracking-wider text-[var(--text-tertiary)] uppercase">
          FinPilot AI — NVDA
        </span>
      </div>
      {/* Lines */}
      <div className="min-h-[180px] space-y-2.5 font-mono text-xs sm:text-sm leading-relaxed">
        {terminalLines.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            className={`${styleMap[line.style]} animate-fade-in`}
          >
            {line.style === "red-lead" && (
              <span className="text-[var(--accent-red)]">■ </span>
            )}
            {line.style === "green-lead" && (
              <span className="text-[var(--accent-green)]">■ </span>
            )}
            {line.style === "red-lead" || line.style === "green-lead"
              ? line.text.slice(2)
              : line.text}
          </div>
        ))}
        {visibleCount < terminalLines.length && (
          <span className="inline-block h-4 w-1.5 animate-pulse bg-[var(--accent-cyan)]" />
        )}
      </div>
    </div>
  );
}

/* ── Main Hero ── */
export default function Hero() {
  const sectionRef = useRef<HTMLElement>(null);

  return (
    <section
      ref={sectionRef}
      className="relative flex min-h-[100dvh] flex-col items-center justify-center overflow-hidden px-6"
    >
      {/* Background — subtle radial glow, Apple-style */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/3 h-[800px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent-cyan)] opacity-[0.04] blur-[160px]" />
      </div>

      {/* ── Text Block ── */}
      <div className="relative z-10 mx-auto max-w-4xl text-center">
        {/* Overline */}
        <p className="mb-5 text-sm font-medium uppercase tracking-[0.25em] text-[var(--accent-cyan)] opacity-80">
          Yapay Zeka Borsa Analisti
        </p>

        {/* Headline — Apple gigantic type */}
        <h1 className="mb-6 text-[clamp(2.8rem,8vw,6.5rem)] font-bold leading-[1.05] tracking-tight text-[var(--text-primary)]">
          Piyasayı Anla.
          <br />
          <span className="bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] bg-clip-text text-transparent">
            Kararı Sen Ver.
          </span>
        </h1>

        {/* Subheadline */}
        <p className="mx-auto mb-10 max-w-2xl text-base leading-relaxed text-[var(--text-secondary)] sm:text-lg md:text-xl">
          300+ hissede profesyonel düzey AI analizi, sade dilde.
          <br className="hidden sm:block" />
          Bloomberg&apos;süz, <em>ne</em> oluyor, <em>neden</em> önemli
          ve <em>ne yapmalı</em> — tek ekranda.
        </p>

        {/* CTAs */}
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="#waitlist"
            className="group flex items-center gap-2 rounded-full bg-[var(--accent-cyan)] px-8 py-3.5 text-base font-semibold text-black transition-all hover:shadow-[0_0_40px_var(--glow-cyan)]"
          >
            Ücretsiz Başla
            <ArrowRight
              size={18}
              className="transition-transform group-hover:translate-x-1"
            />
          </Link>
          <Link
            href="/demo"
            className="rounded-full border border-[var(--border-subtle)] px-8 py-3.5 text-base font-medium text-[var(--text-primary)] transition-all hover:border-[var(--border-hover)] hover:bg-[var(--bg-card)]"
          >
            Demo&apos;yu Dene
          </Link>
        </div>
      </div>

      {/* ── Terminal Mockup — scroll-reveal style ── */}
      <div className="relative z-10 mx-auto mt-16 w-full max-w-3xl sm:mt-20">
        <TerminalMockup />
      </div>

      {/* ── Stats strip — Apple "numbers at a glance" ── */}
      <div className="relative z-10 mx-auto mt-16 grid w-full max-w-3xl grid-cols-3 divide-x divide-[var(--border-subtle)]">
        {[
          { value: "300+", label: "Hisse Analizi" },
          { value: "15", label: "AI Model" },
          { value: "3", label: "Dil Desteği" },
        ].map((stat) => (
          <div key={stat.label} className="px-4 py-2 text-center">
            <div className="text-2xl font-bold text-[var(--text-primary)] sm:text-3xl">
              {stat.value}
            </div>
            <div className="mt-0.5 text-xs tracking-wide text-[var(--text-tertiary)] uppercase">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2">
        <div className="h-10 w-5 rounded-full border border-[var(--border-subtle)]">
          <div className="mx-auto mt-1.5 h-2.5 w-1 animate-bounce rounded-full bg-[var(--accent-cyan)]" />
        </div>
      </div>
    </section>
  );
}
