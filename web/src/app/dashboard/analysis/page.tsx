"use client";

import { useState, useEffect, useMemo, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Shield,
  BarChart3,
  Newspaper,
  ChevronDown,
  Search,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Loader2,
  X,
} from "lucide-react";
import { C, hashStr, seededRandom, genStock as genStockBase, companyNames, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";

/* ── Pools for generating realistic text ───────────────────── */
const macdStates = ["Bullish Crossover", "Bearish Crossover", "Neutral", "Divergence", "Strong Bullish", "Weak Bearish"];
const regimes = ["Trend", "Volatile", "Range", "Breakout", "Mean-Revert"];
const sentiments = ["Strong Bullish", "Moderately Bullish", "Neutral", "Moderately Bearish", "Mixed"];
const models = ["PPO-v3 (Trend)", "A2C-v2 (Range)", "SAC-v1 (Volatile)", "DQN-v3 (Breakout)", "PPO-v3 (Multi)"];

const catalystPool = [
  "Strong earnings beat expected next quarter",
  "Institutional accumulation detected",
  "Sector rotation favoring this industry",
  "New product launch catalyst approaching",
  "Analyst upgrades trending positive",
  "Technical breakout from consolidation",
  "Revenue growth accelerating QoQ",
  "Expanding profit margins",
  "Market share gains in core segment",
  "Favorable regulatory developments",
  "Insider buying activity detected",
  "Share buyback program active",
  "International expansion underway",
  "Cost restructuring yielding results",
  "Strategic partnership announced",
];

const riskPool = [
  "Elevated valuation vs sector peers",
  "Rising interest rate sensitivity",
  "Competitive pressure intensifying",
  "Supply chain disruption risk",
  "Regulatory headwinds possible",
  "Key management transition risk",
  "Currency exposure concern",
  "Customer concentration risk",
  "Margin compression trend",
  "Debt-to-equity ratio elevated",
  "Market sentiment shifting bearish",
  "Geopolitical exposure in key markets",
];

const newsTitles = [
  "{T} reports quarterly earnings above estimates",
  "Analysts raise price target for {T}",
  "{T} announces strategic expansion plans",
  "Institutional investors increase {T} holdings",
  "{T} unveils new product roadmap",
  "Sector analysis: {T} positioned for growth",
  "{T} margin improvement surprises analysts",
  "Market outlook: {T} faces near-term headwinds",
  "{T} trading volume surges on momentum",
  "Technical analysis: {T} approaching key level",
  "{T} management reaffirms full-year guidance",
  "{T} partner deal boosts revenue outlook",
];

/* ── Generate full analysis for any ticker ─────────────────── */
function genAnalysis(ticker: string) {
  const base = genStockBase(ticker);
  const h = hashStr(ticker);
  const h2 = hashStr(ticker + "x");
  const h3 = hashStr(ticker + "z");

  const { price, change, score, signal } = base;
  const confidence = Math.round(40 + seededRandom(h + 3) * 55);
  const rsi = Math.round(15 + seededRandom(h + 4) * 70);
  const macd = macdStates[Math.floor(seededRandom(h + 10) * macdStates.length)];
  const sma50 = +(price * (0.92 + seededRandom(h + 11) * 0.16)).toFixed(2);
  const sma200 = +(price * (0.82 + seededRandom(h + 12) * 0.20)).toFixed(2);
  const bb_upper = +(price * (1.05 + seededRandom(h + 13) * 0.10)).toFixed(2);
  const bb_lower = +(price * (0.88 + seededRandom(h + 14) * 0.08)).toFixed(2);
  const regime = regimes[Math.floor(seededRandom(h + 15) * regimes.length)];
  const sentiment = sentiments[Math.floor(seededRandom(h + 16) * sentiments.length)];
  const volume = `${(2 + seededRandom(h + 17) * 98).toFixed(1)}M`;
  const pe = +(8 + seededRandom(h + 18) * 80).toFixed(1);
  const mcapB = Math.round(1 + seededRandom(h + 19) * 500);
  const marketCap = mcapB >= 100 ? `$${(mcapB / 100).toFixed(1)}T` : `$${mcapB}B`;
  const rr = +(0.5 + seededRandom(h + 20) * 3.5).toFixed(1);

  const stop = +(price * (1 - 0.02 - seededRandom(h + 21) * 0.06)).toFixed(2);
  const tp1 = +(price * (1 + 0.03 + seededRandom(h + 22) * 0.05)).toFixed(2);
  const tp2 = +(price * (1 + 0.07 + seededRandom(h + 23) * 0.06)).toFixed(2);
  const tp3 = +(price * (1 + 0.12 + seededRandom(h + 24) * 0.08)).toFixed(2);

  // Deterministic summary
  const direction = score >= 60 ? "bullish" : score >= 40 ? "neutral" : "bearish";
  const maStr = price > sma50 ? "above" : "below";
  const rsiStr = rsi > 65 ? "approaching overbought" : rsi < 35 ? "in oversold territory" : "at neutral levels";
  const aiSummary = `${ticker} shows ${direction} momentum with the stock trading ${maStr} its 50-day moving average. RSI at ${rsi} is ${rsiStr}. ${macd} on MACD confirms the current ${regime.toLowerCase()} regime. The AI model assigns a ${score}/100 composite score with ${confidence}% confidence. ${score >= 60 ? "Current conditions favor continuation of the trend with defined risk parameters." : "Position sizing should be conservative given mixed signals."}`;

  // Pick catalysts & risks deterministically
  const catalysts: string[] = [];
  for (let i = 0; i < 4; i++) catalysts.push(catalystPool[Math.floor(seededRandom(h + 40 + i) * catalystPool.length)]);
  const risks: string[] = [];
  for (let i = 0; i < 3; i++) risks.push(riskPool[Math.floor(seededRandom(h + 50 + i) * riskPool.length)]);

  // News
  const newsItems = [];
  const newsSentiments = ["Bullish", "Bearish", "Neutral"];
  const times = ["1h ago", "3h ago", "5h ago", "8h ago", "1d ago", "2d ago"];
  for (let i = 0; i < 4; i++) {
    const idx = Math.floor(seededRandom(h + 60 + i) * newsTitles.length);
    newsItems.push({
      title: newsTitles[idx].replace("{T}", ticker),
      sentiment: newsSentiments[Math.floor(seededRandom(h + 70 + i) * 3)],
      time: times[Math.floor(seededRandom(h + 80 + i) * times.length)],
    });
  }

  // Sparkline: 30 points using seededRandom for mini price chart
  const sparkline: number[] = [];
  let sp = price * 0.9;
  for (let i = 0; i < 30; i++) {
    sp += (seededRandom(h + 100 + i) - 0.48) * (price * 0.03);
    sp = Math.max(price * 0.7, Math.min(price * 1.3, sp));
    sparkline.push(+sp.toFixed(2));
  }
  sparkline[sparkline.length - 1] = +price.toFixed(2); // end at current price

  // Extra fundamental metrics
  const eps = +(seededRandom(h + 30) * 20 + 0.5).toFixed(2);
  const revenueGrowth = +(seededRandom(h + 31) * 60 - 10).toFixed(1);
  const debtEquity = +(seededRandom(h + 32) * 2).toFixed(2);
  const divYield = +(seededRandom(h + 33) * 5).toFixed(1);
  const high52w = +(price * (1.05 + seededRandom(h + 34) * 0.30)).toFixed(2);
  const low52w = +(price * (0.55 + seededRandom(h + 35) * 0.30)).toFixed(2);
  const beta = +((40 + seededRandom(h + 36) * 160) / 100).toFixed(2);
  const floatStr = `${Math.round(50 + seededRandom(h + 37) * 450)}M`;

  const companyName = companyNames[ticker] || `${ticker} Corp`;

  return {
    ticker,
    companyName,
    price,
    change,
    score,
    signal,
    confidence,
    rsi,
    macd,
    sma50,
    sma200,
    bb_upper,
    bb_lower,
    regime,
    sentiment,
    volume,
    pe,
    marketCap,
    rr,
    stop,
    tp1,
    tp2,
    tp3,
    aiSummary,
    catalysts,
    risks,
    newsItems,
    model: models[Math.floor(seededRandom(h + 90) * models.length)],
    sparkline,
    eps,
    revenueGrowth,
    debtEquity,
    divYield,
    high52w,
    low52w,
    beta,
    floatStr,
  };
}

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
    <span style={{ color: c.color, backgroundColor: c.bg, borderRadius: 9999, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>
      {signal}
    </span>
  );
}

/* ── Tabs ──────────────────────────────────────────────────── */
const tabs = ["AI Analysis", "Technical", "Fundamental", "News"];

/* ── SVG Sparkline ─────────────────────────────────────────── */
function Sparkline({ data, width = 320, height = 100 }: { data: number[]; width?: number; height?: number }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 8) - 4;
    return `${x},${y}`;
  });
  const isUp = data[data.length - 1] >= data[0];
  const lineColor = isUp ? C.green : C.red;
  const fillPoints = `0,${height} ${points.join(" ")} ${width},${height}`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={fillPoints} fill="url(#sparkGrad)" />
      <polyline points={points.join(" ")} fill="none" stroke={lineColor} strokeWidth="2" strokeLinejoin="round" />
      <circle cx={width} cy={parseFloat(points[points.length - 1].split(",")[1])} r="3" fill={lineColor} />
    </svg>
  );
}

