"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowLeft,
  Brain,
  BarChart3,
  Activity,
} from "lucide-react";

const sampleStocks = [
  {
    ticker: "NVDA",
    name: "NVIDIA Corp",
    price: 142.5,
    change: +3.2,
    signal: "hold",
    rsi: 78.4,
    macd: "bullish",
    confidence: 82,
    analysis:
      "RSI at 78.4 indicates overbought conditions. However, MACD shows a fresh bullish crossover suggesting underlying momentum remains strong. Historically, NVDA pulls back 3-5% when RSI exceeds 75, but recovers within 2 weeks in an uptrend. Recommendation: Hold current positions, avoid adding. Set re-entry alert at $135.",
  },
  {
    ticker: "AAPL",
    name: "Apple Inc",
    price: 198.7,
    change: -0.8,
    signal: "buy",
    rsi: 42.1,
    macd: "neutral",
    confidence: 74,
    analysis:
      "RSI at 42.1 is approaching oversold territory from a neutral zone. MACD is flat, indicating consolidation after the recent earnings pullback. Volume is declining — typical before a reversal. This pattern historically leads to a 4-7% bounce within 3 weeks. Recommendation: Accumulate small position. Strong support at $192.",
  },
  {
    ticker: "TSLA",
    name: "Tesla Inc",
    price: 178.3,
    change: +5.1,
    signal: "caution",
    rsi: 71.2,
    macd: "bearish_divergence",
    confidence: 61,
    analysis:
      "Price is rising but MACD is forming a bearish divergence — momentum is weakening even as price makes new highs. RSI at 71.2 is elevated but not extreme. This divergence pattern resolved bearishly 68% of the time historically. Recommendation: Tighten stop-loss to $165. Take partial profits if holding. Not a new entry point.",
  },
  {
    ticker: "MSFT",
    name: "Microsoft Corp",
    price: 445.2,
    change: +1.4,
    signal: "buy",
    rsi: 55.3,
    macd: "bullish",
    confidence: 79,
    analysis:
      "Healthy momentum: RSI at 55.3 (neutral-bullish) with a confirmed MACD bullish crossover above the signal line. Price is consolidating above the 50-day MA — a classic continuation pattern. Cloud revenue growth supports fundamental thesis. Recommendation: Good entry point for new positions. Target: $470.",
  },
  {
    ticker: "META",
    name: "Meta Platforms",
    price: 512.8,
    change: -2.3,
    signal: "hold",
    rsi: 48.7,
    macd: "neutral",
    confidence: 68,
    analysis:
      "Mid-range RSI at 48.7 with neutral MACD. The stock is range-bound between $490-$530 for 3 weeks. No clear directional signal. Volume is average. Recommendation: Hold existing positions. Wait for a breakout above $530 or support test at $490 before acting.",
  },
  {
    ticker: "AMZN",
    name: "Amazon.com",
    price: 193.5,
    change: +2.7,
    signal: "buy",
    rsi: 58.9,
    macd: "bullish",
    confidence: 76,
    analysis:
      "RSI at 58.9 with room to run. MACD crossed bullish 3 days ago and accelerating. AWS revenue beat expectations, providing fundamental tailwind. Price broke above the 20-day MA with above-average volume. Recommendation: Buy on any pullback to $188. Stop-loss: $182.",
  },
];

function SignalBadge({ signal }: { signal: string }) {
  const config: Record<string, { color: string; bg: string; label: string }> = {
    buy: { color: "var(--accent-green)", bg: "rgba(48,209,88,0.1)", label: "BUY" },
    sell: { color: "var(--accent-red)", bg: "rgba(255,69,58,0.1)", label: "SELL" },
    hold: { color: "var(--accent-cyan)", bg: "rgba(0,212,255,0.1)", label: "HOLD" },
    caution: { color: "#ffd60a", bg: "rgba(255,214,10,0.1)", label: "CAUTION" },
  };
  const c = config[signal] || config.hold;
  return (
    <span
      className="rounded-full px-3 py-1 text-xs font-bold"
      style={{ color: c.color, backgroundColor: c.bg }}
    >
      {c.label}
    </span>
  );
}

