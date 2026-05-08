"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft, Search, Heart, Star, ChevronRight,
  Shield, BarChart3, Brain, Zap, Check, Clock, TrendingUp, TrendingDown,
} from "lucide-react";
import StockChart from "@/components/dashboard/StockChart";
import { C } from "@/lib/stockData";

/* ─── Types ──────────────────────────────────────────────────── */
interface RawStock {
  symbol: string;
  price: number;
  score: number;
  filter_score: number;
  composite_score?: number;
  regime: boolean;
  direction: boolean;
  entry_ok: boolean;
  high_quality_signal: boolean;
  trend_strength: boolean;
  volume_spike: boolean;
  price_momentum: boolean;
  momentum_bias: string;
  momentum_3d_pct: number;
  momentum_best_return_pct: number;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  position_size: number;
  stop_loss_percent: number;
  kelly_fraction: number;
  atr: number;
  ema_gap_pct: number;
  alignment_ratio: number;
  timeframe_aligned: boolean;
  momentum_confluence: boolean;
  timestamp: string;
}

interface DemoStock {
  ticker: string;
  price: number;
  score: number;
  signal: "BUY" | "HOLD" | "CAUTION" | "SELL";
  regime: string;
  sentiment: string;
  rr: number;
  stop: number;
  tp: number;
  entryOk: boolean;
  highQuality: boolean;
  trendStrength: boolean;
  volumeSpike: boolean;
  momentum: string;
  momentum3d: number;
  atr: number;
  positionSize: number;
  kelly: number;
  emaGap: number;
  aligned: boolean;
  confluence: boolean;
  stopPct: number;
}

/* ─── Helpers ────────────────────────────────────────────────── */
function parseBool(v: unknown): boolean {
  return v === true || v === "True" || v === "true" || v === 1;
}

function rawToDemo(r: RawStock): DemoStock {
  const filterScore = r.filter_score ?? r.score ?? 0;
  const score =
    r.composite_score != null
      ? Math.round(r.composite_score)
      : Math.round((Math.min(filterScore, 4) / 4) * 100);

  const hq = parseBool(r.high_quality_signal);
  const eo = parseBool(r.entry_ok);
  const signal: DemoStock["signal"] =
    hq || eo ? "BUY" : filterScore >= 3 ? "HOLD" : filterScore >= 2 ? "CAUTION" : "SELL";

  const regime = parseBool(r.regime)
    ? parseBool(r.trend_strength) ? "Trend" : "Range"
    : "Volatile";

  return {
    ticker: r.symbol,
    price: r.price,
    score,
    signal,
    regime,
    sentiment:
      r.momentum_bias === "bullish"
        ? "Bullish"
        : r.momentum_bias === "bearish"
        ? "Bearish"
        : "Neutral",
    rr: r.risk_reward ?? 0,
    stop: r.stop_loss ?? 0,
    tp: r.take_profit ?? 0,
    entryOk: eo,
    highQuality: hq,
    trendStrength: parseBool(r.trend_strength),
    volumeSpike: parseBool(r.volume_spike),
    momentum: r.momentum_bias ?? "neutral",
    momentum3d: r.momentum_3d_pct ?? 0,
    atr: r.atr ?? 0,
    positionSize: r.position_size ?? 0,
    kelly: r.kelly_fraction ?? 0,
    emaGap: r.ema_gap_pct ?? 0,
    aligned: parseBool(r.timeframe_aligned),
    confluence: parseBool(r.momentum_confluence),
    stopPct: r.stop_loss_percent ?? 0,
  };
}