/* ── SVG Score Ring ────────────────────────────────────────── */
function ScoreRing({ score }: { score: number }) {
  const r = 34;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 75 ? C.green : score >= 50 ? C.cyan : C.red;
  return (
    <div className="flex flex-col items-center">
      <svg width={84} height={84} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={42} cy={42} r={r} fill="none" stroke={C.primary} strokeWidth={5} />
        <circle
          cx={42} cy={42} r={r} fill="none"
          stroke={color} strokeWidth={5}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease-out" }}
        />
      </svg>
      <span
        className="text-xl font-bold"
        style={{ color: C.text1, position: "relative", top: -56, marginBottom: -40 }}
      >
        {score}
      </span>
      <span style={{ fontSize: 10, color: C.text3 }}>AI Score</span>
    </div>
  );
}

/* ── Scan API result type ──────────────────────────────────── */
interface ScanResult {
  symbol: string;
  price: number;
  score: number;
  regime: boolean;
  direction: boolean;
  atr: number | null;
  entry_ok: boolean;
  market_status: string;
  timestamp: string;
  volume_spike: boolean;
  price_momentum: boolean;
  trend_strength: boolean;
  filter_score: number;
  volume_multiple: number;
  momentum_3d_pct: number;
  momentum_best_return_pct: number;
  momentum_bias: string;
  ema_gap_pct: number;
  timeframe_aligned: boolean;
  alignment_ratio: number;
  momentum_confluence: boolean;
  stop_loss: number;
  take_profit: number;
  position_size: number;
  risk_reward: number;
  stop_loss_percent: number;
  sentiment: number;
  high_quality_signal: boolean;
}