export default function DemoPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const filtered = sampleStocks.filter(
    (s) =>
      s.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stock = sampleStocks.find((s) => s.ticker === selected);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Header */}
      <header className="glass fixed top-0 left-0 right-0 z-50">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <ArrowLeft size={16} />
            Back to Home
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-4 py-1.5 text-xs font-semibold text-black"
          >
            Open Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-blue)]">
              <span className="text-[10px] font-bold text-black">F</span>
            </div>
            <span className="text-sm font-medium text-[var(--text-primary)]">
              FinPilot Demo
            </span>
          </div>
          <Link
            href="/#waitlist"
            className="rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-4 py-1.5 text-xs font-semibold text-black"
          >
            Get Full Access
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 pt-24 pb-16">
        {/* Search */}
        <div className="mb-8">
          <div className="relative mx-auto max-w-md">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]"
            />
            <input
              type="text"
              placeholder="Search stocks... (e.g., NVDA, Apple)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-card)] py-3 pl-11 pr-4 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none focus:border-[var(--accent-cyan)]"
            />
          </div>
        </div>

        {!selected ? (
          <>
            {/* Stock grid */}
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                AI Scanner Results
              </h2>
              <span className="text-xs text-[var(--text-tertiary)]">
                {filtered.length} stocks • Updated 2 min ago
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((s) => (
                <button
                  key={s.ticker}
                  onClick={() => setSelected(s.ticker)}
                  className="group rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5 text-left transition-all hover:border-[var(--border-hover)] hover:bg-[var(--bg-card-hover)]"
                >
                  <div className="mb-3 flex items-start justify-between">
                    <div>
                      <div className="text-base font-semibold text-[var(--text-primary)]">
                        {s.ticker}
                      </div>
                      <div className="text-xs text-[var(--text-tertiary)]">
                        {s.name}
                      </div>
                    </div>
                    <SignalBadge signal={s.signal} />
                  </div>

                  <div className="mb-3 flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-[var(--text-primary)]">
                      ${s.price.toFixed(2)}
                    </span>
                    <span
                      className="flex items-center gap-0.5 text-sm font-medium"
                      style={{
                        color:
                          s.change > 0
                            ? "var(--accent-green)"
                            : s.change < 0
                            ? "var(--accent-red)"
                            : "var(--text-tertiary)",
                      }}
                    >
                      {s.change > 0 ? (
                        <TrendingUp size={14} />
                      ) : s.change < 0 ? (
                        <TrendingDown size={14} />
                      ) : (
                        <Minus size={14} />
                      )}
                      {s.change > 0 ? "+" : ""}
                      {s.change}%
                    </span>
                  </div>

                  {/* Mini indicators */}
                  <div className="flex gap-3">
                    <div className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
                      <Activity size={12} />
                      RSI {s.rsi}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
                      <Brain size={12} />
                      {s.confidence}% conf
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </>
        ) : stock ? (
          /* Detailed analysis view */
          <div>
            <button
              onClick={() => setSelected(null)}
              className="mb-6 flex items-center gap-1 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              <ArrowLeft size={14} />
              Back to Scanner
            </button>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Main analysis */}
              <div className="lg:col-span-2">
                <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-6">
                  <div className="mb-4 flex items-start justify-between">
                    <div>
                      <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                        {stock.ticker}
                      </h1>
                      <p className="text-sm text-[var(--text-tertiary)]">
                        {stock.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-[var(--text-primary)]">
                        ${stock.price.toFixed(2)}
                      </div>
                      <div
                        className="text-sm font-medium"
                        style={{
                          color:
                            stock.change > 0
                              ? "var(--accent-green)"
                              : "var(--accent-red)",
                        }}
                      >
                        {stock.change > 0 ? "+" : ""}
                        {stock.change}%
                      </div>
                    </div>
                  </div>

                  {/* AI Analysis */}
                  <div className="rounded-xl border border-[var(--border-subtle)] bg-[rgba(0,212,255,0.03)] p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <Brain size={18} className="text-[var(--accent-cyan)]" />
                      <h3 className="text-sm font-semibold text-[var(--accent-cyan)]">
                        AI Analysis
                      </h3>
                    </div>
                    <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                      {stock.analysis}
                    </p>
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-4">
                <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5">
                  <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
                    Technical Indicators
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="text-[var(--text-tertiary)]">RSI (14)</span>
                        <span className="font-medium text-[var(--text-primary)]">
                          {stock.rsi}
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-[var(--bg-card-hover)]">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${stock.rsi}%`,
                            backgroundColor:
                              stock.rsi > 70
                                ? "var(--accent-red)"
                                : stock.rsi < 30
                                ? "var(--accent-green)"
                                : "var(--accent-cyan)",
                          }}
                        />
                      </div>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-[var(--text-tertiary)]">MACD</span>
                      <span className="font-medium text-[var(--text-primary)]">
                        {stock.macd.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-[var(--text-tertiary)]">Signal</span>
                      <SignalBadge signal={stock.signal} />
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-[var(--text-tertiary)]">Confidence</span>
                      <span className="font-medium text-[var(--accent-cyan)]">
                        {stock.confidence}%
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-[var(--text-tertiary)]">Model</span>
                      <span className="font-medium text-[var(--text-primary)]">
                        PPO-v3
                      </span>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-[var(--accent-cyan)] bg-[rgba(0,212,255,0.05)] p-5 text-center">
                  <BarChart3
                    size={24}
                    className="mx-auto mb-2 text-[var(--accent-cyan)]"
                  />
                  <p className="mb-3 text-xs text-[var(--text-secondary)]">
                    Want real-time alerts and unlimited analysis?
                  </p>
                  <Link
                    href="/#waitlist"
                    className="inline-block rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-5 py-2 text-xs font-semibold text-black"
                  >
                    Join Waitlist — It&apos;s Free
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
