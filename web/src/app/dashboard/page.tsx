"use client";

import { useState, useEffect, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Brain,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Target,
  ScanSearch,
  LineChart,
  GraduationCap,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { C, genStockExtended as genStock, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import DemoBanner from "@/components/DemoBanner";

/* ── Signal badge ──────────────────────────────────────────── */
function Signal({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.15)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.15)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.15)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.15)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span style={{ color: c.color, backgroundColor: c.bg, borderRadius: 9999, padding: "2px 10px", fontSize: 10, fontWeight: 700 }}>
      {signal}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? C.green : score >= 50 ? C.cyan : C.red;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full" style={{ backgroundColor: C.cardHover }}>
        <div className="h-1.5 rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-medium" style={{ color }}>{score}</span>
    </div>
  );
}

/* ── Hover card wrapper ────────────────────────────────────── */
function HoverCard({ children, className = "", style = {}, ...rest }: React.ComponentProps<"div">) {
  return (
    <div
      className={className}
      style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, transition: "border-color 0.2s, background-color 0.2s", ...style }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.borderHover; e.currentTarget.style.backgroundColor = C.cardHover; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.backgroundColor = C.card; }}
      {...rest}
    >
      {children}
    </div>
  );
}

/* ── DRL Models (static display) ───────────────────────────── */
const drlModels = [
  { name: "Trend Agent", regime: "📈 Trend", status: "active", accuracy: "73%", trades: 142 },
  { name: "Volatility Agent", regime: "🌊 Volatile", status: "active", accuracy: "68%", trades: 98 },
  { name: "Range Agent", regime: "📐 Range", status: "active", accuracy: "71%", trades: 115 },
];