/** Merge real scan data into the mock analysis object */
function mergeWithScan(mock: ReturnType<typeof genAnalysis>, scan: ScanResult) {
  const price = scan.price || mock.price;
  const score = scan.score ?? mock.score;
  const rr = scan.risk_reward ?? mock.rr;
  const stop = scan.stop_loss ?? mock.stop;
  const tp1 = scan.take_profit ?? mock.tp1;
  const tp2 = +(tp1 * 1.04).toFixed(2);
  const tp3 = +(tp1 * 1.08).toFixed(2);
  const signal = score >= 70 ? "BUY" : score >= 40 ? "HOLD" : score <= 20 ? "SELL" : "CAUTION";
  const regime = scan.direction ? "Trend" : scan.regime ? "Range" : "Volatile";
  const sentimentLabel = scan.sentiment > 0.3 ? "Strong Bullish" : scan.sentiment > 0 ? "Moderately Bullish" : scan.sentiment < -0.3 ? "Moderately Bearish" : "Neutral";
  const direction = score >= 60 ? "bullish" : score >= 40 ? "neutral" : "bearish";
  const rsiStr = mock.rsi > 65 ? "approaching overbought" : mock.rsi < 35 ? "in oversold territory" : "at neutral levels";
  const aiSummary = `${scan.symbol} shows ${direction} momentum (scanner score ${score}/100). ${scan.entry_ok ? "Entry conditions met." : "Entry conditions NOT met."} Market status: ${scan.market_status}. Momentum bias: ${scan.momentum_bias}. ${scan.high_quality_signal ? "High-quality signal detected." : ""} ${scan.momentum_confluence ? "Multi-timeframe momentum confluence confirmed." : ""} RSI is ${rsiStr}. Risk/Reward: ${rr}x.`;

  return {
    ...mock,
    price,
    score,
    signal,
    rr,
    stop,
    tp1,
    tp2,
    tp3,
    regime,
    sentiment: sentimentLabel,
    aiSummary,
    confidence: Math.min(99, Math.round(score * 0.9 + (scan.alignment_ratio ?? 0) * 20)),
    _scanData: scan, // keep raw data for display
  };
}

