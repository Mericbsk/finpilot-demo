"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  Play,
  Filter,
  Download,
  TrendingUp,
  Brain,
  Zap,
  BarChart3,
  ChevronDown,
  ArrowUpRight,
  Loader2,
} from "lucide-react";
import { C, hashStr, seededRandom, genStock as genStockBase, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import DemoBanner from "@/components/DemoBanner";

/* ── Scanner-specific stock generator (extends shared base) ── */
function genStock(ticker: string, seed = 0) {
  const base = genStockBase(ticker);          // always use clean ticker
  const h = hashStr(ticker + seed);           // seed only affects AI metrics
  const rsi = Math.round(15 + seededRandom(h + 4) * 70);
  const rr = +(0.5 + seededRandom(h + 5) * 3.5).toFixed(1);
  const regimes = ["Trend", "Volatile", "Range"] as const;
  const regime = regimes[Math.floor(seededRandom(h + 6) * 3)];
  const sentiments = ["Bullish", "Neutral", "Bearish", "Mixed"] as const;
  const sentiment = sentiments[Math.floor(seededRandom(h + 7) * 4)];
  const stop = +(base.price * (1 - 0.02 - seededRandom(h + 8) * 0.06)).toFixed(2);
  const tp1 = +(base.price * (1 + 0.03 + seededRandom(h + 9) * 0.05)).toFixed(2);
  const tp2 = +(base.price * (1 + 0.07 + seededRandom(h + 10) * 0.06)).toFixed(2);
  const tp3 = +(base.price * (1 + 0.12 + seededRandom(h + 11) * 0.08)).toFixed(2);
  return {
    ...base,                                  // ticker stays clean: "AAPL" not "AAPL17731..."
    score: Math.round(12 + seededRandom(h + 2) * 83),   // AI score varies per scan
    signal: (function(s: number) { return s >= 75 ? "BUY" : s >= 55 ? "HOLD" : s >= 40 ? "CAUTION" : "SELL"; })(Math.round(12 + seededRandom(h + 2) * 83)),
    rsi,
    regime,
    sentiment,
    rr,
    stop,
    tp1,
    tp2,
    tp3,
  };
}

/* ── Preset type ───────────────────────────────────────────── */
type Preset = {
  id: string;
  name: string;
  icon: string;
  category: string;
  symbols: string[];
};

/* ── Category tab groups ───────────────────────────────────── */
const categoryOrder = ["Sectors", "Thematic", "Strategy", "Regional", "FinPilot"];
const categoryColors: Record<string, string> = {
  "Sectors": C.cyan,
  "Thematic": "#bf5af2",
  "Strategy": C.green,
  "Regional": C.yellow,
  "FinPilot": C.blue,
};

/* ── Signal Badge ──────────────────────────────────────────── */
function SignalBadge({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.15)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.15)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.15)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.15)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span style={{ color: c.color, backgroundColor: c.bg, borderRadius: 9999, padding: "2px 8px", fontSize: 10, fontWeight: 700 }}>
      {signal}
    </span>
  );
}

