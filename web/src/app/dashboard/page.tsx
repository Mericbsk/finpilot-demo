"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
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
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { C, companyNames } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import { getCurrencySymbol } from "@/lib/userSettings";
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

/* ── DRL Models (loaded from API) ───────────────────────────── */
interface DRLModelDisplay {
  name: string;
  regime: string;
  status: string;
  algorithm: string;
  sharpe: string;
  totalReturn: string;
}

interface ScanResult {
  ticker: string;
  name: string;
  price: number;
  change: number;
  score: number;
  signal: string;
  regime?: string;
  target?: number;
  stop?: number;
}

/* ── Main Page ─────────────────────────────────────────────── */
export default function DashboardOverview() {
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanResults, setScanResults] = useState<ScanResult[]>([]);
  const [scanLoading, setScanLoading] = useState(false);
  const [drlModels, setDrlModels] = useState<DRLModelDisplay[]>([]);
  const [currency, setCurrency] = useState("$");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("finpilot_settings");
      if (stored) setCurrency(getCurrencySymbol(JSON.parse(stored).market || "US"));
    } catch {}
  }, []);

  /* Load presets */
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

  /* Load DRL models from API */
  useEffect(() => {
    fetch("/py-api/models")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          const regimeEmoji: Record<string, string> = { trend: "📈", volatile: "🌊", range: "📐", momentum: "🚀", breakout: "💥" };
          const activeModels = (data as Record<string, unknown>[]).filter((m) => m.is_active !== false);
          setDrlModels(
            activeModels.slice(0, 6).map((m: Record<string, unknown>) => {
              const metrics = (m.metrics ?? {}) as Record<string, unknown>;
              const sharpeRaw = metrics.sharpe_ratio;
              const returnRaw = metrics.total_return;
              return {
                name: String(m.name || m.model_id || "Agent"),
                regime: (Array.isArray(m.tags) ? m.tags : []).map((t: string) => `${regimeEmoji[t] || "🔧"} ${t}`).join(", ") || "General",
                status: String(m.is_active ? "active" : "paused"),
                algorithm: String(m.algorithm || "PPO"),
                sharpe: sharpeRaw != null ? Number(sharpeRaw).toFixed(3) : "—",
                totalReturn: returnRaw != null ? `${Number(returnRaw) >= 0 ? "+" : ""}${(Number(returnRaw) * 100).toFixed(1)}%` : "—",
              };
            }),
          );
        }
      })
      .catch(() => {});
  }, []);

  /* Scan top symbols for real data */
  const runQuickScan = useCallback(async (symbols: string[]) => {
    if (symbols.length === 0) return;
    setScanLoading(true);
    try {
      const batch = symbols.slice(0, 30);
      const res = await fetch("/py-api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: batch }),
      });
      if (!res.ok) return;
      const data = await res.json();
      const results: ScanResult[] = Object.entries(data).map(([ticker, d]: [string, unknown]) => {
        const r = d as Record<string, unknown>;
        const score = Math.max(Number(r.filter_score ?? 0), Number(r.score ?? 0));
        const normalized = r.composite_score != null
          ? Number(r.composite_score)
          : Math.round((score / 4) * 100);
        const signal = normalized >= 70 ? "BUY" : normalized >= 45 ? "HOLD" : normalized >= 25 ? "CAUTION" : "SELL";
        return {
          ticker,
          name: companyNames[ticker] || ticker,
          price: 0,
          change: 0,
          score: normalized,
          signal,
          regime: String(r.regime || "—"),
          target: 0,
          stop: 0,
        };
      });
      setScanResults(results);
    } catch { /* silent */ }
    finally { setScanLoading(false); }
  }, []);

  useEffect(() => {
    if (allSymbols.length > 0) runQuickScan(allSymbols);
  }, [allSymbols, runQuickScan]);

  /* Top 4 by score */
  const topOppsBase = useMemo(
    () => [...scanResults].sort((a, b) => b.score - a.score).slice(0, 4),
    [scanResults],
  );

  /* Recent signals: top 8 BUY/SELL by score */
  const recentSigsBase = useMemo(() => {
    const signalStocks = scanResults.filter((s) => s.signal === "BUY" || s.signal === "SELL");
    return [...signalStocks].sort((a, b) => b.score - a.score).slice(0, 8);
  }, [scanResults]);

  /* Live prices for displayed tickers */
  const liveTickers = useMemo(
    () => [...new Set([...topOppsBase, ...recentSigsBase].map((s) => s.ticker))],
    [topOppsBase, recentSigsBase],
  );
  const { data: live } = useStockPrices(liveTickers);

  const topOpportunities = useMemo(
    () => topOppsBase.map((s) => ({
      ...s,
      price: live[s.ticker]?.price ?? s.price,
      change: live[s.ticker]?.change ?? s.change,
    })),
    [topOppsBase, live],
  );
  const recentSignals = useMemo(
    () => recentSigsBase.map((s) => ({
      ...s,
      price: live[s.ticker]?.price ?? s.price,
      change: live[s.ticker]?.change ?? s.change,
    })),
    [recentSigsBase, live],
  );

  /* Market Pulse computed from real scan results */
  const marketPulse = useMemo(() => {
    const stocks = scanResults.length > 0 ? scanResults : [];
    if (stocks.length === 0) return [];
    const buyCount = stocks.filter((s) => s.signal === "BUY").length;
    const avgScore = (stocks.reduce((a, s) => a + s.score, 0) / stocks.length).toFixed(1);
    const buyPct = ((buyCount / stocks.length) * 100).toFixed(0);
    const regime = +buyPct >= 60 ? "Bullish" : +buyPct >= 40 ? "Neutral" : "Bearish";
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
    return [
      { label: "Market Regime", value: regime, change: `${buyPct}% buy`, up: +buyPct >= 50, icon: TrendingUp },
      { label: "Avg Score", value: avgScore, change: `${stocks.length} stocks`, up: +avgScore >= 55, icon: BarChart3 },
      { label: "Buy Signals", value: buyCount.toString(), change: `of ${stocks.length}`, up: true, icon: Zap },
      { label: "Last Update", value: timeStr, change: "live", up: true, icon: Clock },
    ];
  }, [scanResults]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 size={32} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <DemoBanner connected={Object.keys(live).length > 0} />
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>Dashboard</h1>
        <p className="text-sm" style={{ color: C.text3 }}>
          {allSymbols.length.toLocaleString()} stocks · Market overview & AI insights
          {scanLoading && <span className="ml-2"><Loader2 size={12} className="inline animate-spin" /> Scanning...</span>}
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
                <span className="text-lg font-bold" style={{ color: C.text1 }}>
                  {s.price > 0 ? `${currency}${s.price.toFixed(2)}` : "—"}
                </span>
                <span className="text-xs font-medium" style={{ color: s.change >= 0 ? C.green : C.red }}>
                  {s.change !== 0 ? `${s.change >= 0 ? "+" : ""}${s.change.toFixed(2)}%` : ""}
                </span>
              </div>
              <ScoreBar score={s.score} />
              <div className="mt-3 grid grid-cols-2 gap-2" style={{ fontSize: 10 }}>
                <div className="rounded-lg px-2 py-1" style={{ backgroundColor: C.primary }}>
                  <span style={{ color: C.text3 }}>Score</span>
                  <div className="font-medium" style={{ color: C.green }}>{s.score}/100</div>
                </div>
                <div className="rounded-lg px-2 py-1" style={{ backgroundColor: C.primary }}>
                  <span style={{ color: C.text3 }}>Regime</span>
                  <div className="font-medium" style={{ color: C.cyan }}>{s.regime || "—"}</div>
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
                  <span className="rounded-md px-2 py-0.5" style={{ fontSize: 10, backgroundColor: C.card, color: C.text3 }}>{s.regime || "—"}</span>
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
            {drlModels.length > 0 ? drlModels.map((m) => (
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
                  <span>Algorithm: <strong style={{ color: C.text2 }}>{m.algorithm}</strong></span>
                  <span>Sharpe: <strong style={{ color: C.text2 }}>{m.sharpe}</strong></span>
                  {m.totalReturn !== "—" && (
                    <span title="Backtest result – not live performance">Return: <strong style={{ color: C.text2 }}>{m.totalReturn} <span style={{ color: C.text3, fontWeight: 400 }}>(bt)</span></strong></span>
                  )}
                </div>
              </div>
            )) : (
              <div className="flex flex-col items-center gap-2 py-6" style={{ color: C.text3 }}>
                <Brain size={24} />
                <span className="text-xs">No DRL models registered</span>
              </div>
            )}
          </div>
          <Link
            href="/dashboard/drl"
            className="mt-3 flex items-center justify-center gap-1 rounded-xl py-2 text-xs"
            style={{ backgroundColor: C.primary, color: C.cyan }}
          >
            <Activity size={12} />
            Open DRL Agents
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