function generateWhySignal(s: DemoStock): string {
  const parts: string[] = [];
  if (s.highQuality) parts.push("High-quality signal confirmed across multiple model layers.");
  if (s.trendStrength && s.regime === "Trend")
    parts.push(`Strong trend in ${s.regime} regime — EMA gap ${s.emaGap > 0 ? "+" : ""}${s.emaGap.toFixed(1)}%.`);
  if (s.volumeSpike) parts.push("Unusual volume spike detected — potential institutional activity.");
  if (s.momentum !== "neutral")
    parts.push(`3-day momentum is ${s.momentum} (${s.momentum3d > 0 ? "+" : ""}${s.momentum3d.toFixed(1)}%).`);
  if (s.aligned) parts.push("Multi-timeframe alignment confirmed across 15m, 1h, and 4h intervals.");
  if (s.confluence) parts.push("Momentum confluence active — indicators align directionally.");
  if (s.rr > 0) parts.push(`Risk/reward: ${s.rr.toFixed(1)}x with ${s.stopPct.toFixed(1)}% stop distance.`);
  if (parts.length === 0)
    parts.push("Signal based on composite technical analysis across trend, volume, and momentum factors.");
  return parts.join(" ");
}

function generateEnsemble(s: DemoStock) {
  const g = C.green, r = C.red, t = C.text3;
  if (s.signal === "BUY" && s.highQuality)
    return [
      { name: "Trend Agent",      vote: "BUY",  conf: Math.min(95, 80 + Math.floor(s.score * 0.12)), color: g },
      { name: "Range Agent",      vote: s.regime === "Range" ? "BUY" : "HOLD", conf: 65, color: s.regime === "Range" ? g : t },
      { name: "Volatility Agent", vote: "BUY",  conf: 74, color: g },
    ];
  if (s.signal === "SELL")
    return [
      { name: "Trend Agent",      vote: "SELL", conf: 78, color: r },
      { name: "Range Agent",      vote: "HOLD", conf: 54, color: t },
      { name: "Volatility Agent", vote: "SELL", conf: 71, color: r },
    ];
  return [
    { name: "Trend Agent",      vote: "HOLD", conf: 62, color: t },
    { name: "Range Agent",      vote: "HOLD", conf: 68, color: t },
    { name: "Volatility Agent", vote: s.momentum === "bullish" ? "BUY" : "HOLD", conf: 57, color: s.momentum === "bullish" ? g : t },
  ];
}

const SIGNAL_COLOR: Record<string, string> = {
  BUY: C.green, HOLD: C.cyan, CAUTION: "#ffd60a", SELL: C.red,
};

const STATIC_FALLBACK: DemoStock[] = [
  { ticker: "NVDA", price: 142.5, score: 82, signal: "BUY",  regime: "Trend",    sentiment: "Bullish", rr: 1.8, stop: 128.0, tp: 162.0, entryOk: true,  highQuality: true,  trendStrength: true,  volumeSpike: true,  momentum: "bullish", momentum3d: 3.2,  atr: 4.2,  positionSize: 1000, kelly: 0.5, emaGap: 12.3, aligned: true,  confluence: true,  stopPct: 10.2 },
  { ticker: "AAPL", price: 198.7, score: 68, signal: "BUY",  regime: "Range",    sentiment: "Neutral", rr: 1.6, stop: 188.0, tp: 215.0, entryOk: true,  highQuality: false, trendStrength: false, volumeSpike: false, momentum: "neutral", momentum3d: -0.8, atr: 3.1,  positionSize: 1000, kelly: 0.5, emaGap: 2.1,  aligned: false, confluence: false, stopPct: 5.4 },
  { ticker: "MSFT", price: 445.2, score: 74, signal: "BUY",  regime: "Trend",    sentiment: "Bullish", rr: 2.1, stop: 420.0, tp: 493.0, entryOk: true,  highQuality: true,  trendStrength: true,  volumeSpike: false, momentum: "bullish", momentum3d: 1.4,  atr: 7.8,  positionSize: 1000, kelly: 0.5, emaGap: 8.6,  aligned: true,  confluence: true,  stopPct: 5.7 },
  { ticker: "TSLA", price: 178.3, score: 38, signal: "SELL", regime: "Volatile", sentiment: "Bearish", rr: 2.1, stop: 195.0, tp: 145.0, entryOk: false, highQuality: false, trendStrength: false, volumeSpike: false, momentum: "bearish", momentum3d: -4.1, atr: 8.9,  positionSize: 1000, kelly: 0.5, emaGap: -6.2, aligned: false, confluence: false, stopPct: 9.4 },
  { ticker: "META", price: 512.8, score: 62, signal: "HOLD", regime: "Range",    sentiment: "Neutral", rr: 1.4, stop: 488.0, tp: 546.0, entryOk: false, highQuality: false, trendStrength: false, volumeSpike: false, momentum: "neutral", momentum3d: 0.3,  atr: 9.2,  positionSize: 1000, kelly: 0.5, emaGap: 1.5,  aligned: false, confluence: false, stopPct: 4.8 },
  { ticker: "AMZN", price: 193.5, score: 71, signal: "BUY",  regime: "Trend",    sentiment: "Bullish", rr: 1.9, stop: 182.0, tp: 213.0, entryOk: true,  highQuality: false, trendStrength: true,  volumeSpike: true,  momentum: "bullish", momentum3d: 2.1,  atr: 4.6,  positionSize: 1000, kelly: 0.5, emaGap: 7.4,  aligned: true,  confluence: false, stopPct: 6.0 },
];