/* ── Main Page ─────────────────────────────────────────────── */
export default function DashboardOverview() {
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((data: Record<string, { symbols: string[] }>) => {
        const syms = [...new Set(Object.values(data).flatMap((v) => v.symbols))];
        setAllSymbols(syms);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  /* Generate data for all stocks */
  const allStocks = useMemo(() => allSymbols.map(genStock), [allSymbols]);

  /* Top 4 by score */
  const topOppsBase = useMemo(
    () => [...allStocks].sort((a, b) => b.score - a.score).slice(0, 4),
    [allStocks],
  );

  /* Recent signals: top 8 BUY/SELL signals by score */
  const recentSigsBase = useMemo(() => {
    const signalStocks = allStocks.filter((s) => s.signal === "BUY" || s.signal === "SELL");
    const sorted = [...signalStocks].sort((a, b) => b.score - a.score).slice(0, 8);
    const times = ["14:32", "14:28", "14:15", "13:58", "13:42", "13:30", "13:18", "13:05"];
    return sorted.map((s, i) => ({ ...s, time: times[i % times.length] }));
  }, [allStocks]);

  /* Live prices for displayed tickers */
  const liveTickers = useMemo(
    () => [...new Set([...topOppsBase, ...recentSigsBase].map((s) => s.ticker))],
    [topOppsBase, recentSigsBase],
  );
  const { data: live } = useStockPrices(liveTickers);

  const topOpportunities = useMemo(
    () => topOppsBase.map((s) => withLivePrice(s, live[s.ticker])),
    [topOppsBase, live],
  );
  const recentSignals = useMemo(
    () => recentSigsBase.map((s) => withLivePrice(s, live[s.ticker])),
    [recentSigsBase, live],
  );

  /* Market Pulse computed */
  const marketPulse = useMemo(() => {
    if (allStocks.length === 0) return [];
    const buyCount = allStocks.filter((s) => s.signal === "BUY").length;
    const avgScore = (allStocks.reduce((a, s) => a + s.score, 0) / allStocks.length).toFixed(1);
    const buyPct = ((buyCount / allStocks.length) * 100).toFixed(0);
    const regime = +buyPct >= 60 ? "Bullish" : +buyPct >= 40 ? "Neutral" : "Bearish";
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
    return [
      { label: "Market Regime", value: regime, change: `${buyPct}% buy`, up: +buyPct >= 50, icon: TrendingUp },
      { label: "Avg Score", value: avgScore, change: `${allStocks.length} stocks`, up: +avgScore >= 55, icon: BarChart3 },
      { label: "Buy Signals", value: buyCount.toString(), change: `of ${allStocks.length}`, up: true, icon: Zap },
      { label: "Last Update", value: timeStr, change: "live", up: true, icon: Clock },
    ];
  }, [allStocks]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 size={32} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <DemoBanner />
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>Dashboard</h1>
        <p className="text-sm" style={{ color: C.text3 }}>
          {allSymbols.length.toLocaleString()} stocks · Market overview & AI insights
        </p>
      </div>

      {/* Market Pulse */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {marketPulse.map((m) => (
          <HoverCard key={m.label} className="rounded-2xl p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs" style={{ color: C.text3 }}>{m.label}</span>
              <m.icon size={14} style={{ color: C.text3 }} />
            </div>
            <div className="text-lg font-semibold" style={{ color: C.text1 }}>{m.value}</div>
            {m.change && (
              <div className="mt-1 flex items-center gap-1 text-xs" style={{ color: m.up ? C.green : C.red }}>
                {m.up ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {m.change}
              </div>
            )}
          </HoverCard>
        ))}
      </div>

      {/* Top Opportunities */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>
            Top Opportunities
            <span className="ml-2 font-normal" style={{ color: C.text3, fontSize: 11 }}>by AI Score</span>
          </h2>
          <Link href="/dashboard/scanner" className="text-xs hover:underline" style={{ color: C.cyan }}>
            View All →
          </Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {topOpportunities.map((s) => (
            <Link
              key={s.ticker}
              href={`/dashboard/analysis?symbol=${s.ticker}`}
              className="group rounded-2xl p-4"
              style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, transition: "border-color 0.2s, background-color 0.2s" }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.borderHover; e.currentTarget.style.backgroundColor = C.cardHover; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.backgroundColor = C.card; }}
            >
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <div className="text-sm font-semibold" style={{ color: C.text1 }}>{s.ticker}</div>
                  <div style={{ fontSize: 11, color: C.text3 }}>Score {s.score}/100</div>
                </div>
                <Signal signal={s.signal} />
              </div>
              <div className="mb-2 flex items-baseline gap-2">
                <span className="text-lg font-bold" style={{ color: C.text1 }}>${s.price}</span>
                <span className="text-xs font-medium" style={{ color: s.change >= 0 ? C.green : C.red }}>
                  {s.change >= 0 ? "+" : ""}{s.change}%
                </span>
              </div>
              <ScoreBar score={s.score} />
              <div className="mt-3 grid grid-cols-2 gap-2" style={{ fontSize: 10 }}>
                <div className="rounded-lg px-2 py-1" style={{ backgroundColor: C.primary }}>
                  <span style={{ color: C.text3 }}>Target</span>
                  <div className="font-medium" style={{ color: C.green }}>${s.target}</div>
                </div>
                <div className="rounded-lg px-2 py-1" style={{ backgroundColor: C.primary }}>
                  <span style={{ color: C.text3 }}>Stop</span>
                  <div className="font-medium" style={{ color: C.red }}>${s.stop}</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Two-column: Recent Signals + DRL Models */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Recent signals */}
        <div className="lg:col-span-3 rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>
              Recent Signals
              <span className="ml-2 font-normal" style={{ color: C.text3, fontSize: 11 }}>top {recentSignals.length} active</span>
            </h2>
            <Link href="/dashboard/history" className="text-xs hover:underline" style={{ color: C.cyan }}>
              View History →
            </Link>
          </div>
          <div className="space-y-2">
            {recentSignals.map((s, i) => (
              <Link
                key={i}
                href={`/dashboard/analysis?symbol=${s.ticker}`}
                className="flex items-center justify-between rounded-xl px-4 py-2.5"
                style={{ backgroundColor: C.primary, transition: "background-color 0.15s" }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = C.cardHover; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = C.primary; }}
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold" style={{ color: C.text1 }}>{s.ticker}</span>
                  <Signal signal={s.signal} />
                </div>
                <div className="flex items-center gap-4">
                  <ScoreBar score={s.score} />
                  <span className="rounded-md px-2 py-0.5" style={{ fontSize: 10, backgroundColor: C.card, color: C.text3 }}>{s.regime}</span>
                  <span style={{ fontSize: 10, color: C.text3 }}>{s.time}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* DRL Model Status */}
        <div className="lg:col-span-2 rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div className="mb-4 flex items-center gap-2">
            <Brain size={16} style={{ color: C.cyan }} />
            <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>DRL Agents</h2>
          </div>
          <div className="space-y-3">
            {drlModels.map((m) => (
              <div key={m.name} className="rounded-xl p-3" style={{ backgroundColor: C.primary }}>
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs">{m.regime}</span>
                    <span className="text-xs font-medium" style={{ color: C.text1 }}>{m.name}</span>
                  </div>
                  <span style={{ borderRadius: 9999, backgroundColor: "rgba(48,209,88,0.15)", padding: "2px 8px", fontSize: 10, fontWeight: 500, color: C.green }}>
                    {m.status}
                  </span>
                </div>
                <div className="flex gap-4" style={{ fontSize: 10, color: C.text3 }}>
                  <span>Accuracy: <strong style={{ color: C.text2 }}>{m.accuracy}</strong></span>
                  <span>Trades: <strong style={{ color: C.text2 }}>{m.trades}</strong></span>
                </div>
              </div>
            ))}
          </div>
          <Link
            href="/dashboard/ai-lab"
            className="mt-3 flex items-center justify-center gap-1 rounded-xl py-2 text-xs"
            style={{ backgroundColor: C.primary, color: C.cyan }}
          >
            <Activity size={12} />
            Open AI Lab
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Run Scan", icon: ScanSearch, href: "/dashboard/scanner", color: C.cyan },
          { label: "Backtest", icon: LineChart, href: "/dashboard/backtest", color: C.blue },
          { label: "FinSense", icon: GraduationCap, href: "/dashboard/finsense", color: "#a78bfa" },
          { label: "Watchlist", icon: Target, href: "/dashboard/watchlist", color: C.green },
        ].map((a) => (
          <Link
            key={a.label}
            href={a.href}
            className="flex items-center gap-3 rounded-2xl p-4"
            style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, transition: "border-color 0.2s, background-color 0.2s" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.borderHover; e.currentTarget.style.backgroundColor = C.cardHover; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.backgroundColor = C.card; }}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ backgroundColor: `${a.color}15` }}>
              <a.icon size={18} style={{ color: a.color }} />
            </div>
            <span className="text-sm font-medium" style={{ color: C.text1 }}>{a.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