/* ── Inner component (uses useSearchParams) ────────────────── */
function AnalysisInner() {
  const searchParams = useSearchParams();
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("NVDA");
  const [activeTab, setActiveTab] = useState("AI Analysis");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [scanData, setScanData] = useState<ScanResult | null>(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  /* Outside click to close dropdown */
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
        setSearchTerm("");
      }
    }
    if (searchOpen) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [searchOpen]);

  /* Load symbols from presets JSON */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((data: Record<string, { symbols: string[] }>) => {
        const syms = [...new Set(Object.values(data).flatMap((v) => v.symbols))].sort();
        setAllSymbols(syms);
        // Read URL param
        const urlSymbol = searchParams.get("symbol");
        if (urlSymbol && syms.includes(urlSymbol.toUpperCase())) {
          setSelectedTicker(urlSymbol.toUpperCase());
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [searchParams]);

  /* Fetch real scan data from Python API */
  useEffect(() => {
    let cancelled = false;
    setScanLoading(true);
    setScanError(false);
    fetch("/py-api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols: [selectedTicker] }),
    })
      .then((r) => { if (!r.ok) throw new Error("scan failed"); return r.json(); })
      .then((result) => {
        if (!cancelled && result[selectedTicker]) {
          setScanData(result[selectedTicker]);
        } else if (!cancelled) {
          setScanData(null);
        }
        setScanLoading(false);
      })
      .catch(() => {
        if (!cancelled) { setScanData(null); setScanError(true); setScanLoading(false); }
      });
    return () => { cancelled = true; };
  }, [selectedTicker]);

  const dataBase = useMemo(() => genAnalysis(selectedTicker), [selectedTicker]);

  /* Live price overlay */
  const { data: live } = useStockPrices([selectedTicker]);
  const dataMock = useMemo(
    () => withLivePrice(dataBase, live[selectedTicker]),
    [dataBase, live, selectedTicker],
  );
  const data = useMemo(
    () => scanData ? mergeWithScan(dataMock, scanData) : dataMock,
    [dataMock, scanData],
  );

  const filteredSymbols = useMemo(() => {
    if (!searchTerm) return allSymbols.slice(0, 50);
    const q = searchTerm.toUpperCase();
    return allSymbols.filter((s) => s.includes(q)).slice(0, 50);
  }, [allSymbols, searchTerm]);

  const handleSelectTicker = useCallback((t: string) => {
    setSelectedTicker(t);
    setSearchOpen(false);
    setSearchTerm("");
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 size={32} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>AI Analysis</h1>
          <p className="text-sm" style={{ color: C.text3 }}>
            Deep AI-powered analysis · {allSymbols.length.toLocaleString()} stocks
            {scanData && (
              <span style={{ color: C.green, marginLeft: 8, fontSize: 11 }}>● Live Scanner</span>
            )}
            {scanLoading && (
              <span style={{ color: C.cyan, marginLeft: 8, fontSize: 11 }}>⟳ Scanning…</span>
            )}
            {scanError && !scanData && (
              <span style={{ color: C.yellow, marginLeft: 8, fontSize: 11 }}>⚠ Demo Data</span>
            )}
          </p>
        </div>
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium"
            style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text1 }}
          >
            <span style={{ color: C.cyan, fontWeight: 700 }}>{selectedTicker}</span>
            <ChevronDown size={14} style={{ color: C.text3 }} />
          </button>
          {searchOpen && (
            <div
              className="absolute right-0 top-full z-50 mt-2 w-72 rounded-xl overflow-hidden"
              style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, boxShadow: "0 16px 48px rgba(0,0,0,0.5)" }}
            >
              <div className="relative p-2">
                <Search size={14} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: C.text3 }} />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search ticker..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full rounded-lg py-2 pl-8 pr-8 text-sm outline-none"
                  style={{ backgroundColor: C.primary, color: C.text1, border: `1px solid ${C.border}` }}
                />
                <button onClick={() => { setSearchOpen(false); setSearchTerm(""); }} className="absolute right-4 top-1/2 -translate-y-1/2">
                  <X size={14} style={{ color: C.text3 }} />
                </button>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {filteredSymbols.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSelectTicker(s)}
                    className="flex w-full items-center justify-between px-4 py-2 text-xs transition-colors"
                    style={{
                      color: s === selectedTicker ? C.cyan : C.text2,
                      backgroundColor: s === selectedTicker ? "rgba(0,212,255,0.08)" : "transparent",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = C.cardHover; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = s === selectedTicker ? "rgba(0,212,255,0.08)" : "transparent"; }}
                  >
                    <span className="font-medium">{s}</span>
                    {s === selectedTicker && <CheckCircle size={12} style={{ color: C.cyan }} />}
                  </button>
                ))}
                {filteredSymbols.length === 0 && (
                  <div className="px-4 py-6 text-center text-xs" style={{ color: C.text3 }}>No results</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stock header card */}
      <div className="rounded-2xl p-6" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold" style={{ color: C.text1 }}>{selectedTicker}</h2>
              <SignalBadge signal={data.signal} />
            </div>
            <p className="text-sm" style={{ color: C.text3 }}>{data.companyName}</p>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold" style={{ color: C.text1 }}>${data.price}</span>
              <span className="flex items-center gap-1 text-sm font-medium" style={{ color: data.change >= 0 ? C.green : C.red }}>
                {data.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {data.change >= 0 ? "+" : ""}{data.change}%
              </span>
            </div>
          </div>
          {/* Score ring */}
          <ScoreRing score={data.score} />
          {/* Quick metrics */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {[
              { label: "Confidence", value: `${data.confidence}%`, color: C.cyan },
              { label: "Regime", value: data.regime, color: C.text1 },
              { label: "Sentiment", value: data.sentiment, color: data.sentiment.includes("Bullish") ? C.green : data.sentiment.includes("Bearish") ? C.red : C.text2 },
              { label: "Model", value: data.model.split(" ")[0], color: C.text1 },
            ].map((m) => (
              <div key={m.label} className="rounded-lg px-3 py-2" style={{ backgroundColor: C.primary }}>
                <div style={{ color: C.text3 }}>{m.label}</div>
                <div className="font-semibold" style={{ color: m.color }}>{m.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl p-1" style={{ backgroundColor: C.card }}>
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className="flex-1 rounded-lg px-4 py-2 text-xs font-medium transition-colors"
            style={{
              backgroundColor: activeTab === t ? C.primary : "transparent",
              color: activeTab === t ? C.text1 : C.text3,
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {/* AI Analysis Tab */}
          {activeTab === "AI Analysis" && (
            <>
              <div className="rounded-2xl p-6" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                <div className="mb-3 flex items-center gap-2">
                  <Brain size={18} style={{ color: C.cyan }} />
                  <h3 className="text-sm font-semibold" style={{ color: C.text1 }}>AI Summary</h3>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: C.text2 }}>{data.aiSummary}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                  <div className="mb-3 flex items-center gap-2">
                    <Lightbulb size={16} style={{ color: C.green }} />
                    <h3 className="text-sm font-semibold" style={{ color: C.text1 }}>Catalysts</h3>
                  </div>
                  <ul className="space-y-2">
                    {data.catalysts.map((c, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs" style={{ color: C.text2 }}>
                        <CheckCircle size={12} className="mt-0.5 shrink-0" style={{ color: C.green }} />
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
                  <div className="mb-3 flex items-center gap-2">
                    <AlertTriangle size={16} style={{ color: C.red }} />
                    <h3 className="text-sm font-semibold" style={{ color: C.text1 }}>Risks</h3>
                  </div>
                  <ul className="space-y-2">
                    {data.risks.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs" style={{ color: C.text2 }}>
                        <AlertTriangle size={12} className="mt-0.5 shrink-0" style={{ color: C.red }} />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}

          {/* Technical Tab */}
          {activeTab === "Technical" && (
            <div className="rounded-2xl p-6" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <h3 className="mb-4 text-sm font-semibold" style={{ color: C.text1 }}>Technical Indicators</h3>
              {/* Chart */}
              <div className="mb-6 rounded-xl p-4" style={{ backgroundColor: C.primary }}>
                <div className="mb-2 flex items-center justify-between text-xs">
                  <span style={{ color: C.text3 }}>30-Day Price Action</span>
                  <span className="font-medium" style={{ color: data.change >= 0 ? C.green : C.red }}>
                    {data.change >= 0 ? "+" : ""}{data.change}%
                  </span>
                </div>
                <Sparkline data={data.sparkline} />
                <div className="mt-2 flex justify-between text-xs" style={{ color: C.text3 }}>
                  <span>30d ago</span>
                  <span>Today · ${data.price}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {[
                  { label: "RSI (14)", value: data.rsi.toString(), color: data.rsi > 70 ? C.red : data.rsi < 30 ? C.green : C.text1 },
                  { label: "MACD", value: data.macd, color: data.macd.includes("Bullish") ? C.green : data.macd.includes("Bearish") ? C.red : C.text1 },
                  { label: "SMA 50", value: `$${data.sma50}`, color: data.price > data.sma50 ? C.green : C.red },
                  { label: "SMA 200", value: `$${data.sma200}`, color: data.price > data.sma200 ? C.green : C.red },
                  { label: "BB Upper", value: `$${data.bb_upper}`, color: C.text1 },
                  { label: "BB Lower", value: `$${data.bb_lower}`, color: C.text1 },
                  { label: "Risk/Reward", value: `${data.rr}x`, color: data.rr >= 2 ? C.green : C.text2 },
                  { label: "Volume", value: data.volume, color: C.text1 },
                ].map((ind) => (
                  <div key={ind.label} className="flex justify-between rounded-lg px-3 py-2.5" style={{ backgroundColor: C.primary }}>
                    <span style={{ color: C.text3 }}>{ind.label}</span>
                    <span className="font-semibold" style={{ color: ind.color }}>{ind.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fundamental Tab */}
          {activeTab === "Fundamental" && (
            <div className="rounded-2xl p-6" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <h3 className="mb-4 text-sm font-semibold" style={{ color: C.text1 }}>Fundamental Data</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {[
                  { label: "Market Cap", value: data.marketCap },
                  { label: "P/E Ratio", value: data.pe.toString() },
                  { label: "EPS", value: `$${data.eps}` },
                  { label: "Revenue Growth", value: `${data.revenueGrowth}%`, color: data.revenueGrowth >= 0 ? C.green : C.red },
                  { label: "Debt/Equity", value: data.debtEquity.toString(), color: data.debtEquity > 1.5 ? C.red : C.text1 },
                  { label: "Div Yield", value: `${data.divYield}%` },
                  { label: "52W High", value: `$${data.high52w}` },
                  { label: "52W Low", value: `$${data.low52w}` },
                  { label: "Beta", value: data.beta.toString() },
                  { label: "Float", value: data.floatStr },
                  { label: "Volume", value: data.volume },
                  { label: "Sentiment", value: data.sentiment },
                ].map((f) => (
                  <div key={f.label} className="flex justify-between rounded-lg px-3 py-2.5" style={{ backgroundColor: C.primary }}>
                    <span style={{ color: C.text3 }}>{f.label}</span>
                    <span className="font-semibold" style={{ color: f.color || C.text1 }}>{f.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* News Tab */}
          {activeTab === "News" && (
            <div className="rounded-2xl p-6" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <div className="mb-4 flex items-center gap-2">
                <Newspaper size={16} style={{ color: C.cyan }} />
                <h3 className="text-sm font-semibold" style={{ color: C.text1 }}>News & Sentiment</h3>
              </div>
              <div className="space-y-3">
                {data.newsItems.map((n, i) => (
                  <div key={i} className="rounded-xl p-4" style={{ backgroundColor: C.primary }}>
                    <div className="mb-1 flex items-start justify-between gap-2">
                      <p className="text-sm font-medium" style={{ color: C.text1 }}>{n.title}</p>
                      <span
                        className="shrink-0 rounded-full px-2 py-0.5 font-medium"
                        style={{
                          fontSize: 10,
                          color: n.sentiment === "Bullish" ? C.green : n.sentiment === "Bearish" ? C.red : C.text2,
                          backgroundColor: n.sentiment === "Bullish" ? "rgba(48,209,88,0.1)" : n.sentiment === "Bearish" ? "rgba(255,69,58,0.1)" : "rgba(255,255,255,0.05)",
                        }}
                      >
                        {n.sentiment}
                      </span>
                    </div>
                    <span style={{ fontSize: 10, color: C.text3 }}>{n.time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Trade Plan */}
          <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
            <div className="mb-3 flex items-center gap-2">
              <Target size={16} style={{ color: C.cyan }} />
              <h3 className="text-sm font-semibold" style={{ color: C.text1 }}>Trade Plan</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg px-3 py-2.5 text-xs" style={{ backgroundColor: "rgba(255,69,58,0.06)" }}>
                <div className="flex items-center gap-2">
                  <Shield size={12} style={{ color: C.red }} />
                  <span style={{ color: C.red }}>Stop Loss</span>
                </div>
                <span className="font-bold" style={{ color: C.red }}>${data.stop}</span>
              </div>
              <div className="rounded-lg px-3 py-2.5" style={{ backgroundColor: "rgba(48,209,88,0.06)" }}>
                {[
                  { label: "Target 1", val: data.tp1, pct: ((data.tp1 - data.price) / data.price * 100).toFixed(1) },
                  { label: "Target 2", val: data.tp2, pct: ((data.tp2 - data.price) / data.price * 100).toFixed(1) },
                  { label: "Target 3", val: data.tp3, pct: ((data.tp3 - data.price) / data.price * 100).toFixed(1) },
                ].map((tp) => (
                  <div key={tp.label} className="flex items-center justify-between py-1.5 text-xs">
                    <span style={{ color: C.green }}>{tp.label}</span>
                    <div className="text-right">
                      <span className="font-bold" style={{ color: C.green }}>${tp.val}</span>
                      <span className="ml-1" style={{ fontSize: 10, color: C.text3 }}>+{tp.pct}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* FinPilot Edge */}
          <div className="rounded-2xl p-5" style={{ border: `1px solid rgba(0,212,255,0.2)`, backgroundColor: "rgba(0,212,255,0.03)" }}>
            <div className="mb-3 flex items-center gap-2">
              <Activity size={16} style={{ color: C.cyan }} />
              <h3 className="text-sm font-semibold" style={{ color: C.cyan }}>FinPilot Edge</h3>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <div className="mb-1" style={{ color: C.text3 }}>Model Used</div>
                <div className="font-medium" style={{ color: C.text1 }}>{data.model}</div>
              </div>
              <div>
                <div className="mb-1" style={{ color: C.text3 }}>Confidence</div>
                <div className="flex items-center gap-2">
                  <div className="h-1.5 flex-1 rounded-full" style={{ backgroundColor: C.card }}>
                    <div className="h-1.5 rounded-full" style={{ width: `${data.confidence}%`, backgroundColor: C.cyan }} />
                  </div>
                  <span className="font-medium" style={{ color: C.cyan }}>{data.confidence}%</span>
                </div>
              </div>
              <div>
                <div className="mb-1" style={{ color: C.text3 }}>Data Sources</div>
                <div className="flex flex-wrap gap-1">
                  {["Price", "Volume", "RSI", "MACD", "Bollinger", "Sentiment"].map((s) => (
                    <span key={s} className="rounded-md px-1.5 py-0.5" style={{ fontSize: 10, backgroundColor: C.card, color: C.text2 }}>{s}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
            <h3 className="mb-3 text-sm font-semibold" style={{ color: C.text1 }}>Key Levels</h3>
            <div className="space-y-2 text-xs">
              {[
                { label: "SMA 50", value: `$${data.sma50}`, above: data.price > data.sma50 },
                { label: "SMA 200", value: `$${data.sma200}`, above: data.price > data.sma200 },
                { label: "BB Upper", value: `$${data.bb_upper}`, above: false },
                { label: "BB Lower", value: `$${data.bb_lower}`, above: true },
              ].map((l) => (
                <div key={l.label} className="flex justify-between">
                  <span style={{ color: C.text3 }}>{l.label}</span>
                  <span className="font-medium" style={{ color: l.above ? C.green : C.text2 }}>{l.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Page wrapper (Suspense for useSearchParams) ───────────── */
export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="flex h-96 items-center justify-center">
        <Loader2 size={32} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    }>
      <AnalysisInner />
    </Suspense>
  );
}