/* ─── Sub-components ─────────────────────────────────────────── */
function ScoreBadge({ score }: { score: number }) {
  const color = score >= 70 ? C.green : score >= 45 ? C.cyan : C.red;
  return (
    <span
      style={{
        display: "inline-block",
        minWidth: 36,
        padding: "2px 8px",
        borderRadius: 99,
        background: `${color}22`,
        color,
        fontSize: 11,
        fontWeight: 700,
        textAlign: "center",
      }}
    >
      {score}
    </span>
  );
}

function SignalBadge({ signal }: { signal: string }) {
  const color = SIGNAL_COLOR[signal] ?? C.text3;
  return (
    <span
      style={{
        padding: "2px 10px",
        borderRadius: 99,
        background: `${color}22`,
        color,
        fontSize: 11,
        fontWeight: 700,
      }}
    >
      {signal}
    </span>
  );
}

function FeedbackWidget({ ticker }: { ticker?: string }) {
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!rating) return;
    setLoading(true);
    try {
      await fetch("/py-api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comment, page: "demo", ticker: ticker ?? null }),
      });
    } catch {
      // best effort
    }
    setSubmitted(true);
    setLoading(false);
  }

  if (submitted)
    return (
      <div
        style={{
          background: `${C.green}15`,
          border: `1px solid ${C.green}30`,
          borderRadius: 12,
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <Check size={16} color={C.green} />
        <span style={{ color: C.green, fontSize: 13, fontWeight: 600 }}>
          Thank you for your feedback!
        </span>
      </div>
    );

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 14,
        padding: "20px 22px",
      }}
    >
      <p style={{ color: C.text2, fontSize: 12, marginBottom: 10, fontWeight: 600 }}>
        How useful was this demo?
      </p>
      <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            onClick={() => setRating(n)}
            onMouseEnter={() => setHovered(n)}
            onMouseLeave={() => setHovered(0)}
            style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}
          >
            <Star
              size={22}
              fill={(hovered || rating) >= n ? "#ffd60a" : "transparent"}
              color={(hovered || rating) >= n ? "#ffd60a" : C.text3}
            />
          </button>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Optional: what would make this more useful?"
        rows={2}
        style={{
          width: "100%",
          background: "rgba(255,255,255,0.04)",
          border: `1px solid ${C.border}`,
          borderRadius: 8,
          color: C.text1,
          fontSize: 12,
          padding: "8px 10px",
          resize: "none",
          outline: "none",
          marginBottom: 10,
          boxSizing: "border-box",
        }}
      />
      <button
        onClick={handleSubmit}
        disabled={!rating || loading}
        style={{
          background: rating ? C.blue : "rgba(255,255,255,0.06)",
          color: rating ? "#fff" : C.text3,
          border: "none",
          borderRadius: 8,
          padding: "8px 18px",
          fontSize: 12,
          fontWeight: 600,
          cursor: rating ? "pointer" : "not-allowed",
          transition: "all .2s",
        }}
      >
        {loading ? "Sending…" : "Submit Feedback"}
      </button>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────────── */
