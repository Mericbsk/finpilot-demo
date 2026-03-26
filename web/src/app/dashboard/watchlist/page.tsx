"use client";

import { useState, useEffect, useRef } from "react";
import {
  Star,
  Plus,
  X,
  Download,
  Play,
  TrendingUp,
  TrendingDown,
  Search,
  BarChart3,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { C, hashStr, seededRandom, genStock, companyNames, genSparkline, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import DemoBanner from "@/components/DemoBanner";

/* ── Mini sparkline (14 days) ──────────────────────────────── */
function Sparkline({ ticker }: { ticker: string }) {
  const pts = genSparkline(ticker, 14);
  const mn = Math.min(...pts);
  const mx = Math.max(...pts);
  const range = mx - mn || 1;
  const last = pts[pts.length - 1];
  const first = pts[0];
  const color = last >= first ? C.green : C.red;
  const points = pts.map((p, i) => `${(i / 13) * 80},${32 - ((p - mn) / range) * 28}`).join(" ");
  return (
    <svg width="80" height="32" viewBox="0 0 80 32" style={{ display: "block" }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Signal badge ──────────────────────────────────────────── */
function SignalBadge({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.12)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.12)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.12)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.12)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span
      style={{
        color: c.color,
        backgroundColor: c.bg,
        borderRadius: 9999,
        padding: "2px 8px",
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 0.5,
      }}
    >
      {signal}
    </span>
  );
}

/* ── Default watchlist ─────────────────────────────────────── */
const defaultTickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"];
const popularStocks = ["GOOGL", "META", "AMD", "AVGO", "CRM", "PLTR", "COIN", "UBER"];
const WATCHLIST_KEY = "finpilot_watchlist";
export default function WatchlistPage() {
  const [tickers, setTickers] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem(WATCHLIST_KEY);
        if (stored) { const arr = JSON.parse(stored); if (Array.isArray(arr) && arr.length) return arr; }
      } catch {}
    }
    return defaultTickers;
  });
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [dropOpen, setDropOpen] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanDone, setScanDone] = useState(false);
  const [scanPct, setScanPct] = useState(0);
  const [hovered, setHovered] = useState<string | null>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  /* Load 1,542 symbols */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((d: { presets: { symbols: string[] }[] }) => {
        const set = new Set<string>();
        d.presets.forEach((p) => p.symbols.forEach((s) => set.add(s)));
        setAllSymbols(Array.from(set).sort());
      })
      .catch(() => {});
  }, []);

  /* Outside-click close dropdown */
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setDropOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  /* Live prices */
  const { data: live } = useStockPrices(tickers);

  /* Derived watchlist data */
  const watchlist = tickers.map((t) => withLivePrice(genStock(t), live[t]));

  /* Filtered dropdown */
  const filtered = search.length >= 1
    ? allSymbols.filter((s) => s.startsWith(search.toUpperCase()) && !tickers.includes(s)).slice(0, 40)
    : [];

  /* Add / Remove */
  const addTicker = (sym: string) => {
    const s = sym.trim().toUpperCase();
    if (s && !tickers.includes(s)) {
      const next = [...tickers, s];
      setTickers(next);
      try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next)); } catch {}
    }
    setSearch("");
    setDropOpen(false);
  };
  const removeTicker = (sym: string) => {
    const next = tickers.filter((t) => t !== sym);
    setTickers(next);
    try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next)); } catch {}
  };

  /* Scan watchlist */
  const runScan = () => {
    if (scanning) return;
    setScanning(true);
    setScanDone(false);
    setScanPct(0);
    let pct = 0;
    const iv = setInterval(() => {
      pct += Math.random() * 18 + 5;
      if (pct >= 100) {
        pct = 100;
        clearInterval(iv);
        setTimeout(() => {
          setScanning(false);
          setScanDone(true);
        }, 400);
      }
      setScanPct(Math.min(100, Math.round(pct)));
    }, 220);
  };

  /* Export CSV */
  const exportCSV = () => {
    const header = "Ticker,Name,Price,Change%,Score,Signal\n";
    const rows = watchlist.map((w) => `${w.ticker},${w.name},${w.price},${w.change},${w.score},${w.signal}`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "watchlist.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  /* Summary stats */
  const buyCount = watchlist.filter((w) => w.signal === "BUY").length;
  const avgScore = watchlist.length ? Math.round(watchlist.reduce((a, w) => a + w.score, 0) / watchlist.length) : 0;
  const gainers = watchlist.filter((w) => w.change > 0).length;

  const summaryCards = [
    { label: "Tracked", value: watchlist.length, color: C.text1 },
    { label: "Buy Signals", value: buyCount, color: C.green },
    { label: "Avg Score", value: avgScore, color: C.cyan },
    { label: "Gainers", value: gainers, color: C.green },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
      <DemoBanner />
      {/* ── Header ─────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Star size={20} color={C.yellow} />
            <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1, margin: 0 }}>Watchlist</h1>
          </div>
          <p style={{ fontSize: 13, color: C.text3, margin: "4px 0 0" }}>Track your favorite stocks and get alerts</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={exportCSV}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12,
              border: `1px solid ${C.border}`, background: C.card,
              padding: "8px 14px", fontSize: 12, color: C.text2, cursor: "pointer",
            }}
          >
            <Download size={14} /> Export CSV
          </button>
          <button
            onClick={runScan}
            disabled={scanning}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12, border: "none",
              background: scanning ? C.card : `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
              padding: "8px 16px", fontSize: 12, fontWeight: 600,
              color: scanning ? C.text2 : "#000",
              cursor: scanning ? "default" : "pointer",
            }}
          >
            {scanning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            {scanning ? `Scanning… ${scanPct}%` : "Scan Watchlist"}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {scanning && (
        <div style={{ height: 3, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
          <div style={{ height: 3, borderRadius: 2, width: `${scanPct}%`, background: `linear-gradient(90deg, ${C.cyan}, ${C.blue})`, transition: "width 0.3s" }} />
        </div>
      )}
      {scanDone && (
        <div style={{ background: "rgba(48,209,88,0.08)", border: "1px solid rgba(48,209,88,0.25)", borderRadius: 12, padding: "10px 16px", fontSize: 12, color: C.green, fontWeight: 500 }}>
          ✓ Scan complete — {watchlist.length} stocks analyzed
        </div>
      )}

      {/* ── Add Symbol (searchable dropdown) ───────────────── */}
      <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, background: C.card, padding: 20 }}>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: C.text1, margin: "0 0 12px" }}>Add Symbols</h2>
        <div style={{ display: "flex", gap: 12, position: "relative" }} ref={dropRef}>
          <div style={{ flex: 1, position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: 12, top: 11, color: C.text3 }} />
            <input
              type="text"
              placeholder="Search from 1,542 stocks…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setDropOpen(true); }}
              onFocus={() => { if (search.length >= 1) setDropOpen(true); }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && search.trim()) addTicker(search);
              }}
              style={{
                width: "100%", borderRadius: 12, border: `1px solid ${C.border}`,
                background: C.primary, padding: "10px 14px 10px 34px", fontSize: 13,
                color: C.text1, outline: "none", boxSizing: "border-box",
              }}
            />
            {/* Dropdown */}
            {dropOpen && filtered.length > 0 && (
              <div
                style={{
                  position: "absolute", top: 44, left: 0, right: 0, maxHeight: 240,
                  overflowY: "auto", background: "#16161e", border: `1px solid ${C.border}`,
                  borderRadius: 12, zIndex: 50,
                }}
              >
                {filtered.map((s) => (
                  <button
                    key={s}
                    onClick={() => addTicker(s)}
                    style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      width: "100%", padding: "8px 14px", fontSize: 12, color: C.text1,
                      background: "transparent", border: "none", cursor: "pointer", textAlign: "left",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = C.cardHover)}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <span style={{ fontWeight: 600 }}>{s}</span>
                    <span style={{ color: C.text3, fontSize: 11 }}>{companyNames[s] || ""}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => { if (search.trim()) addTicker(search); }}
            style={{
              display: "flex", alignItems: "center", gap: 6, borderRadius: 12, border: "none",
              background: "rgba(0,212,255,0.1)", padding: "10px 16px", fontSize: 12,
              fontWeight: 500, color: C.cyan, cursor: "pointer", whiteSpace: "nowrap",
            }}
          >
            <Plus size={14} /> Add
          </button>
        </div>

        {/* Quick add */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12, alignItems: "center" }}>
          <span style={{ fontSize: 10, color: C.text3 }}>Quick add:</span>
          {popularStocks.filter((s) => !tickers.includes(s)).map((s) => (
            <button
              key={s}
              onClick={() => addTicker(s)}
              style={{
                borderRadius: 6, background: C.primary, border: `1px solid ${C.border}`,
                padding: "2px 8px", fontSize: 10, color: C.text2, cursor: "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = C.cyan)}
              onMouseLeave={(e) => (e.currentTarget.style.color = C.text2)}
            >
              + {s}
            </button>
          ))}
        </div>
      </div>

      {/* ── Summary Cards ──────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {summaryCards.map((c) => (
          <div
            key={c.label}
            style={{
              borderRadius: 12, border: `1px solid ${C.border}`, background: C.card,
              padding: "12px 16px", transition: "border-color 0.2s, background 0.2s",
              ...(hovered === `sum-${c.label}` ? { borderColor: C.borderHover, background: C.cardHover } : {}),
            }}
            onMouseEnter={() => setHovered(`sum-${c.label}`)}
            onMouseLeave={() => setHovered(null)}
          >
            <div style={{ fontSize: 11, color: C.text3 }}>{c.label}</div>
            <div style={{ fontSize: 20, fontWeight: 600, color: c.color, marginTop: 2 }}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* ── Watchlist Grid ─────────────────────────────────── */}
      {watchlist.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: C.text3, fontSize: 13 }}>
          No stocks in your watchlist. Add some above!
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
          {watchlist.map((w) => {
            const isHov = hovered === w.ticker;
            return (
              <div
                key={w.ticker}
                style={{
                  borderRadius: 16, border: `1px solid ${isHov ? C.borderHover : C.border}`,
                  background: isHov ? C.cardHover : C.card, padding: 16,
                  transition: "all 0.2s", cursor: "default",
                }}
                onMouseEnter={() => setHovered(w.ticker)}
                onMouseLeave={() => setHovered(null)}
              >
                {/* Top row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div>
                      <a
                        href={`/dashboard/analysis?symbol=${w.ticker}`}
                        style={{ fontSize: 14, fontWeight: 600, color: C.text1, textDecoration: "none" }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = C.cyan)}
                        onMouseLeave={(e) => (e.currentTarget.style.color = C.text1)}
                      >
                        {w.ticker}
                        <ExternalLink size={10} style={{ marginLeft: 4, opacity: 0.5, verticalAlign: "middle" }} />
                      </a>
                      <div style={{ fontSize: 11, color: C.text3 }}>{w.name}</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <SignalBadge signal={w.signal} />
                    <button
                      onClick={() => removeTicker(w.ticker)}
                      style={{
                        borderRadius: 6, padding: 4, background: "transparent", border: "none",
                        color: C.text3, cursor: "pointer",
                        opacity: isHov ? 1 : 0, transition: "opacity 0.2s",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = C.red)}
                      onMouseLeave={(e) => (e.currentTarget.style.color = C.text3)}
                    >
                      <X size={12} />
                    </button>
                  </div>
                </div>

                {/* Price + sparkline row */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: C.text1 }}>${w.price.toFixed(2)}</span>
                    <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 12, fontWeight: 500, color: w.change >= 0 ? C.green : C.red }}>
                      {w.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {w.change >= 0 ? "+" : ""}{w.change.toFixed(2)}%
                    </span>
                  </div>
                  <Sparkline ticker={w.ticker} />
                </div>

                {/* Score bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ flex: 1, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
                    <div
                      style={{
                        height: 4, borderRadius: 2,
                        width: `${w.score}%`,
                        background: w.score >= 75 ? C.green : w.score >= 50 ? C.cyan : C.red,
                        transition: "width 0.5s",
                      }}
                    />
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 500, color: C.text2 }}>{w.score}/100</span>
                </div>

                {/* Quick actions on hover */}
                <div
                  style={{
                    display: "flex", gap: 6, marginTop: 10,
                    opacity: isHov ? 1 : 0, transition: "opacity 0.2s",
                    pointerEvents: isHov ? "auto" : "none",
                  }}
                >
                  <a
                    href={`/dashboard/analysis?symbol=${w.ticker}`}
                    style={{
                      display: "flex", alignItems: "center", gap: 4, borderRadius: 8,
                      background: "rgba(0,212,255,0.08)", padding: "4px 10px",
                      fontSize: 10, color: C.cyan, textDecoration: "none", fontWeight: 500,
                    }}
                  >
                    <BarChart3 size={10} /> Analysis
                  </a>
                  <a
                    href={`/dashboard/backtest?symbol=${w.ticker}`}
                    style={{
                      display: "flex", alignItems: "center", gap: 4, borderRadius: 8,
                      background: "rgba(10,132,255,0.08)", padding: "4px 10px",
                      fontSize: 10, color: C.blue, textDecoration: "none", fontWeight: 500,
                    }}
                  >
                    <Play size={10} /> Backtest
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