/* ── Main Page ─────────────────────────────────────────────── */
export default function ScannerPage() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [activeCategory, setActiveCategory] = useState("Sectors");
  const [activePresetId, setActivePresetId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanComplete, setScanComplete] = useState(false);
  const [sortByScore, setSortByScore] = useState(true);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  /* Load presets from JSON */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((data: Record<string, { name: string; icon: string; category: string; symbols: string[] }>) => {
        const list: Preset[] = Object.entries(data).map(([id, v]) => ({
          id,
          name: v.name,
          icon: v.icon,
          category: v.category,
          symbols: v.symbols,
        }));
        setPresets(list);
        const first = list.find((p) => p.category === "Sectors");
        if (first) setActivePresetId(first.id);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  /* Derived data */
  const categories = useMemo(() => {
    const cats = [...new Set(presets.map((p) => p.category))];
    return categoryOrder.filter((c) => cats.includes(c));
  }, [presets]);

  const filteredPresets = useMemo(
    () => presets.filter((p) => p.category === activeCategory),
    [presets, activeCategory],
  );

  const activePreset = presets.find((p) => p.id === activePresetId);

  const stocksBase = useMemo(() => {
    if (!activePreset) return [];
    const list = activePreset.symbols.map((t) => genStock(t, 0));
    return sortByScore ? [...list].sort((a, b) => b.score - a.score) : list;
  }, [activePreset, sortByScore]);

  /* Live prices from Yahoo Finance */
  const liveTickers = useMemo(() => stocksBase.map((s) => s.ticker), [stocksBase]);
  const { data: live } = useStockPrices(liveTickers);
  const stocks = useMemo(
    () => stocksBase.map((s) => withLivePrice(s, live[s.ticker])),
    [stocksBase, live],
  );

  const filtered = useMemo(() => {
    if (!searchTerm) return stocks;
    const q = searchTerm.toLowerCase();
    return stocks.filter((s) => s.ticker.toLowerCase().includes(q));
  }, [stocks, searchTerm]);

  /* Run Scan handler */
  const runScan = () => {
    if (isScanning || !activePreset) return;
    setIsScanning(true);
    setScanComplete(false);
    setScanProgress(0);
    setSelectedTicker(null);

    const total = activePreset.symbols.length;
    const steps = 20;
    const perStep = Math.ceil(total / steps);
    let current = 0;

    const interval = setInterval(() => {
      current += perStep;
      if (current >= total) {
        current = total;
        clearInterval(interval);
        setScanProgress(total);
        setSortByScore(true);
        setTimeout(() => {
          setIsScanning(false);
          setScanComplete(true);
        }, 400);
      } else {
        setScanProgress(current);
      }
    }, 100);
  };

  const selected = filtered.find((s) => s.ticker === selectedTicker) || stocks.find((s) => s.ticker === selectedTicker);

  const buyCount = filtered.filter((s) => s.signal === "BUY").length;
  const avgScore = filtered.length > 0 ? (filtered.reduce((a, s) => a + s.score, 0) / filtered.length).toFixed(1) : "0";
  const avgRR = filtered.length > 0 ? (filtered.reduce((a, s) => a + s.rr, 0) / filtered.length).toFixed(1) : "0";

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 size={32} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <DemoBanner />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>AI Scanner</h1>
          <p className="text-sm" style={{ color: C.text3 }}>
            {presets.length} preset · {new Set(presets.flatMap((p) => p.symbols)).size.toLocaleString()}+ stocks
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs"
            style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text2 }}
          >
            <Filter size={14} /> Filters <ChevronDown size={12} />
          </button>
          <button
            className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs"
            style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text2 }}
          >
            <Download size={14} /> Export
          </button>
          <button
            onClick={runScan}
            disabled={isScanning}
            className="flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold"
            style={{
              background: isScanning ? C.cardHover : `linear-gradient(to right, ${C.cyan}, ${C.blue})`,
              color: isScanning ? C.text2 : "#000",
              cursor: isScanning ? "not-allowed" : "pointer",
            }}
          >
            {isScanning ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {isScanning ? `Scanning ${scanProgress}/${activePreset?.symbols.length ?? 0}...` : "Run Scan"}
          </button>
        </div>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setActiveCategory(cat);
              const first = presets.find((p) => p.category === cat);
              if (first) setActivePresetId(first.id);
              setSelectedTicker(null);
            }}
            className="shrink-0 rounded-full px-4 py-1.5 text-xs font-medium transition-colors"
            style={{
              backgroundColor: activeCategory === cat ? `${categoryColors[cat] || C.cyan}20` : C.card,
              color: activeCategory === cat ? categoryColors[cat] || C.cyan : C.text2,
              border: activeCategory === cat ? `1px solid ${categoryColors[cat] || C.cyan}` : "1px solid transparent",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Preset selector */}
      <div className="flex flex-wrap gap-2">
        {filteredPresets.map((p) => (
          <button
            key={p.id}
            onClick={() => { setActivePresetId(p.id); setSelectedTicker(null); setSearchTerm(""); setScanComplete(false); }}
            className="shrink-0 rounded-xl px-3 py-2 text-xs font-medium transition-colors"
            style={{
              backgroundColor: activePresetId === p.id ? C.cardHover : C.card,
              color: activePresetId === p.id ? C.text1 : C.text2,
              border: activePresetId === p.id ? `1px solid ${C.border}` : "1px solid transparent",
            }}
          >
            <span className="mr-1.5">{p.icon}</span>
            {p.name}
            <span className="ml-1.5 opacity-50">({p.symbols.length})</span>
          </button>
        ))}
      </div>

      {/* Scan progress bar */}
      {isScanning && activePreset && (
        <div className="rounded-xl p-3" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span style={{ color: C.text2 }}>Scanning <span style={{ color: C.text1, fontWeight: 600 }}>{activePreset.name}</span>...</span>
            <span style={{ color: C.cyan, fontWeight: 600 }}>{Math.round((scanProgress / activePreset.symbols.length) * 100)}%</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: C.primary }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${(scanProgress / activePreset.symbols.length) * 100}%`,
                background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`,
                transition: "width 0.15s ease-out",
              }}
            />
          </div>
        </div>
      )}

      {/* Scan complete banner */}
      {scanComplete && !isScanning && (
        <div className="flex items-center justify-between rounded-xl px-4 py-3" style={{ backgroundColor: "rgba(48,209,88,0.1)", border: `1px solid rgba(48,209,88,0.25)` }}>
          <div className="flex items-center gap-2">
            <Zap size={14} style={{ color: C.green }} />
            <span className="text-xs font-medium" style={{ color: C.green }}>
              Scan complete — {filtered.length} stocks analyzed · {buyCount} buy signals · Top score {filtered.length > 0 ? Math.max(...filtered.map((s) => s.score)) : 0}/100
            </span>
          </div>
          <button
            onClick={() => setScanComplete(false)}
            className="text-xs rounded-lg px-2 py-1"
            style={{ color: C.text3 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Summary metrics */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Stocks", value: filtered.length.toString(), icon: BarChart3, color: C.text1 },
          { label: "Buy Signals", value: buyCount.toString(), icon: TrendingUp, color: C.green },
          { label: "Avg Score", value: avgScore, icon: Brain, color: C.text1 },
          { label: "Avg R/R", value: avgRR, icon: Zap, color: C.cyan },
        ].map((m) => (
          <div key={m.label} className="rounded-xl px-4 py-3" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
            <div className="flex items-center justify-between">
              <span style={{ fontSize: 11, color: C.text3 }}>{m.label}</span>
              <m.icon size={13} style={{ color: C.text3 }} />
            </div>
            <div className="mt-1 text-lg font-semibold" style={{ color: m.color }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: C.text3 }} />
        <input
          type="text"
          placeholder="Filter by ticker..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded-xl py-2.5 pl-9 pr-4 text-sm outline-none"
          style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text1 }}
        />
      </div>

      {/* Results table + Detail panel */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Table */}
        <div className="lg:col-span-3 rounded-2xl overflow-hidden" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <div className="overflow-x-auto" style={{ maxHeight: 520 }}>
            <table className="w-full text-left">
              <thead className="sticky top-0 z-10" style={{ backgroundColor: C.card }}>
                <tr style={{ borderBottom: `1px solid ${C.border}`, fontSize: 11, color: C.text3 }}>
                  <th className="px-4 py-3 font-medium">Symbol</th>
                  <th className="px-4 py-3 font-medium">Price</th>
                  <th className="px-4 py-3 font-medium">Chg%</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Signal</th>
                  <th className="px-4 py-3 font-medium">RSI</th>
                  <th className="px-4 py-3 font-medium">R/R</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr
                    key={s.ticker}
                    onClick={() => setSelectedTicker(s.ticker)}
                    className="cursor-pointer text-xs transition-colors"
                    style={{
                      borderBottom: `1px solid ${C.border}`,
                      backgroundColor: selectedTicker === s.ticker ? "rgba(0,212,255,0.08)" : "transparent",
                    }}
                    onMouseEnter={(e) => { if (selectedTicker !== s.ticker) e.currentTarget.style.backgroundColor = C.cardHover; }}
                    onMouseLeave={(e) => { if (selectedTicker !== s.ticker) e.currentTarget.style.backgroundColor = "transparent"; }}
                  >
                    <td className="px-4 py-2.5 font-medium" style={{ color: C.text1 }}>{s.ticker}</td>
                    <td className="px-4 py-2.5" style={{ color: C.text1 }}>${s.price}</td>
                    <td className="px-4 py-2.5" style={{ color: s.change >= 0 ? C.green : C.red }}>
                      {s.change >= 0 ? "+" : ""}{s.change}%
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <div className="h-1 w-8 rounded-full" style={{ backgroundColor: C.primary }}>
                          <div className="h-1 rounded-full" style={{
                            width: `${s.score}%`,
                            backgroundColor: s.score >= 75 ? C.green : s.score >= 50 ? C.cyan : C.red,
                          }} />
                        </div>
                        <span style={{ color: C.text2 }}>{s.score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5"><SignalBadge signal={s.signal} /></td>
                    <td className="px-4 py-2.5" style={{ color: C.text2 }}>{s.rsi}</td>
                    <td className="px-4 py-2.5" style={{ color: s.rr >= 2 ? C.green : C.text2 }}>{s.rr}x</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-sm" style={{ color: C.text3 }}>
                      No stocks found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-2 space-y-4">
          {selected ? (
            <>
              <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold" style={{ color: C.text1 }}>{selected.ticker}</h2>
                    <p className="text-xs" style={{ color: C.text3 }}>{activePreset?.name}</p>
                  </div>
                  <SignalBadge signal={selected.signal} />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold" style={{ color: C.text1 }}>${selected.price}</span>
                  <span className="text-sm" style={{ color: selected.change >= 0 ? C.green : C.red }}>
                    {selected.change >= 0 ? "+" : ""}{selected.change}%
                  </span>
                </div>
              </div>

              <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <h3 className="mb-3 text-xs font-semibold" style={{ color: C.text1 }}>AI Score & Indicators</h3>
                <div className="mb-4">
                  <div className="mb-1 flex justify-between text-xs">
                    <span style={{ color: C.text3 }}>Composite Score</span>
                    <span className="font-bold" style={{ color: C.text1 }}>{selected.score}/100</span>
                  </div>
                  <div className="h-2 rounded-full" style={{ backgroundColor: C.primary }}>
                    <div className="h-2 rounded-full" style={{
                      width: `${selected.score}%`,
                      backgroundColor: selected.score >= 75 ? C.green : selected.score >= 50 ? C.cyan : C.red,
                    }} />
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  {[
                    { label: "RSI (14)", value: selected.rsi.toString() },
                    { label: "Regime", value: selected.regime },
                    { label: "Sentiment", value: selected.sentiment },
                    { label: "Risk/Reward", value: `${selected.rr}x` },
                  ].map((i) => (
                    <div key={i.label} className="flex justify-between">
                      <span style={{ color: C.text3 }}>{i.label}</span>
                      <span className="font-medium" style={{ color: C.text1 }}>{i.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <h3 className="mb-3 text-xs font-semibold" style={{ color: C.text1 }}>Trade Plan</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(255,69,58,0.08)" }}>
                    <span style={{ color: C.red }}>Stop Loss</span>
                    <span className="font-bold" style={{ color: C.red }}>${selected.stop}</span>
                  </div>
                  {[
                    { label: "TP1", val: selected.tp1 },
                    { label: "TP2", val: selected.tp2 },
                    { label: "TP3", val: selected.tp3 },
                  ].map((tp) => (
                    <div key={tp.label} className="flex items-center justify-between rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(48,209,88,0.08)" }}>
                      <span style={{ color: C.green }}>{tp.label}</span>
                      <span className="font-bold" style={{ color: C.green }}>${tp.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Link
                href={`/dashboard/analysis?symbol=${selected.ticker}`}
                className="flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold"
                style={{ background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`, color: "#000" }}
              >
                <Brain size={16} /> Full AI Analysis <ArrowUpRight size={14} />
              </Link>
            </>
          ) : (
            <div
              className="flex h-64 items-center justify-center rounded-2xl text-sm"
              style={{ border: `1px dashed ${C.border}`, color: C.text3 }}
            >
              Select a stock to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