export default function DemoPage() {
  const [stocks, setStocks] = useState<DemoStock[]>([]);
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set());
  const [chartInterval, setChartInterval] = useState<"1d" | "1h" | "4h">("1d");

  /* Load watchlist from localStorage */
  useEffect(() => {
    try {
      const saved = localStorage.getItem("demo_watchlist");
      if (saved) setWatchlist(new Set(JSON.parse(saved)));
    } catch {}
  }, []);

  const toggleWatchlist = useCallback((ticker: string) => {
    setWatchlist((prev) => {
      const next = new Set(prev);
      next.has(ticker) ? next.delete(ticker) : next.add(ticker);
      try { localStorage.setItem("demo_watchlist", JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  /* Fetch shortlist */
  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetch("/py-api/scan/shortlist/latest?limit=30");
        if (res.ok) {
          const data = await res.json();
          if (data.stocks?.length) {
            setStocks(data.stocks.map((r: RawStock) => rawToDemo(r)));
            setTimestamp(data.timestamp);
            setIsLive(true);
            setLoading(false);
            return;
          }
        }
      } catch {}
      setStocks(STATIC_FALLBACK);
      setTimestamp(null);
      setIsLive(false);
      setLoading(false);
    }
    load();
  }, []);

  const filtered = stocks.filter((s) =>
    s.ticker.toLowerCase().includes(search.toLowerCase())
  );

  const selectedStock = stocks.find((s) => s.ticker === selected);
  const ensemble = selectedStock ? generateEnsemble(selectedStock) : [];
  const whySig = selectedStock ? generateWhySignal(selectedStock) : "";

  /* ── Timestamp display ── */
  function formatTimestamp(iso: string | null): string {
    if (!iso) return "Demo data";
    try {
      const d = new Date(iso);
      const now = new Date();
      const diffH = Math.round((now.getTime() - d.getTime()) / 3600000);
      if (diffH < 1) return "Less than 1h ago";
      if (diffH < 24) return `${diffH}h ago`;
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch { return "Recent"; }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#09090f", color: C.text1 }}>

      {/* ── Header ── */}
      <header
        style={{
          position: "fixed",
          top: 0, left: 0, right: 0,
          zIndex: 50,
          background: "rgba(9,9,15,0.92)",
          backdropFilter: "blur(20px)",
          borderBottom: `1px solid ${C.border}`,
          height: 52,
          display: "flex",
          alignItems: "center",
          padding: "0 24px",
          gap: 16,
        }}
      >
        <Link
          href="/"
          style={{ display: "flex", alignItems: "center", gap: 6, color: C.text3, fontSize: 13, textDecoration: "none" }}
        >
          <ArrowLeft size={15} />
          Home
        </Link>

        <div style={{ flex: 1 }} />

        {/* Live / Demo badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "3px 10px",
            borderRadius: 99,
            background: isLive ? `${C.green}18` : "rgba(255,255,255,0.06)",
            border: `1px solid ${isLive ? C.green + "40" : C.border}`,
            fontSize: 11,
            fontWeight: 600,
            color: isLive ? C.green : C.text3,
          }}
        >
          <span
            style={{
              width: 6, height: 6,
              borderRadius: "50%",
              background: isLive ? C.green : C.text3,
              animation: isLive ? "pulse 2s infinite" : "none",
            }}
          />
          {isLive ? "Live Data" : "Demo Mode"}
        </div>

        {isLive && timestamp && (
          <div style={{ display: "flex", alignItems: "center", gap: 5, color: C.text3, fontSize: 11 }}>
            <Clock size={12} />
            {formatTimestamp(timestamp)}
          </div>
        )}

        <Link
          href="/dashboard"
          style={{
            padding: "6px 14px",
            borderRadius: 99,
            background: C.blue,
            color: "#fff",
            fontSize: 12,
            fontWeight: 700,
            textDecoration: "none",
            whiteSpace: "nowrap",
          }}
        >
          Full Dashboard →
        </Link>
      </header>

      {/* ── Main ── */}
      <main style={{ paddingTop: 52, display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* ── Left panel: Scanner list ── */}
        <div
          style={{
            width: 340,
            minWidth: 280,
            borderRight: `1px solid ${C.border}`,
            display: "flex",
            flexDirection: "column",
            height: "100%",
            flexShrink: 0,
          }}
          className="hidden sm:flex"
        >
          {/* Search */}
          <div style={{ padding: "14px 14px 8px", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ position: "relative" }}>
              <Search
                size={14}
                style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: C.text3 }}
              />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search ticker…"
                style={{
                  width: "100%",
                  background: "rgba(255,255,255,0.04)",
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                  color: C.text1,
                  fontSize: 12,
                  padding: "7px 10px 7px 30px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div style={{ marginTop: 6, fontSize: 10, color: C.text3 }}>
              {filtered.length} signals · Sorted by score
            </div>
          </div>

          {/* Stock rows */}
          <div style={{ flex: 1, overflowY: "auto" }}>
            {loading ? (
              <div style={{ padding: 24, textAlign: "center", color: C.text3, fontSize: 12 }}>
                Loading scan data…
              </div>
            ) : filtered.length === 0 ? (
              <div style={{ padding: 24, textAlign: "center", color: C.text3, fontSize: 12 }}>
                No results
              </div>
            ) : (
              filtered.map((s) => {
                const isSelected = selected === s.ticker;
                const sigColor = SIGNAL_COLOR[s.signal];
                return (
                  <button
                    key={s.ticker}
                    onClick={() => setSelected(s.ticker)}
                    style={{
                      width: "100%",
                      padding: "11px 14px",
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      background: isSelected ? "rgba(255,255,255,0.06)" : "transparent",
                      border: "none",
                      borderBottom: `1px solid ${C.border}`,
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "background .15s",
                    }}
                  >
                    {/* Signal color bar */}
                    <div style={{ width: 3, height: 32, borderRadius: 2, background: sigColor, flexShrink: 0 }} />

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: C.text1 }}>{s.ticker}</span>
                        <ScoreBadge score={s.score} />
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 3 }}>
                        <SignalBadge signal={s.signal} />
                        <span style={{ fontSize: 10, color: C.text3 }}>{s.regime}</span>
                        {s.rr > 0 && (
                          <span style={{ fontSize: 10, color: C.text3, marginLeft: "auto" }}>
                            R/R {s.rr.toFixed(1)}x
                          </span>
                        )}
                      </div>
                    </div>

                    <ChevronRight size={14} color={isSelected ? C.text2 : C.text3} />
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ── Right panel: Detail ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px 40px" }}>

          {/* Mobile: stock list when nothing selected */}
          {!selected && (
            <div className="sm:hidden">
              {/* Mobile search */}
              <div style={{ marginBottom: 14, position: "relative" }}>
                <Search
                  size={14}
                  style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: C.text3 }}
                />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search ticker…"
                  style={{
                    width: "100%",
                    background: "rgba(255,255,255,0.04)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 8,
                    color: C.text1,
                    fontSize: 12,
                    padding: "8px 10px 8px 30px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {filtered.map((s) => (
                  <button
                    key={s.ticker}
                    onClick={() => setSelected(s.ticker)}
                    style={{
                      background: C.card,
                      border: `1px solid ${C.border}`,
                      borderRadius: 12,
                      padding: "14px",
                      textAlign: "left",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: C.text1 }}>{s.ticker}</span>
                      <ScoreBadge score={s.score} />
                    </div>
                    <SignalBadge signal={s.signal} />
                    <div style={{ marginTop: 6, fontSize: 10, color: C.text3 }}>{s.regime} · R/R {s.rr.toFixed(1)}x</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Desktop: placeholder when nothing selected */}
          {!selected && (
            <div className="hidden sm:flex" style={{ flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 400, gap: 12, color: C.text3 }}>
              <BarChart3 size={40} color={C.text3} />
              <p style={{ fontSize: 14 }}>Select a stock from the list to view analysis</p>
              {!isLive && (
                <p style={{ fontSize: 11, color: C.text3, background: "rgba(255,255,255,0.04)", padding: "6px 14px", borderRadius: 99 }}>
                  Demo mode — showing sample data
                </p>
              )}
            </div>
          )}

          {/* Detail view */}
          {selected && selectedStock && (
            <>
              {/* Mobile back */}
              <button
                onClick={() => setSelected(null)}
                className="sm:hidden"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 16,
                  color: C.text3,
                  fontSize: 13,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                <ArrowLeft size={15} />
                Back to list
              </button>

              {/* Stock header */}
              <div
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 14,
                  padding: "18px 20px",
                  marginBottom: 16,
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <h1 style={{ fontSize: 24, fontWeight: 800, color: C.text1, margin: 0 }}>
                        {selectedStock.ticker}
                      </h1>
                      <SignalBadge signal={selectedStock.signal} />
                      {selectedStock.highQuality && (
                        <span
                          style={{
                            fontSize: 10,
                            fontWeight: 700,
                            color: C.green,
                            background: `${C.green}18`,
                            border: `1px solid ${C.green}30`,
                            padding: "2px 8px",
                            borderRadius: 99,
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                          }}
                        >
                          <Zap size={10} />
                          High Quality
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                      {[
                        { label: "Regime", val: selectedStock.regime },
                        { label: "Sentiment", val: selectedStock.sentiment },
                        { label: "Score", val: `${selectedStock.score}/100` },
                        ...(selectedStock.price > 0 ? [{ label: "Price", val: `$${selectedStock.price.toFixed(2)}` }] : []),
                      ].map((m) => (
                        <div key={m.label}>
                          <div style={{ fontSize: 10, color: C.text3, marginBottom: 1 }}>{m.label}</div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: C.text1 }}>{m.val}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  {/* Watchlist button */}
                  <button
                    onClick={() => toggleWatchlist(selectedStock.ticker)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "8px 14px",
                      borderRadius: 8,
                      border: `1px solid ${watchlist.has(selectedStock.ticker) ? C.green + "50" : C.border}`,
                      background: watchlist.has(selectedStock.ticker) ? `${C.green}15` : "rgba(255,255,255,0.04)",
                      color: watchlist.has(selectedStock.ticker) ? C.green : C.text3,
                      cursor: "pointer",
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    <Heart
                      size={14}
                      fill={watchlist.has(selectedStock.ticker) ? C.green : "transparent"}
                      color={watchlist.has(selectedStock.ticker) ? C.green : C.text3}
                    />
                    {watchlist.has(selectedStock.ticker) ? "Saved" : "Watchlist"}
                  </button>
                </div>
              </div>

              {/* Chart */}
              <div
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 14,
                  padding: "16px 18px",
                  marginBottom: 16,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text2 }}>Price Chart</span>
                  <div style={{ display: "flex", gap: 6 }}>
                    {(["1d", "4h", "1h"] as const).map((iv) => (
                      <button
                        key={iv}
                        onClick={() => setChartInterval(iv)}
                        style={{
                          padding: "3px 10px",
                          borderRadius: 6,
                          border: `1px solid ${chartInterval === iv ? C.cyan + "60" : C.border}`,
                          background: chartInterval === iv ? `${C.cyan}18` : "transparent",
                          color: chartInterval === iv ? C.cyan : C.text3,
                          fontSize: 11,
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {iv}
                      </button>
                    ))}
                  </div>
                </div>
                <StockChart symbol={selectedStock.ticker} interval={chartInterval} days={90} height={220} />
                <div style={{ marginTop: 8, fontSize: 10, color: C.text3 }}>
                  Model output · For informational purposes only · Not financial advice
                </div>
              </div>

              {/* Risk metrics */}
              {selectedStock.stop > 0 && (
                <div
                  style={{
                    background: C.card,
                    border: `1px solid ${C.border}`,
                    borderRadius: 14,
                    padding: "16px 18px",
                    marginBottom: 16,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 14 }}>
                    <Shield size={15} color={C.cyan} />
                    <span style={{ fontSize: 12, fontWeight: 600, color: C.text2 }}>Risk Management</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                    {[
                      { label: "Entry", val: selectedStock.price > 0 ? `$${selectedStock.price.toFixed(2)}` : "—", color: C.text1 },
                      { label: "Stop Loss", val: `$${selectedStock.stop.toFixed(2)}`, color: C.red },
                      { label: "Take Profit", val: `$${selectedStock.tp.toFixed(2)}`, color: C.green },
                      { label: "R/R Ratio", val: `${selectedStock.rr.toFixed(1)}x`, color: C.cyan },
                    ].map((m) => (
                      <div
                        key={m.label}
                        style={{
                          background: "rgba(255,255,255,0.03)",
                          border: `1px solid ${C.border}`,
                          borderRadius: 10,
                          padding: "12px 10px",
                          textAlign: "center",
                        }}
                      >
                        <div style={{ fontSize: 15, fontWeight: 700, color: m.color }}>{m.val}</div>
                        <div style={{ fontSize: 10, color: C.text3, marginTop: 4 }}>{m.label}</div>
                      </div>
                    ))}
                  </div>
                  {selectedStock.stopPct > 0 && (
                    <div style={{ marginTop: 10, fontSize: 11, color: C.text3 }}>
                      Stop distance: {selectedStock.stopPct.toFixed(1)}% · Kelly fraction: {(selectedStock.kelly * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              )}

              {/* Why this signal */}
              <div
                style={{
                  background: `${C.cyan}08`,
                  border: `1px solid ${C.cyan}25`,
                  borderRadius: 14,
                  padding: "16px 18px",
                  marginBottom: 16,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 10 }}>
                  <Brain size={15} color={C.cyan} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.cyan }}>Why this signal?</span>
                </div>
                <p style={{ fontSize: 13, color: C.text2, lineHeight: 1.65, margin: 0 }}>{whySig}</p>

                {/* Signal flags */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
                  {[
                    { flag: selectedStock.trendStrength, label: "Trend Strength" },
                    { flag: selectedStock.volumeSpike,   label: "Volume Spike" },
                    { flag: selectedStock.aligned,       label: "TF Aligned" },
                    { flag: selectedStock.confluence,    label: "Confluence" },
                    { flag: selectedStock.entryOk,       label: "Entry OK" },
                  ]
                    .filter((f) => f.flag)
                    .map((f) => (
                      <span
                        key={f.label}
                        style={{
                          fontSize: 10,
                          fontWeight: 600,
                          padding: "3px 9px",
                          borderRadius: 99,
                          background: `${C.green}18`,
                          color: C.green,
                          border: `1px solid ${C.green}30`,
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                      >
                        <Check size={9} />
                        {f.label}
                      </span>
                    ))}
                </div>
              </div>

              {/* Ensemble voting */}
              <div
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 14,
                  padding: "16px 18px",
                  marginBottom: 16,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 14 }}>
                  <Brain size={15} color={C.blue} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text2 }}>Ensemble Voting</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {ensemble.map((a) => (
                    <div key={a.name} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: a.color, flexShrink: 0 }} />
                      <span style={{ fontSize: 11, fontWeight: 600, color: C.text1, width: 110 }}>{a.name}</span>
                      <div style={{ flex: 1, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                        <div style={{ width: `${a.conf}%`, height: "100%", background: a.color, borderRadius: 2, transition: "width .8s ease" }} />
                      </div>
                      <span style={{ fontSize: 10, color: C.text3, width: 32, textAlign: "right" }}>{a.conf}%</span>
                      <span style={{ fontSize: 10, fontWeight: 700, color: a.color, width: 34, textAlign: "right" }}>{a.vote}</span>
                    </div>
                  ))}
                </div>
                <div
                  style={{
                    marginTop: 12,
                    padding: "8px 12px",
                    borderRadius: 8,
                    background: `${SIGNAL_COLOR[selectedStock.signal]}15`,
                    border: `1px solid ${SIGNAL_COLOR[selectedStock.signal]}30`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: 12, fontWeight: 700, color: SIGNAL_COLOR[selectedStock.signal] }}>
                    Consensus: {selectedStock.signal}
                  </span>
                  <span style={{ fontSize: 10, color: SIGNAL_COLOR[selectedStock.signal] + "aa" }}>
                    Score {selectedStock.score}/100
                  </span>
                </div>
              </div>

              {/* Backtest mini-card */}
              <div
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 14,
                  padding: "16px 18px",
                  marginBottom: 16,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 14 }}>
                  <BarChart3 size={15} color={C.purple} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text2 }}>Backtest Summary</span>
                  <span style={{ fontSize: 10, color: C.text3, marginLeft: "auto" }}>Walk-forward validated</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                  {[
                    { label: "Win Rate", val: "68%", bar: 68, color: C.green },
                    { label: "Sharpe", val: "1.24", bar: 62, color: C.cyan },
                    { label: "Profit Factor", val: "2.1×", bar: 70, color: C.blue },
                    { label: "Max DD", val: "12.4%", bar: 25, color: C.red },
                  ].map((m) => (
                    <div key={m.label} style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 15, fontWeight: 700, color: m.color }}>{m.val}</div>
                      <div style={{ margin: "6px auto 4px", height: 3, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                        <div style={{ width: `${m.bar}%`, height: "100%", background: m.color, borderRadius: 2 }} />
                      </div>
                      <div style={{ fontSize: 10, color: C.text3 }}>{m.label}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 10, fontSize: 10, color: C.text3 }}>
                  Based on 1,000 Monte Carlo simulations · PPO-v3 ensemble
                </div>
              </div>

              {/* Feedback + CTA */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 24 }} className="sm:grid-cols-2">
                <FeedbackWidget ticker={selectedStock.ticker} />
                <div
                  style={{
                    background: `${C.blue}12`,
                    border: `1px solid ${C.blue}30`,
                    borderRadius: 14,
                    padding: "20px 22px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: 14,
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
                      <TrendingUp size={15} color={C.blue} />
                      <span style={{ fontSize: 12, fontWeight: 700, color: C.blue }}>Full Dashboard</span>
                    </div>
                    <p style={{ fontSize: 12, color: C.text3, lineHeight: 1.55, margin: 0 }}>
                      Access 1,500+ stocks, real-time alerts, portfolio tracking, and advanced backtesting.
                    </p>
                  </div>
                  <Link
                    href="/dashboard"
                    style={{
                      display: "inline-block",
                      padding: "9px 16px",
                      borderRadius: 8,
                      background: C.blue,
                      color: "#fff",
                      fontSize: 12,
                      fontWeight: 700,
                      textDecoration: "none",
                      textAlign: "center",
                    }}
                  >
                    Open Dashboard →
                  </Link>
                </div>
              </div>
            </>
          )}

          {/* Bottom feedback (when nothing selected) */}
          {!selected && !loading && (
            <div style={{ maxWidth: 480, marginTop: 32 }}>
              <FeedbackWidget />
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
