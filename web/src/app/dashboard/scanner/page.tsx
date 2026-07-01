"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Search,
  Play,
  Download,
  TrendingUp,
  Brain,
  Zap,
  BarChart3,
  ArrowUpRight,
  Loader2,
  Globe,
  Square,
  ArrowUpDown,
  ShoppingCart,
  DollarSign,
  FileText,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Eye,
} from "lucide-react";
import { toast } from "sonner";
import { useVirtualizer } from "@tanstack/react-virtual";
import { C, companyNames } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import { getCurrencySymbol } from "@/lib/userSettings";
import { apiFetch } from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import { ExplainPanel } from "@/components/ExplainPanel";
import { ConfidenceBadge } from "@/components/dashboard/ConfidenceCard";
import { FactorBadgeRow, MacroRegimeBanner, type FactorData, type MacroRegime } from "@/components/dashboard/FactorBadges";

/* ── Types ─────────────────────────────────────────────────── */
interface ScanResult {
  symbol: string;
  price: number;
  score: number;
  filter_score: number;
  regime: boolean;
  direction: boolean;
  entry_ok: boolean;
  risk_reward: number;
  stop_loss: number;
  take_profit: number;
  stop_loss_percent: number;
  momentum_bias: string;
  momentum_3d_pct: number;
  momentum_best_return_pct: number;
  trend_strength: boolean;
  volume_spike: boolean;
  price_momentum: boolean;
  liquidity_ok: boolean;
  high_quality_signal: boolean;
  sentiment: number;
  reason?: string;
  explanation?: string;
  timestamp: string;
  atr: number;
  position_size: number;
  kelly_fraction: number;
  volume_multiple: number;
  ema_gap_pct: number;
  alignment_ratio: number;
  timeframe_aligned: boolean;
  momentum_confluence: boolean;
  composite_score?: number;
  // Task 2: Risk-adjusted metrics
  sharpe_ratio?: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  max_drawdown_pct?: number;
  ann_vol_pct?: number;
  ann_return_pct?: number;
  ev_per_trade?: number;
  risk_data_quality?: string;
  // New enrichment factors
  squeeze_factor?: number;
  catalyst_factor?: number;
  // Early tier (WATCH/SETUP/TRIGGER/CONFIRM)
  tier?: string;
  tier_score?: number;
  tier_reasons?: string[];
  tier_size_fraction?: number;
  contraction_factor?: number;
  rvol_acceleration?: number;
  range_expansion?: number;
  // Fundamentals (EODHD)
  fundamental_score?: number;
  fundamental_quality?: string;
  pe_ratio?: number | null;
  forward_pe?: number | null;
  eps_growth_yoy?: number | null;
  revenue_growth_yoy?: number | null;
  profit_margin?: number | null;
  return_on_equity?: number | null;
  analyst_target?: number | null;
  analyst_rating?: number | null;
  // Faz 4: News catalyst (EODHD)
  news_catalyst_score?: number;
  news_sentiment?: number;
  news_count?: number;
  top_headlines?: string[];
  // Task 3: Dynamic position sizing
  dyn_shares?: number;
  dyn_notional?: number;
  dyn_risk_pct?: number;
  dyn_position_pct?: number;
  dyn_kelly_pct?: number;
  dyn_regime_scale?: number;
  dyn_portfolio_ok?: boolean;
}

interface DisplayStock {
  ticker: string;
  price: number;
  change: number;
  score: number;
  signal: string;
  regime: string;
  sentiment: string;
  rr: number;
  stop: number;
  tp1: number;
  momentum: string;
  trendStrength: boolean;
  volumeSpike: boolean;
  entryOk: boolean;
  highQuality: boolean;
  atr: number;
  positionSize: number;
  kellyFraction: number;
  volumeMultiple: number;
  emaGap: number;
  aligned: boolean;
  confluence: boolean;
  fromAPI: boolean;
  reason: string;
  explanation: string;
  // Task 2
  sharpe: number;
  sortino: number;
  annVol: number;
  maxDD: number;
  annReturn: number;
  evPerTrade: number;
  riskDataQuality: string;
  // Task 3
  dynShares: number;
  dynRiskPct: number;
  dynPositionPct: number;
  dynKellyPct: number;
  dynRegimeScale: number;
  dynPortfolioOk: boolean;
  // New enrichment factors
  squeezeFactor: number;
  catalystFactor: number;
  // Early tier
  tier: string;
  tierScore: number;
  tierReasons: string[];
  tierSizeFraction: number;
  contractionFactor: number;
  rvolAcceleration: number;
  rangeExpansion: number;
  // Fundamentals
  fundamentalScore: number;
  fundamentalQuality: string;
  peRatio: number | null;
  forwardPE: number | null;
  epsGrowth: number | null;
  revenueGrowth: number | null;
  profitMargin: number | null;
  returnOnEquity: number | null;
  analystTarget: number | null;
  analystRating: number | null;
  // Faz 4: News catalyst
  newsCatalystScore: number;
  newsSentiment: number;
  newsCount: number;
  topHeadlines: string[];
}

type Preset = {
  id: string;
  name: string;
  icon: string;
  category: string;
  symbols: string[];
};

/* ── Helpers ───────────────────────────────────────────────── */
function apiResultToStock(r: ScanResult, liveChange: number): DisplayStock {
  const score = Math.max(r.filter_score, r.score) || 0;
  const signal = r.high_quality_signal
    ? "BUY"
    : r.entry_ok
      ? "BUY"
      : score >= 3
        ? "HOLD"
        : score >= 2
          ? "CAUTION"
          : "SELL";
  return {
    ticker: r.symbol,
    price: r.price,
    change: liveChange,
    score: r.composite_score ?? Math.round((score / 4) * 100), // use backend 0-100 score when available
    signal,
    regime: r.regime ? (r.trend_strength ? "Trend" : "Range") : "Volatile",
    sentiment:
      r.momentum_bias === "bullish"
        ? "Bullish"
        : r.momentum_bias === "bearish"
          ? "Bearish"
          : "Neutral",
    rr: r.risk_reward,
    stop: r.stop_loss,
    tp1: r.take_profit,
    momentum: r.momentum_bias,
    trendStrength: r.trend_strength,
    volumeSpike: r.volume_spike,
    entryOk: r.entry_ok,
    highQuality: r.high_quality_signal,
    atr: r.atr,
    positionSize: r.position_size,
    kellyFraction: r.kelly_fraction,
    volumeMultiple: r.volume_multiple,
    emaGap: r.ema_gap_pct,
    aligned: r.timeframe_aligned,
    confluence: r.momentum_confluence,
    fromAPI: true,
    reason: r.reason ?? "",
    explanation: r.explanation ?? "",
    // Task 2: risk-adjusted metrics
    sharpe: r.sharpe_ratio ?? 0,
    sortino: r.sortino_ratio ?? 0,
    annVol: r.ann_vol_pct ?? 0,
    maxDD: r.max_drawdown_pct ?? 0,
    annReturn: r.ann_return_pct ?? 0,
    evPerTrade: r.ev_per_trade ?? 0,
    riskDataQuality: r.risk_data_quality ?? "low",
    // Task 3: dynamic position sizing
    dynShares: r.dyn_shares ?? 0,
    dynRiskPct: r.dyn_risk_pct ?? 0,
    dynPositionPct: r.dyn_position_pct ?? 0,
    dynKellyPct: r.dyn_kelly_pct ?? 0,
    dynRegimeScale: r.dyn_regime_scale ?? 1.0,
    dynPortfolioOk: r.dyn_portfolio_ok ?? true,
    squeezeFactor: r.squeeze_factor ?? 0,
    catalystFactor: r.catalyst_factor ?? 0,
    tier: r.tier ?? "",
    tierScore: r.tier_score ?? 0,
    tierReasons: r.tier_reasons ?? [],
    tierSizeFraction: r.tier_size_fraction ?? 0,
    contractionFactor: r.contraction_factor ?? 0,
    rvolAcceleration: r.rvol_acceleration ?? 0,
    rangeExpansion: r.range_expansion ?? 0,
    fundamentalScore: r.fundamental_score ?? 0,
    fundamentalQuality: r.fundamental_quality ?? "low",
    peRatio: r.pe_ratio ?? null,
    forwardPE: r.forward_pe ?? null,
    epsGrowth: r.eps_growth_yoy ?? null,
    revenueGrowth: r.revenue_growth_yoy ?? null,
    profitMargin: r.profit_margin ?? null,
    returnOnEquity: r.return_on_equity ?? null,
    analystTarget: r.analyst_target ?? null,
    analystRating: r.analyst_rating ?? null,
    newsCatalystScore: r.news_catalyst_score ?? 0,
    newsSentiment: r.news_sentiment ?? 0,
    newsCount: r.news_count ?? 0,
    topHeadlines: r.top_headlines ?? [],
  };
}

function mockToStock(ticker: string): DisplayStock {
  return {
    ticker,
    price: 0,
    change: 0,
    score: 0,
    signal: "—",
    regime: "—",
    sentiment: "—",
    rr: 0,
    stop: 0,
    tp1: 0,
    momentum: "—",
    trendStrength: false,
    volumeSpike: false,
    entryOk: false,
    highQuality: false,
    atr: 0,
    positionSize: 0,
    kellyFraction: 0,
    volumeMultiple: 0,
    emaGap: 0,
    aligned: false,
    confluence: false,
    fromAPI: false,
    reason: "",
    explanation: "",
    sharpe: 0,
    sortino: 0,
    annVol: 0,
    maxDD: 0,
    annReturn: 0,
    evPerTrade: 0,
    riskDataQuality: "low",
    dynShares: 0,
    dynRiskPct: 0,
    dynPositionPct: 0,
    dynKellyPct: 0,
    dynRegimeScale: 1.0,
    dynPortfolioOk: true,
    squeezeFactor: 0,
    catalystFactor: 0,
    tier: "",
    tierScore: 0,
    tierReasons: [],
    tierSizeFraction: 0,
    contractionFactor: 0,
    rvolAcceleration: 0,
    rangeExpansion: 0,
    fundamentalScore: 0,
    fundamentalQuality: "low",
    peRatio: null,
    forwardPE: null,
    epsGrowth: null,
    revenueGrowth: null,
    profitMargin: null,
    returnOnEquity: null,
    analystTarget: null,
    analystRating: null,
    newsCatalystScore: 0,
    newsSentiment: 0,
    newsCount: 0,
    topHeadlines: [],
  };
}

function exportCSV(stocks: DisplayStock[]) {
  const headers = [
    "Symbol",
    "Price",
    "Change%",
    "Score",
    "Signal",
    "R/R",
    "Stop",
    "TP",
    "Regime",
    "Sentiment",
    "Momentum",
    "Entry OK",
    "HQ Signal",
  ];
  const rows = stocks.map((s) => [
    s.ticker,
    s.price,
    s.change,
    s.score,
    s.signal,
    s.rr,
    s.stop,
    s.tp1,
    s.regime,
    s.sentiment,
    s.momentum,
    s.entryOk ? "Yes" : "No",
    s.highQuality ? "Yes" : "No",
  ]);
  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `scan_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ── Category config ───────────────────────────────────────── */
const categoryOrder = ["Sectors", "Thematic", "Strategy", "Regional", "FinPilot"];
const categoryColors: Record<string, string> = {
  Sectors: C.cyan,
  Thematic: "#bf5af2",
  Strategy: C.green,
  Regional: C.yellow,
  FinPilot: C.blue,
};

/* ── Signal Badge ──────────────────────────────────────────── */
function SignalBadge({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.15)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.15)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.15)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.15)" },
    "—": { color: C.text3, bg: "rgba(255,255,255,0.05)" },
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
      }}
    >
      {signal}
    </span>
  );
}

/* ── Tier Badge ───────────────────────────────────────────── */
const TIER_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  WATCH:   { color: "#ffd60a", bg: "rgba(255,214,10,0.15)",   label: "👁 WATCH" },
  SETUP:   { color: "#ff9f0a", bg: "rgba(255,159,10,0.15)",   label: "⚙ SETUP" },
  TRIGGER: { color: "#00d4ff", bg: "rgba(0,212,255,0.15)",    label: "⚡ TRIGGER" },
  CONFIRM: { color: "#30d158", bg: "rgba(48,209,88,0.15)",    label: "✓ CONFIRM" },
};

function TierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier];
  if (!cfg) return null;
  return (
    <span
      style={{
        color: cfg.color,
        backgroundColor: cfg.bg,
        borderRadius: 9999,
        padding: "1px 6px",
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: "0.02em",
        whiteSpace: "nowrap" as const,
      }}
    >
      {cfg.label}
    </span>
  );
}

/* ── sessionStorage persistence ────────────────────────────── */
const CACHE_KEY = "finpilot_scanner_cache";
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

interface ScannerCache {
  scanResults: Record<string, ScanResult>;
  activePresetId: string | null;
  scanAllMode: boolean;
  savedAt: number;
}

function readCache(): ScannerCache | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed: ScannerCache = JSON.parse(raw);
    if (Date.now() - parsed.savedAt > CACHE_TTL_MS) {
      sessionStorage.removeItem(CACHE_KEY);
      return null;
    }
    return parsed;
  } catch { return null; }
}

function writeCache(data: Omit<ScannerCache, "savedAt">) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ...data, savedAt: Date.now() }));
  } catch { /* quota — skip */ }
}

/* ── Scan API caller (batches of 200) ─────────────────────────────────────
 * Sending 200 symbols per call means only ~9 sequential batches for all 1812
 * symbols (vs 36+ batches at batch=50). Alpaca bulk prefetch issues a fixed
 * number of HTTP calls per batch regardless of symbol count (~O(timeframes),
 * not O(symbols)), so larger batches cut total request count with no extra
 * server-side cost. CONCURRENT_BATCHES stays at 1 for now — raising it is a
 * separate follow-up once single-batch throughput is confirmed stable.
 * ─────────────────────────────────────────────────────────────────────── */
const BATCH_SIZE = 200;       // 200 symbols per batch — Alpaca bulk prefetch issues O(timeframes)
                               // HTTP calls, not O(symbols), so larger batches don't add server-side
                               // cost; cuts a 1812-symbol scan from ~36 sequential requests to ~9.
const CONCURRENT_BATCHES = 1; // Sequential batches — concurrent scan causes API thread exhaustion

async function scanBatch(
  symbols: string[],
): Promise<Record<string, ScanResult>> {
  const resp = await apiFetch("/api/v1/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbols }),
  });
  if (!resp.ok) throw new Error(`Scan failed: ${resp.status}`);
  return resp.json();
}

/* ── Main Page ─────────────────────────────────────────────── */
export default function ScannerPage() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [activeCategory, setActiveCategory] = useState("Sectors");
  const [activePresetId, setActivePresetId] = useState<string | null>(() => readCache()?.activePresetId ?? null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanTotal, setScanTotal] = useState(0);
  const [scanResults, setScanResults] = useState<Record<string, ScanResult>>(
    () => readCache()?.scanResults ?? {},
  );
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [explainOpen, setExplainOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sortCol, setSortCol] = useState<string>("score");
  const [sortAsc, setSortAsc] = useState(false);
  const [scanAllMode, setScanAllMode] = useState<boolean>(() => readCache()?.scanAllMode ?? false);
  const abortRef = useRef(false);
  const tableParentRef = useRef<HTMLDivElement>(null);

  /* Daily report + paper trading queue */
  const [dailyReport, setDailyReport] = useState<{
    date: string; scanned: number; buySignals: number; topSignals: DisplayStock[];
  } | null>(null);
  const [paperQueue, setPaperQueue] = useState<DisplayStock[]>([]);
  const [reportSaved, setReportSaved] = useState(false);
  const [showReportPanel, setShowReportPanel] = useState(false);

  /* Alpaca state */
  const [alpacaAccount, setAlpacaAccount] = useState<{
    cash: number; portfolio_value: number; buying_power: number;
  } | null>(null);
  const [alpacaConnected, setAlpacaConnected] = useState(false);
  const [orderPending, setOrderPending] = useState(false);

  /* Load min score threshold + currency from user settings */
  const [minScoreFilter, setMinScoreFilter] = useState(0);
  const [showOnlyResults, setShowOnlyResults] = useState(false);
  const [currency, setCurrency] = useState("$");
  const [systemBrier, setSystemBrier] = useState<number | null>(null);
  const [macroData, setMacroData] = useState<FactorData | null>(null);
  useEffect(() => {
    try {
      const stored = localStorage.getItem("finpilot_settings");
      if (stored) {
        const s = JSON.parse(stored);
        // riskAppetite 1(conservative)→80, 3(medium)→60, 5(aggressive)→30
        const map: Record<number, number> = { 1: 80, 2: 70, 3: 60, 4: 45, 5: 30 };
        setMinScoreFilter(map[s.riskAppetite as number] ?? 0);
        setCurrency(getCurrencySymbol(s.market || "US"));
      }
    } catch {}
  }, []);

  /* Fetch system calibration brier for confidence badge */
  useEffect(() => {
    fetch("/py-api/loop/calibration/stats")
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.brier != null) setSystemBrier(d.brier); })
      .catch(() => {});
  }, []);

  /* Fetch FRED macro regime once on mount (SPY as proxy — regime is global) */
  useEffect(() => {
    apiFetch("/api/v1/factors/SPY")
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.macro_regime) setMacroData(d as FactorData); })
      .catch(() => {});
  }, []);

  /* Persist preset/mode changes to sessionStorage */
  useEffect(() => {
    if (!activePresetId && !scanAllMode) return;
    const cached = readCache();
    writeCache({
      scanResults: cached?.scanResults ?? {},
      activePresetId,
      scanAllMode,
    });
  }, [activePresetId, scanAllMode]);

  /* Check Alpaca connection on mount */
  useEffect(() => {
    apiFetch("/api/v1/trade/account")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((data) => { setAlpacaAccount(data); setAlpacaConnected(true); })
      .catch(() => setAlpacaConnected(false));
  }, []);

  /* Add one stock to persistent watchlist */
  const addToWatchlist = useCallback(async (stock: DisplayStock) => {
    try {
      const res = await apiFetch("/api/v1/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: stock.ticker,
          signal: stock.signal,
          entry_price: stock.price,
          stop_loss: stock.stop,
          take_profit: stock.tp1,
          score: stock.score,
          regime: stock.regime,
          sentiment: stock.sentiment,
          risk_reward: stock.rr,
          reason: stock.reason,
          explanation: stock.explanation,
        }),
      });
      if (!res.ok) throw new Error();
      toast.success(`${stock.ticker} watchlist'e eklendi`, { description: `Giriş: $${stock.price.toFixed(2)} · Stop: $${stock.stop > 0 ? stock.stop.toFixed(2) : "—"}` });
    } catch {
      toast.error(`${stock.ticker} eklenemedi`);
    }
  }, []);

  /* Place order on Alpaca */
  const placeAlpacaOrder = useCallback(async (stock: DisplayStock) => {
    if (orderPending) return;
    const confirmed = window.confirm(`Place BUY order for ${stock.ticker}?\nPrice: ${currency}${stock.price.toFixed(2)}\nStop Loss: ${stock.stop > 0 ? currency + stock.stop : 'Auto'}\nTake Profit: ${stock.tp1 > 0 ? currency + stock.tp1 : 'Auto'}`);
    if (!confirmed) return;
    setOrderPending(true);
    const toastId = toast.loading(`Placing order for ${stock.ticker}…`);
    try {
      const resp = await apiFetch("/api/v1/trade/buy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: stock.ticker,
          qty: 0,
          limit_price: stock.price > 0 ? Math.round(stock.price * 1.005 * 100) / 100 : null,
          stop_loss: stock.stop > 0 ? stock.stop : null,
          take_profit: stock.tp1 > 0 ? stock.tp1 : null,
          time_in_force: "day",
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Order failed" }));
        throw new Error(err.detail || "Order failed");
      }
      const order = await resp.json();
      toast.success(
        `${stock.ticker} — ${order.qty} shares @ ${currency}${order.limit_price || 'MKT'} (${order.order_id.slice(0, 8)}…)`,
        { id: toastId },
      );
      apiFetch("/api/v1/trade/account").then(r => r.json()).then(setAlpacaAccount).catch(() => {});
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Order failed";
      toast.error(msg, { id: toastId });
    } finally {
      setOrderPending(false);
    }
  }, [orderPending]);

  /* Load presets from JSON */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then(
        (
          data: Record<
            string,
            {
              name: string;
              icon: string;
              category: string;
              symbols: string[];
            }
          >,
        ) => {
          const list: Preset[] = Object.entries(data).map(([id, v]) => ({
            id,
            name: v.name,
            icon: v.icon,
            category: v.category,
            symbols: v.symbols,
          }));
          setPresets(list);
          const first = list.find((p) => p.category === "Sectors");
          // Only set default preset if no cached preset is available
          if (first && !readCache()?.activePresetId) setActivePresetId(first.id);
          setLoading(false);
        },
      )
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

  /* Current symbols to display */
  const currentSymbols = useMemo(
    () => activePreset?.symbols ?? [],
    [activePreset],
  );

  /* All unique symbols across every preset (1812) */
  const allPresetSymbols = useMemo(
    () => [...new Set(presets.flatMap((p) => p.symbols))],
    [presets],
  );

  /* Live prices from Yahoo Finance — only for the active preset to avoid hammering the API */
  const { data: live } = useStockPrices(currentSymbols);

  /* Build display stocks: merge API results with live prices */
  const stocks = useMemo(() => {
    // In Scan All mode show ALL preset symbols (1812) so the user can see every
    // stock; scanned ones (213) get full API data, the rest get price from live
    // quotes or show "—" placeholders.
    const symbolsToShow = scanAllMode ? allPresetSymbols : currentSymbols;

    const list: DisplayStock[] = symbolsToShow.map((ticker) => {
      const apiData = scanResults[ticker];
      const liveData = live[ticker];
      if (apiData) {
        const s = apiResultToStock(apiData, liveData?.change ?? 0);
        if (liveData) s.price = liveData.price;
        return s;
      }
      // No scan yet: show with live prices
      const base = mockToStock(ticker);
      if (liveData) {
        base.price = liveData.price;
        base.change = liveData.change;
      }
      return base;
    });
    return list;
  }, [currentSymbols, allPresetSymbols, scanResults, live, scanAllMode]);

  /* Sort stocks — BUY signals always pinned to top when sorting by score */
  const sorted = useMemo(() => {
    const arr = [...stocks];
    const dir = sortAsc ? 1 : -1;
    // Signal priority: BUY=0, HOLD=1, CAUTION=2, SELL=3, —=4
    const sigPriority = (s: string) =>
      s === "BUY" ? 0 : s === "HOLD" ? 1 : s === "CAUTION" ? 2 : s === "SELL" ? 3 : 4;
    arr.sort((a, b) => {
      switch (sortCol) {
        case "ticker": return dir * a.ticker.localeCompare(b.ticker);
        case "price": return dir * (a.price - b.price);
        case "change": return dir * (a.change - b.change);
        case "signal": return dir * a.signal.localeCompare(b.signal);
        case "rr": return dir * (a.rr - b.rr);
        case "sharpe": return dir * (a.sharpe - b.sharpe);
        case "annVol": return dir * (a.annVol - b.annVol);
        case "regime": return dir * a.regime.localeCompare(b.regime);
        default: {
          // Default (score): BUY first → score desc → "—" last
          const sigDiff = sigPriority(a.signal) - sigPriority(b.signal);
          if (sigDiff !== 0) return sigDiff; // BUY always top regardless of asc/desc toggle
          return dir * (a.score - b.score);
        }
      }
    });
    return arr;
  }, [stocks, sortCol, sortAsc]);

  const filtered = useMemo(() => {
    let list = sorted;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      list = list.filter((s) => s.ticker.toLowerCase().includes(q));
    }
    // In scanAllMode show ALL results (ignore risk filter) so "Hepsini Tara" always shows output
    if (!scanAllMode && minScoreFilter > 0 && Object.keys(scanResults).length > 0) {
      list = list.filter((s) => s.score >= minScoreFilter);
    }
    // Hide unscanned (—) rows when toggle is on
    if (showOnlyResults && Object.keys(scanResults).length > 0) {
      list = list.filter((s) => s.fromAPI);
    }
    return list;
  }, [sorted, searchTerm, minScoreFilter, scanResults, scanAllMode]);

  /* Add all scanned BUY/HQ signals to watchlist */
  const addAllSignalsToWatchlist = useCallback(async () => {
    const signals = filtered.filter((s) => s.fromAPI && (s.signal === "BUY" || s.highQuality));
    if (signals.length === 0) { toast.warning("Eklenecek BUY sinyali yok"); return; }
    try {
      const res = await apiFetch("/api/v1/watchlist/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: signals.map((s) => ({
            symbol: s.ticker,
            signal: s.signal,
            entry_price: s.price,
            stop_loss: s.stop,
            take_profit: s.tp1,
            score: s.score,
            regime: s.regime,
            sentiment: s.sentiment,
            risk_reward: s.rr,
            reason: s.reason,
            explanation: s.explanation,
          })),
        }),
      });
      if (!res.ok) throw new Error();
      toast.success(`${signals.length} sinyal watchlist'e eklendi`);
    } catch {
      toast.error("Toplu ekleme başarısız");
    }
  }, [filtered]);

  /* ── Scan function: calls real backend in batches ──────── */
  const runScan = useCallback(
    async (symbols: string[]) => {
      if (isScanning) return;

      abortRef.current = false;
      setIsScanning(true);
      setScanProgress(0);
      setScanTotal(symbols.length);
      setSelectedTicker(null);

      const results: Record<string, ScanResult> = {};
      let scanned = 0;

      try {
        // Build all batches upfront
        const batches: string[][] = [];
        for (let i = 0; i < symbols.length; i += BATCH_SIZE) {
          batches.push(symbols.slice(i, i + BATCH_SIZE));
        }

        // Fire in chunks of CONCURRENT_BATCHES; check abort between chunks
        for (let i = 0; i < batches.length; i += CONCURRENT_BATCHES) {
          if (abortRef.current) break;
          const chunk = batches.slice(i, i + CONCURRENT_BATCHES);
          await Promise.allSettled(
            chunk.map((batch) =>
              scanBatch(batch)
                .then((batchResult) => {
                  Object.assign(results, batchResult);
                  scanned += batch.length;
                  setScanProgress(scanned);
                  setScanResults({ ...results });
                })
                .catch((batchErr) => {
                  console.warn("Batch scan failed:", batchErr);
                  scanned += batch.length;
                  setScanProgress(scanned);
                })
            )
          );
        }

        setScanResults({ ...results });
        writeCache({ scanResults: { ...results }, activePresetId, scanAllMode });

        if (Object.keys(results).length === 0) {
          try {
            const hc = await fetch("/py-api/health");
            if (hc.ok) {
              toast.warning("Sonuç bulunamadı — semboller delisted veya veri yetersiz. Farklı bir preset deneyin.");
            } else {
              toast.error(`Backend yanıt vermiyor (HTTP ${hc.status}). Lütfen tekrar deneyin.`);
            }
          } catch {
            toast.error("Backend'e ulaşılamıyor. API çalışıyor mu?");
          }
        } else {
          const buyCount = Object.values(results).filter(
            r => r.high_quality_signal || r.entry_ok
          ).length;
          const topScore = Math.max(...Object.values(results).map(r => r.composite_score ?? 0));
          toast.success(
            `Scan complete — ${Object.keys(results).length} stocks · ${buyCount} buy signals · Top ${topScore}/100`
          );

          // Build top signals list (BUY + highest composite score)
          const allScanned = Object.values(results)
            .map((r) => apiResultToStock(r, 0))
            .sort((a, b) => b.score - a.score);
          const topSignals = allScanned.filter((s) => s.entryOk || s.highQuality).slice(0, 10);

          // Populate paper trading queue (high-quality signals with score ≥ 60)
          const queueItems = allScanned.filter((s) => s.highQuality && s.score >= 60).slice(0, 20);
          setPaperQueue(queueItems);

          // Build and save daily report
          const today = new Date().toISOString().slice(0, 10);
          const report = {
            date: today,
            scanned: Object.keys(results).length,
            buySignals: buyCount,
            topSignals,
          };
          setDailyReport(report);
          setReportSaved(false);
          setShowReportPanel(true);

          // Auto-save report to backend
          apiFetch("/api/v1/scan/daily-report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              date: today,
              universe_size: symbols.length,
              scanned: Object.keys(results).length,
              buy_signals: buyCount,
              top_signals: topSignals.slice(0, 10).map((s) => ({
                ticker: s.ticker,
                score: s.score,
                signal: s.signal,
                rr: s.rr,
                stop: s.stop,
                tp: s.tp1,
                reason: s.reason,
              })),
              paper_trades: queueItems.slice(0, 10).map((s) => ({
                ticker: s.ticker,
                entry: s.price,
                stop: s.stop,
                tp: s.tp1,
                score: s.score,
                reason: s.reason,
              })),
              notes: `Scan ran at ${new Date().toLocaleTimeString()}. ${scanAllMode ? "Full universe" : "Preset: " + (activePresetId ?? "")}`,
            }),
          })
            .then((r) => r.ok && setReportSaved(true))
            .catch(() => {});
        }
      } catch {
        toast.error("Scan failed. Please try again.");
      } finally {
        setIsScanning(false);
      }
    },
    [isScanning, scanAllMode, activePresetId],
  );

  /* Scan preset */
  const scanPreset = useCallback(() => {
    if (activePreset) {
      setScanAllMode(false);
      runScan(activePreset.symbols);
    }
  }, [activePreset, runScan]);

  /* Scan all stocks */
  const scanAll = useCallback(() => {
    const allSymbols = [...new Set(presets.flatMap((p) => p.symbols))];
    setScanAllMode(true);
    runScan(allSymbols);
  }, [presets, runScan]);

  /* Selected stock */
  const selected =
    filtered.find((s) => s.ticker === selectedTicker) ||
    stocks.find((s) => s.ticker === selectedTicker);

  /* Stats */
  const buyCount = filtered.filter((s) => s.signal === "BUY").length;
  const scannedCount = filtered.filter((s) => s.fromAPI).length;
  // Total scan results across all presets (for status bar)
  const totalScanResults = Object.keys(scanResults).length;
  const rrStocks = filtered.filter((s) => s.rr > 0);
  const avgRR =
    rrStocks.length > 0
      ? (rrStocks.reduce((a, s) => a + s.rr, 0) / rrStocks.length).toFixed(1)
      : "—";

  // Risk-adjusted summary stats (only from scanned stocks)
  const scannedStocks = filtered.filter((s) => s.fromAPI);
  const avgScore =
    scannedStocks.length > 0
      ? (scannedStocks.reduce((a, s) => a + s.score, 0) / scannedStocks.length).toFixed(1)
      : "0";
  const avgSharpe =
    scannedStocks.length > 0
      ? (scannedStocks.reduce((a, s) => a + s.sharpe, 0) / scannedStocks.length).toFixed(2)
      : "—";
  const avgMaxDD =
    scannedStocks.length > 0
      ? (scannedStocks.reduce((a, s) => a + s.maxDD, 0) / scannedStocks.length).toFixed(1) + "%"
      : "—";
  const avgAnnVol =
    scannedStocks.length > 0
      ? (scannedStocks.reduce((a, s) => a + s.annVol, 0) / scannedStocks.length).toFixed(1) + "%"
      : "—";
  const totalUniqueSymbols = useMemo(
    () => new Set(presets.flatMap((p) => p.symbols)).size,
    [presets],
  );

  const rowVirtualizer = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => tableParentRef.current,
    estimateSize: () => 44,
    overscan: 5,
  });

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2
          size={32}
          className="animate-spin"
          style={{ color: C.cyan }}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>
            AI Scanner
          </h1>
          <div className="flex items-center gap-2 mt-0.5">
            {systemBrier != null && <ConfidenceBadge brier={systemBrier} />}
            {macroData?.flags_active?.fred && (
              <MacroRegimeBanner
                regime={macroData.macro_regime as MacroRegime}
                vix={macroData.macro_vix}
                spread={macroData.macro_spread}
              />
            )}
            <p className="text-sm" style={{ color: C.text3 }}>
            {presets.length} preset · {totalUniqueSymbols.toLocaleString()}{" "}
            stocks
            {totalScanResults > 0 && (
              <span style={{ color: C.green }}>
                {" "}
                · {scanTotal > 0
                    ? `${scanTotal.toLocaleString()} tarandı · ${totalScanResults} sinyal`
                    : `${totalScanResults} sinyal`}
              </span>
            )}
            {alpacaConnected && alpacaAccount && (
              <span style={{ color: C.cyan }}>
                {" "}· <DollarSign size={11} className="inline -mt-0.5" /> Alpaca: ${alpacaAccount.cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            )}
            {!alpacaConnected && (
              <span style={{ color: C.text3 }}>
                {" "}· Alpaca: not connected
              </span>
            )}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportCSV(filtered)}
            className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs"
            style={{
              border: `1px solid ${C.border}`,
              backgroundColor: C.card,
              color: C.text2,
            }}
          >
            <Download size={14} /> Export CSV
          </button>
          {Object.keys(scanResults).length > 0 && (
            <button
              onClick={addAllSignalsToWatchlist}
              className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
              style={{
                border: `1px solid ${C.cyan}`,
                backgroundColor: "rgba(0,212,255,0.08)",
                color: C.cyan,
              }}
            >
              <Eye size={14} /> Sinyalleri Kaydet ({filtered.filter(s => s.fromAPI && (s.signal === "BUY" || s.highQuality)).length})
            </button>
          )}
          <button
            onClick={scanAll}            disabled={isScanning}
            className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
            style={{
              border: `1px solid ${isScanning ? C.border : C.green}`,
              backgroundColor: isScanning
                ? C.cardHover
                : "rgba(48,209,88,0.1)",
              color: isScanning ? C.text3 : C.green,
              cursor: isScanning ? "not-allowed" : "pointer",
            }}
          >
            <Globe size={14} />
            Scan All ({totalUniqueSymbols})
          </button>
          <button
            onClick={scanPreset}
            disabled={isScanning}
            className="flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold"
            style={{
              background: isScanning
                ? C.cardHover
                : `linear-gradient(to right, ${C.cyan}, ${C.blue})`,
              color: isScanning ? C.text2 : "#000",
              cursor: isScanning ? "not-allowed" : "pointer",
            }}
          >
            {isScanning ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            {isScanning
              ? `Scanning ${scanProgress}/${scanTotal}...`
              : `Run Scan (${activePreset?.symbols.length ?? 0})`}
          </button>
          {isScanning && (
            <button
              onClick={() => { abortRef.current = true; }}
              className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
              style={{
                border: `1px solid ${C.red}`,
                backgroundColor: "rgba(255,69,58,0.1)",
                color: C.red,
              }}
            >
              <Square size={12} /> Stop
            </button>
          )}
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
              backgroundColor:
                activeCategory === cat
                  ? `${categoryColors[cat] || C.cyan}20`
                  : C.card,
              color:
                activeCategory === cat
                  ? categoryColors[cat] || C.cyan
                  : C.text2,
              border:
                activeCategory === cat
                  ? `1px solid ${categoryColors[cat] || C.cyan}`
                  : "1px solid transparent",
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
            onClick={() => {
              setActivePresetId(p.id);
              setSelectedTicker(null);
              setSearchTerm("");
              setScanAllMode(false);
            }}
            className="shrink-0 rounded-xl px-3 py-2 text-xs font-medium transition-colors"
            style={{
              backgroundColor:
                activePresetId === p.id ? C.cardHover : C.card,
              color: activePresetId === p.id ? C.text1 : C.text2,
              border:
                activePresetId === p.id
                  ? `1px solid ${C.border}`
                  : "1px solid transparent",
            }}
          >
            <span className="mr-1.5">{p.icon}</span>
            {p.name}
            <span className="ml-1.5 opacity-50">({p.symbols.length})</span>
          </button>
        ))}
      </div>

      {/* Scan progress bar */}
      {isScanning && (
        <div
          className="rounded-xl p-3"
          style={{
            border: `1px solid ${C.border}`,
            backgroundColor: C.card,
          }}
        >
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span style={{ color: C.text2 }}>
              Scanning{" "}
              <span style={{ color: C.text1, fontWeight: 600 }}>
                {scanTotal === totalUniqueSymbols
                  ? "All Stocks"
                  : activePreset?.name}
              </span>
              ...
              <span style={{ color: C.text3, marginLeft: 8 }}>
                ({Math.floor(scanProgress / BATCH_SIZE)}/{Math.ceil(scanTotal / BATCH_SIZE)} batch)
              </span>
            </span>
            <span style={{ color: C.cyan, fontWeight: 600 }}>
              {scanTotal > 0
                ? Math.round((scanProgress / scanTotal) * 100)
                : 0}
              %
            </span>
          </div>
          <div
            className="h-1.5 overflow-hidden rounded-full"
            style={{ backgroundColor: C.primary }}
          >
            <div
              className="h-full rounded-full"
              style={{
                width: `${scanTotal > 0 ? (scanProgress / scanTotal) * 100 : 0}%`,
                background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`,
                transition: "width 0.3s ease-out",
              }}
            />
          </div>
        </div>
      )}

      {/* Summary metrics */}
      <div className="grid grid-cols-4 gap-3">
        {[
          {
            label: "Stocks",
            value: filtered.length.toString(),
            icon: BarChart3,
            color: C.text1,
          },
          {
            label: "Buy Signals",
            value: buyCount.toString(),
            icon: TrendingUp,
            color: C.green,
          },
          {
            label: "Avg Score",
            value: avgScore,
            icon: Brain,
            color: C.text1,
          },
          { label: "Avg R/R", value: avgRR, icon: Zap, color: C.cyan },
        ].map((m) => (
          <div
            key={m.label}
            className="rounded-xl px-4 py-3"
            style={{
              border: `1px solid ${C.border}`,
              backgroundColor: C.card,
            }}
          >
            <div className="flex items-center justify-between">
              <span style={{ fontSize: 11, color: C.text3 }}>{m.label}</span>
              <m.icon size={13} style={{ color: C.text3 }} />
            </div>
            <div
              className="mt-1 text-lg font-semibold"
              style={{ color: m.color }}
            >
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Risk-adjusted metrics row (shown once scan results are available) */}
      {scannedStocks.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              label: "Avg Sharpe",
              value: avgSharpe,
              sub: "Risk-adj return",
              color: parseFloat(avgSharpe) >= 1 ? C.green : parseFloat(avgSharpe) >= 0 ? C.cyan : C.red,
            },
            {
              label: "Avg MaxDD",
              value: avgMaxDD,
              sub: "Max peak-to-trough",
              color: parseFloat(avgMaxDD) < 15 ? C.green : parseFloat(avgMaxDD) < 30 ? C.yellow : C.red,
            },
            {
              label: "Avg Ann Vol",
              value: avgAnnVol,
              sub: "Annualised volatility",
              color: parseFloat(avgAnnVol) < 25 ? C.cyan : parseFloat(avgAnnVol) < 40 ? C.yellow : C.red,
            },
          ].map((m) => (
            <div
              key={m.label}
              className="rounded-xl px-4 py-3"
              style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
            >
              <div className="flex items-center justify-between">
                <span style={{ fontSize: 11, color: C.text3 }}>{m.label}</span>
                <span style={{ fontSize: 9, color: C.text3 }}>{m.sub}</span>
              </div>
              <div className="mt-1 text-lg font-semibold" style={{ color: m.color }}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: C.text3 }}
          />
          <input
            type="text"
            placeholder="Filter by ticker..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl py-2.5 pl-9 pr-4 text-sm outline-none"
            style={{
              border: `1px solid ${C.border}`,
              backgroundColor: C.card,
              color: C.text1,
            }}
          />
        </div>
        {minScoreFilter > 0 && Object.keys(scanResults).length > 0 && (
          <div className="rounded-xl px-3 py-2.5 text-xs whitespace-nowrap" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, color: C.text3 }}>
            Risk filter: <span style={{ color: C.cyan, fontWeight: 600 }}>≥{minScoreFilter}</span>
            <button onClick={() => setMinScoreFilter(0)} className="ml-2 underline" style={{ color: C.text3 }}>clear</button>
          </div>
        )}
        {Object.keys(scanResults).length > 0 && (
          <button
            onClick={() => setShowOnlyResults((v) => !v)}
            className="rounded-xl px-3 py-2.5 text-xs whitespace-nowrap transition-colors"
            style={{
              border: `1px solid ${showOnlyResults ? C.cyan : C.border}`,
              backgroundColor: showOnlyResults ? `${C.cyan}22` : C.card,
              color: showOnlyResults ? C.cyan : C.text3,
              fontWeight: showOnlyResults ? 600 : 400,
            }}
          >
            {showOnlyResults ? "✓ Sonuçları Göster" : "Sadece Sonuçlar"}
          </button>
        )}
      </div>

      {/* Daily Report Panel */}
      {dailyReport && (
        <div
          className="rounded-2xl overflow-hidden"
          style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
        >
          <button
            className="flex w-full items-center justify-between px-5 py-3"
            onClick={() => setShowReportPanel((v) => !v)}
          >
            <div className="flex items-center gap-2">
              <FileText size={14} style={{ color: C.cyan }} />
              <span className="text-xs font-semibold" style={{ color: C.text1 }}>
                Daily Report — {dailyReport.date}
              </span>
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-bold"
                style={{ backgroundColor: "rgba(48,209,88,0.15)", color: C.green }}
              >
                {dailyReport.buySignals} BUY
              </span>
              {reportSaved && (
                <span className="text-[10px]" style={{ color: C.text3 }}>● saved</span>
              )}
            </div>
            {showReportPanel ? <ChevronUp size={14} style={{ color: C.text3 }} /> : <ChevronDown size={14} style={{ color: C.text3 }} />}
          </button>

          {showReportPanel && (
            <div className="border-t px-5 pb-4 pt-3 space-y-3" style={{ borderColor: C.border }}>
              {/* Summary row */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Scanned", value: dailyReport.scanned, color: C.text1 },
                  { label: "Buy Signals", value: dailyReport.buySignals, color: C.green },
                  { label: "In Queue", value: paperQueue.length, color: C.cyan },
                ].map((m) => (
                  <div key={m.label} className="rounded-xl px-3 py-2" style={{ backgroundColor: C.primary }}>
                    <div className="text-[10px]" style={{ color: C.text3 }}>{m.label}</div>
                    <div className="text-lg font-bold" style={{ color: m.color }}>{m.value}</div>
                  </div>
                ))}
              </div>

              {/* Top signals table */}
              {dailyReport.topSignals.length > 0 && (
                <div>
                  <div className="mb-2 text-[11px] font-semibold" style={{ color: C.text2 }}>
                    Top Signals ({dailyReport.topSignals.length})
                  </div>
                  <div className="space-y-1">
                    {dailyReport.topSignals.slice(0, 8).map((s) => (
                      <div
                        key={s.ticker}
                        className="flex items-center justify-between rounded-lg px-3 py-2 text-xs cursor-pointer"
                        style={{ backgroundColor: C.primary }}
                        onClick={() => setSelectedTicker(s.ticker)}
                      >
                        <div className="flex items-center gap-3">
                          <span className="font-bold w-12" style={{ color: C.text1 }}>{s.ticker}</span>
                          <SignalBadge signal={s.signal} />
                          <span style={{ color: C.text3 }}>{s.explanation || s.reason}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span style={{ color: s.rr >= 2 ? C.green : C.text2 }}>{s.rr > 0 ? `R/R ${s.rr.toFixed(1)}x` : ""}</span>
                          <span className="font-bold" style={{ color: C.cyan }}>{s.score}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Paper Trading Queue */}
      {paperQueue.length > 0 && (
        <div
          className="rounded-2xl p-5 space-y-3"
          style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ClipboardList size={14} style={{ color: C.cyan }} />
              <span className="text-xs font-semibold" style={{ color: C.text1 }}>
                Paper Trading Queue
              </span>
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-bold"
                style={{ backgroundColor: "rgba(0,212,255,0.15)", color: C.cyan }}
              >
                {paperQueue.length} signals
              </span>
            </div>
            <span className="text-[10px]" style={{ color: C.text3 }}>
              High-quality signals ready to simulate
            </span>
          </div>
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {paperQueue.slice(0, 10).map((s) => (
              <div
                key={s.ticker}
                className="flex items-center justify-between rounded-xl px-3 py-2.5 text-xs cursor-pointer"
                style={{ border: `1px solid ${C.border}`, backgroundColor: C.primary }}
                onClick={() => setSelectedTicker(s.ticker)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold w-14" style={{ color: C.text1 }}>{s.ticker}</span>
                  <SignalBadge signal={s.signal} />
                </div>
                <div className="flex items-center gap-3">
                  <span style={{ color: C.text3 }}>SL ${s.stop > 0 ? s.stop.toFixed(2) : "—"}</span>
                  <span style={{ color: C.green }}>TP ${s.tp1 > 0 ? s.tp1.toFixed(2) : "—"}</span>
                  {alpacaConnected && (
                    <button
                      onClick={(e) => { e.stopPropagation(); placeAlpacaOrder(s); }}
                      className="rounded px-2 py-0.5 text-[10px] font-semibold"
                      style={{ backgroundColor: "rgba(48,209,88,0.2)", color: C.green }}
                    >
                      <ShoppingCart size={10} className="inline mr-0.5" />Buy
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results table + Detail panel */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Table */}
        <div
          className="overflow-hidden rounded-2xl lg:col-span-3"
          style={{
            border: `1px solid ${C.border}`,
            backgroundColor: C.card,
          }}
        >
          <div
            ref={tableParentRef}
            className="overflow-x-auto"
            style={{ maxHeight: 520, overflowY: "auto" }}
          >
            <table className="w-full text-left">
              <thead
                className="sticky top-0 z-10"
                style={{ backgroundColor: C.card }}
              >
                <tr
                  style={{
                    borderBottom: `1px solid ${C.border}`,
                    fontSize: 11,
                    color: C.text3,
                  }}
                >
                  {[
                    { key: "ticker", label: "Symbol" },
                    { key: "price", label: "Price" },
                    { key: "change", label: "Chg%" },
                    { key: "score", label: "Score" },
                    { key: "signal", label: "Signal" },
                    { key: "rr", label: "R/R" },
                    { key: "sharpe", label: "Sharpe" },
                    { key: "annVol", label: "Vol%" },
                    { key: "regime", label: "Regime" },
                  ].map((col) => (
                    <th
                      key={col.key}
                      className="px-4 py-3 font-medium cursor-pointer select-none hover:text-white transition-colors"
                      onClick={() => {
                        if (sortCol === col.key) {
                          setSortAsc(!sortAsc);
                        } else {
                          setSortCol(col.key);
                          setSortAsc(false);
                        }
                      }}
                    >
                      <span className="inline-flex items-center gap-1">
                        {col.label}
                        {sortCol === col.key ? (
                          <span style={{ fontSize: 9 }}>{sortAsc ? "▲" : "▼"}</span>
                        ) : (
                          <ArrowUpDown size={9} className="opacity-30" />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-8 text-center text-sm"
                      style={{ color: C.text3 }}
                    >
                      {Object.keys(scanResults).length === 0 ? (
                        "Taramaya başlamak için Run Scan veya Hepsini Tara'ya basın"
                      ) : searchTerm ? (
                        `"${searchTerm}" için sonuç bulunamadı`
                      ) : minScoreFilter > 0 && !scanAllMode && stocks.filter((s) => s.fromAPI).length > 0 ? (
                        <span>
                          {stocks.filter((s) => s.fromAPI).length} sonuç risk filtresi tarafından gizlendi (≥{minScoreFilter}){" "}
                          <button
                            onClick={() => setMinScoreFilter(0)}
                            className="ml-1 underline"
                            style={{ color: C.cyan }}
                          >
                            Filtreyi temizle
                          </button>
                        </span>
                      ) : (
                        "Bu taramada uygun hisse bulunamadı"
                      )}
                    </td>
                  </tr>
                ) : (
                  <>
                    {rowVirtualizer.getVirtualItems()[0]?.start > 0 && (
                      <tr>
                        <td
                          colSpan={7}
                          style={{ height: rowVirtualizer.getVirtualItems()[0].start }}
                        />
                      </tr>
                    )}
                    {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                      const s = filtered[virtualRow.index];
                      return (
                        <tr
                          key={s.ticker}
                          onClick={() => setSelectedTicker(s.ticker)}
                          className="cursor-pointer text-xs transition-colors"
                          style={{
                            borderBottom: `1px solid ${C.border}`,
                            backgroundColor:
                              selectedTicker === s.ticker
                                ? "rgba(0,212,255,0.08)"
                                : "transparent",
                          }}
                          onMouseEnter={(e) => {
                            if (selectedTicker !== s.ticker)
                              e.currentTarget.style.backgroundColor = C.cardHover;
                          }}
                          onMouseLeave={(e) => {
                            if (selectedTicker !== s.ticker)
                              e.currentTarget.style.backgroundColor = "transparent";
                          }}
                        >
                          <td
                            className="px-4 py-2.5 font-medium"
                            style={{ color: C.text1 }}
                          >
                            <div className="flex flex-col gap-0.5">
                              <span>
                                {s.ticker}
                                {s.fromAPI && (
                                  <span
                                    title="Scanned"
                                    style={{ color: C.green, marginLeft: 4 }}
                                  >
                                    ●
                                  </span>
                                )}
                              </span>
                              {s.fromAPI && (s.squeezeFactor > 0.35 || Math.abs(s.catalystFactor) >= 0.05) && (
                                <FactorBadgeRow
                                  data={{
                                    squeeze_factor: s.squeezeFactor,
                                    catalyst_factor: s.catalystFactor,
                                    macro_regime: (macroData?.macro_regime ?? "neutral") as MacroRegime,
                                    flags_active: macroData?.flags_active,
                                  }}
                                />
                              )}
                              {s.fromAPI && s.tier && s.tier !== "NONE" && (
                                <TierBadge tier={s.tier} />
                              )}
                            </div>
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{ color: C.text1 }}
                          >
                            {s.price > 0 ? `${currency}${s.price.toFixed(2)}` : "—"}
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{
                              color: !s.fromAPI && s.price === 0 ? C.text3 : s.change >= 0 ? C.green : C.red,
                            }}
                          >
                            {!s.fromAPI && s.price === 0
                              ? "—"
                              : `${s.change >= 0 ? "+" : ""}${s.change.toFixed(2)}%`}
                          </td>
                          <td className="px-4 py-2.5">
                            <div className="flex items-center gap-1.5">
                              <div
                                className="h-1 w-8 rounded-full"
                                style={{ backgroundColor: C.primary }}
                              >
                                <div
                                  className="h-1 rounded-full"
                                  style={{
                                    width: `${s.score}%`,
                                    backgroundColor:
                                      s.score >= 75
                                        ? C.green
                                        : s.score >= 50
                                          ? C.cyan
                                          : C.red,
                                  }}
                                />
                              </div>
                              <span style={{ color: C.text2 }}>{s.score}</span>
                            </div>
                          </td>
                          <td className="px-4 py-2.5">
                            <SignalBadge signal={s.signal} />
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{
                              color: s.rr >= 2 ? C.green : C.text2,
                            }}
                          >
                            {s.rr > 0 ? `${s.rr.toFixed(1)}x` : "—"}
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{
                              color: !s.fromAPI ? C.text3 : s.sharpe >= 1.5 ? C.green : s.sharpe >= 0.5 ? C.cyan : s.sharpe > 0 ? C.yellow : C.red,
                            }}
                          >
                            {s.fromAPI && s.sharpe !== 0 ? s.sharpe.toFixed(2) : "—"}
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{
                              color: !s.fromAPI ? C.text3 : s.annVol < 20 ? C.green : s.annVol < 35 ? C.yellow : C.red,
                            }}
                          >
                            {s.fromAPI && s.annVol > 0 ? `${s.annVol.toFixed(1)}%` : "—"}
                          </td>
                          <td
                            className="px-4 py-2.5"
                            style={{ color: C.text2 }}
                          >
                            {s.regime}
                          </td>
                        </tr>
                      );
                    })}
                    {(() => {
                      const items = rowVirtualizer.getVirtualItems();
                      const last = items[items.length - 1];
                      const bottom = last
                        ? rowVirtualizer.getTotalSize() - last.end
                        : 0;
                      return bottom > 0 ? (
                        <tr>
                          <td colSpan={7} style={{ height: bottom }} />
                        </tr>
                      ) : null;
                    })()}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="space-y-4 lg:col-span-2">
          {selected ? (
            <>
              <div
                className="rounded-2xl p-5"
                style={{
                  border: `1px solid ${C.border}`,
                  backgroundColor: C.card,
                }}
              >
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h2
                      className="text-lg font-bold"
                      style={{ color: C.text1 }}
                    >
                      {selected.ticker}
                    </h2>
                    <p className="text-xs" style={{ color: C.text3 }}>
                      {companyNames[selected.ticker] || ""}
                    </p>
                    <p className="text-[10px] mt-0.5" style={{ color: selected.fromAPI ? C.green : C.text3 }}>
                      {selected.fromAPI
                        ? "● Live scan data"
                        : "Awaiting scan"}
                    </p>
                  </div>
                  <SignalBadge signal={selected.signal} />
                </div>
                {selected.fromAPI && (selected.squeezeFactor > 0.1 || Math.abs(selected.catalystFactor) >= 0.05 || macroData?.flags_active?.fred) && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <FactorBadgeRow
                      data={{
                        squeeze_factor: selected.squeezeFactor,
                        catalyst_factor: selected.catalystFactor,
                        macro_regime: (macroData?.macro_regime ?? "neutral") as MacroRegime,
                        flags_active: macroData?.flags_active,
                      }}
                    />
                    {macroData?.flags_active?.fred && (
                      <span
                        title={`FRED Macro: ${macroData.macro_regime} | VIX ${macroData.macro_vix?.toFixed(1)} | Position ×${macroData.macro_multiplier}`}
                        style={{ fontSize: 10, color: C.text3, alignSelf: "center" }}
                      >
                        Macro ×{macroData.macro_multiplier?.toFixed(1)}
                      </span>
                    )}
                  </div>
                )}
                <div className="flex items-baseline gap-2 mt-2">
                  <span
                    className="text-2xl font-bold"
                    style={{ color: C.text1 }}
                  >
                    {currency}{selected.price > 0 ? selected.price.toFixed(2) : "—"}
                  </span>
                  <span
                    className="text-sm"
                    style={{
                      color: selected.change >= 0 ? C.green : C.red,
                    }}
                  >
                    {selected.change >= 0 ? "+" : ""}
                    {selected.change.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Price Chart */}
              <div
                className="rounded-2xl overflow-hidden"
                style={{
                  border: `1px solid ${C.border}`,
                  backgroundColor: C.card,
                }}
              >
                <div
                  className="px-4 pt-4 pb-1 text-xs font-semibold"
                  style={{ color: C.text2 }}
                >
                  Price Chart
                </div>
                <PriceChart symbol={selected.ticker} height={240} />
              </div>

              {/* AI Score & Indicators */}
              <div
                className="rounded-2xl p-5"
                style={{
                  border: `1px solid ${C.border}`,
                  backgroundColor: C.card,
                }}
              >
                <h3
                  className="mb-3 text-xs font-semibold"
                  style={{ color: C.text1 }}
                >
                  AI Score & Indicators
                </h3>
                <div className="mb-4">
                  <div className="mb-1 flex justify-between text-xs">
                    <span style={{ color: C.text3 }}>Composite Score</span>
                    <span
                      className="font-bold"
                      style={{ color: C.text1 }}
                    >
                      {selected.score}/100
                    </span>
                  </div>
                  <div
                    className="h-2 rounded-full"
                    style={{ backgroundColor: C.primary }}
                  >
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${selected.score}%`,
                        backgroundColor:
                          selected.score >= 75
                            ? C.green
                            : selected.score >= 50
                              ? C.cyan
                              : C.red,
                      }}
                    />
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  {[
                    { label: "Regime", value: selected.regime },
                    { label: "Momentum", value: selected.momentum },
                    { label: "Sentiment", value: selected.sentiment },
                    {
                      label: "Risk/Reward",
                      value:
                        selected.rr > 0
                          ? `${selected.rr.toFixed(1)}x`
                          : "—",
                    },
                    {
                      label: "ATR",
                      value:
                        selected.atr > 0
                          ? selected.atr.toFixed(3)
                          : "—",
                    },
                    {
                      label: "Volume Multiple",
                      value:
                        selected.volumeMultiple > 0
                          ? `${selected.volumeMultiple.toFixed(2)}x`
                          : "—",
                    },
                    {
                      label: "EMA Gap",
                      value:
                        selected.emaGap !== 0
                          ? `${selected.emaGap > 0 ? "+" : ""}${selected.emaGap.toFixed(2)}%`
                          : "—",
                    },
                  ].map((i) => (
                    <div key={i.label} className="flex justify-between">
                      <span style={{ color: C.text3 }}>{i.label}</span>
                      <span
                        className="font-medium"
                        style={{ color: C.text1 }}
                      >
                        {i.value}
                      </span>
                    </div>
                  ))}
                </div>
                {/* Status badges */}
                {selected.fromAPI && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {selected.trendStrength && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(48,209,88,0.1)",
                          color: C.green,
                        }}
                      >
                        Trend ✓
                      </span>
                    )}
                    {selected.volumeSpike && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(0,212,255,0.1)",
                          color: C.cyan,
                        }}
                      >
                        Volume Spike
                      </span>
                    )}
                    {selected.entryOk && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(48,209,88,0.1)",
                          color: C.green,
                        }}
                      >
                        Entry OK
                      </span>
                    )}
                    {selected.highQuality && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(255,214,10,0.1)",
                          color: C.yellow,
                        }}
                      >
                        ★ HQ Signal
                      </span>
                    )}
                    {selected.aligned && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(0,212,255,0.1)",
                          color: C.cyan,
                        }}
                      >
                        TF Aligned
                      </span>
                    )}
                    {selected.confluence && (
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px]"
                        style={{
                          backgroundColor: "rgba(191,90,242,0.1)",
                          color: "#bf5af2",
                        }}
                      >
                        Confluence
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Signal reason / explanation */}
              {selected.fromAPI && (selected.reason || selected.explanation) && (
                <div
                  className="rounded-xl px-3 py-2.5 text-xs"
                  style={{ backgroundColor: C.primary, border: `1px solid ${C.border}` }}
                >
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide" style={{ color: C.cyan }}>
                    Signal Analysis
                  </div>
                  {selected.reason && (
                    <p style={{ color: C.text1 }}>{selected.reason}</p>
                  )}
                  {selected.explanation && (
                    <p className="mt-1" style={{ color: C.text3 }}>{selected.explanation}</p>
                  )}
                </div>
              )}

              {/* Early Tier Panel */}
              {selected.fromAPI && selected.tier && selected.tier !== "NONE" && selected.tier !== "" && (
                <div
                  className="rounded-2xl p-4"
                  style={{
                    border: `1px solid ${TIER_CONFIG[selected.tier]?.color ?? C.border}44`,
                    backgroundColor: `${TIER_CONFIG[selected.tier]?.bg ?? "transparent"}`,
                  }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <TierBadge tier={selected.tier} />
                      <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: C.text3 }}>
                        Early Detection
                      </span>
                    </div>
                    <span
                      className="text-xs font-bold"
                      style={{ color: TIER_CONFIG[selected.tier]?.color }}
                    >
                      {Math.round(selected.tierScore * 100)}%
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="mb-3">
                    <div className="h-1 rounded-full" style={{ backgroundColor: C.primary }}>
                      <div
                        className="h-1 rounded-full transition-all"
                        style={{
                          width: `${selected.tierScore * 100}%`,
                          backgroundColor: TIER_CONFIG[selected.tier]?.color,
                        }}
                      />
                    </div>
                  </div>

                  {/* Tier ladder */}
                  <div className="mb-3 flex gap-1">
                    {["WATCH", "SETUP", "TRIGGER", "CONFIRM"].map((t) => {
                      const tiers = ["WATCH", "SETUP", "TRIGGER", "CONFIRM"];
                      const currentIdx = tiers.indexOf(selected.tier);
                      const thisIdx = tiers.indexOf(t);
                      const isActive = t === selected.tier;
                      const isPast = thisIdx < currentIdx;
                      return (
                        <div
                          key={t}
                          className="flex-1 rounded px-1 py-1 text-center"
                          style={{
                            backgroundColor: isActive
                              ? `${TIER_CONFIG[t]?.color}33`
                              : isPast
                              ? `${TIER_CONFIG[t]?.color}18`
                              : C.primary,
                            border: isActive
                              ? `1px solid ${TIER_CONFIG[t]?.color}99`
                              : "1px solid transparent",
                          }}
                        >
                          <span
                            style={{
                              fontSize: 8,
                              fontWeight: isActive ? 700 : 400,
                              color: isActive
                                ? TIER_CONFIG[t]?.color
                                : isPast
                                ? `${TIER_CONFIG[t]?.color}88`
                                : C.text3,
                            }}
                          >
                            {t}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-1.5 mb-3 text-xs">
                    <div className="rounded-lg px-2 py-1.5" style={{ backgroundColor: C.primary }}>
                      <div style={{ color: C.text3, fontSize: 9 }}>Size Fraction</div>
                      <div className="font-bold" style={{ color: C.text1 }}>
                        {selected.tierSizeFraction > 0 ? `${Math.round(selected.tierSizeFraction * 100)}%` : "0%"}
                      </div>
                    </div>
                    <div className="rounded-lg px-2 py-1.5" style={{ backgroundColor: C.primary }}>
                      <div style={{ color: C.text3, fontSize: 9 }}>Contraction</div>
                      <div
                        className="font-bold"
                        style={{ color: selected.contractionFactor >= 0.6 ? C.green : C.yellow }}
                      >
                        {selected.contractionFactor > 0 ? selected.contractionFactor.toFixed(2) : "—"}
                      </div>
                    </div>
                    <div className="rounded-lg px-2 py-1.5" style={{ backgroundColor: C.primary }}>
                      <div style={{ color: C.text3, fontSize: 9 }}>RVOL Accel</div>
                      <div
                        className="font-bold"
                        style={{ color: selected.rvolAcceleration >= 0.3 ? C.cyan : C.text2 }}
                      >
                        {selected.rvolAcceleration > 0 ? `+${selected.rvolAcceleration.toFixed(2)}` : "—"}
                      </div>
                    </div>
                  </div>

                  {/* Reasons */}
                  {selected.tierReasons.length > 0 && (
                    <div className="space-y-1">
                      {selected.tierReasons.map((reason, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-1.5 text-[10px]"
                          style={{ color: C.text2 }}
                        >
                          <span style={{ color: TIER_CONFIG[selected.tier]?.color, flexShrink: 0 }}>›</span>
                          {reason}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Fundamentals Panel (EODHD) */}
              {selected.fromAPI && selected.fundamentalScore > 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xs font-semibold" style={{ color: C.text1 }}>
                      Fundamentals
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-semibold"
                        style={{
                          backgroundColor:
                            selected.fundamentalQuality === "high"
                              ? "rgba(48,209,88,0.15)"
                              : selected.fundamentalQuality === "medium"
                              ? "rgba(255,214,10,0.15)"
                              : "rgba(255,255,255,0.08)",
                          color:
                            selected.fundamentalQuality === "high"
                              ? C.green
                              : selected.fundamentalQuality === "medium"
                              ? C.yellow
                              : C.text3,
                        }}
                      >
                        {selected.fundamentalQuality?.toUpperCase()} DATA
                      </span>
                      <span
                        className="text-sm font-bold"
                        style={{
                          color:
                            selected.fundamentalScore >= 65
                              ? C.green
                              : selected.fundamentalScore >= 45
                              ? C.cyan
                              : C.red,
                        }}
                      >
                        {selected.fundamentalScore}/100
                      </span>
                    </div>
                  </div>

                  {/* Score bar */}
                  <div className="mb-4 h-1.5 rounded-full" style={{ backgroundColor: C.primary }}>
                    <div
                      className="h-1.5 rounded-full"
                      style={{
                        width: `${selected.fundamentalScore}%`,
                        backgroundColor:
                          selected.fundamentalScore >= 65
                            ? C.green
                            : selected.fundamentalScore >= 45
                            ? C.cyan
                            : C.red,
                      }}
                    />
                  </div>

                  {/* Metrics grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      {
                        label: "P/E (Trailing)",
                        value: selected.peRatio != null ? selected.peRatio.toFixed(1) : "—",
                        color:
                          selected.peRatio == null
                            ? C.text3
                            : selected.peRatio < 15
                            ? C.green
                            : selected.peRatio < 30
                            ? C.cyan
                            : C.red,
                      },
                      {
                        label: "P/E (Forward)",
                        value: selected.forwardPE != null ? selected.forwardPE.toFixed(1) : "—",
                        color:
                          selected.forwardPE == null
                            ? C.text3
                            : selected.forwardPE < 20
                            ? C.green
                            : selected.forwardPE < 35
                            ? C.cyan
                            : C.red,
                      },
                      {
                        label: "EPS Büyüme YoY",
                        value:
                          selected.epsGrowth != null
                            ? `${selected.epsGrowth > 0 ? "+" : ""}${(selected.epsGrowth * 100).toFixed(1)}%`
                            : "—",
                        color:
                          selected.epsGrowth == null
                            ? C.text3
                            : selected.epsGrowth > 0.15
                            ? C.green
                            : selected.epsGrowth > 0
                            ? C.cyan
                            : C.red,
                      },
                      {
                        label: "Gelir Büyüme YoY",
                        value:
                          selected.revenueGrowth != null
                            ? `${selected.revenueGrowth > 0 ? "+" : ""}${(selected.revenueGrowth * 100).toFixed(1)}%`
                            : "—",
                        color:
                          selected.revenueGrowth == null
                            ? C.text3
                            : selected.revenueGrowth > 0.1
                            ? C.green
                            : selected.revenueGrowth > 0
                            ? C.cyan
                            : C.red,
                      },
                      {
                        label: "Kâr Marjı",
                        value:
                          selected.profitMargin != null
                            ? `${(selected.profitMargin * 100).toFixed(1)}%`
                            : "—",
                        color:
                          selected.profitMargin == null
                            ? C.text3
                            : selected.profitMargin > 0.2
                            ? C.green
                            : selected.profitMargin > 0
                            ? C.cyan
                            : C.red,
                      },
                      {
                        label: "Özsermaye Getirisi",
                        value:
                          selected.returnOnEquity != null
                            ? `${(selected.returnOnEquity * 100).toFixed(1)}%`
                            : "—",
                        color:
                          selected.returnOnEquity == null
                            ? C.text3
                            : selected.returnOnEquity > 0.15
                            ? C.green
                            : selected.returnOnEquity > 0
                            ? C.cyan
                            : C.red,
                      },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="rounded-lg px-2.5 py-2"
                        style={{ backgroundColor: C.primary }}
                      >
                        <div style={{ color: C.text3, fontSize: 9 }}>{item.label}</div>
                        <div className="mt-0.5 font-bold" style={{ color: item.color }}>
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Analyst consensus */}
                  {selected.analystTarget != null && selected.analystRating != null && (
                    <div className="mt-2 rounded-lg px-2.5 py-2.5" style={{ backgroundColor: C.primary }}>
                      <div className="flex items-center justify-between text-xs">
                        <div>
                          <div style={{ color: C.text3, fontSize: 9 }}>Analist Konsensüs</div>
                          <div
                            className="mt-0.5 font-bold"
                            style={{
                              color:
                                selected.analystRating >= 4.0
                                  ? C.green
                                  : selected.analystRating >= 3.0
                                  ? C.cyan
                                  : C.red,
                            }}
                          >
                            {selected.analystRating >= 4.5
                              ? "Güçlü Al"
                              : selected.analystRating >= 4.0
                              ? "Al"
                              : selected.analystRating >= 3.0
                              ? "Tut"
                              : selected.analystRating >= 2.0
                              ? "Sat"
                              : "Güçlü Sat"}{" "}
                            <span style={{ color: C.text3, fontWeight: 400 }}>
                              ({selected.analystRating.toFixed(2)}/5)
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div style={{ color: C.text3, fontSize: 9 }}>Hedef Fiyat</div>
                          <div className="mt-0.5 font-bold" style={{ color: C.text1 }}>
                            ${selected.analystTarget.toFixed(2)}
                          </div>
                          {selected.price > 0 && (
                            <div
                              style={{
                                fontSize: 9,
                                color:
                                  selected.analystTarget > selected.price ? C.green : C.red,
                              }}
                            >
                              {selected.analystTarget > selected.price ? "+" : ""}
                              {(
                                ((selected.analystTarget - selected.price) / selected.price) *
                                100
                              ).toFixed(1)}
                              % potansiyel
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Son Haberler Paneli (EODHD Faz 4) */}
              {selected.fromAPI && selected.newsCount > 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xs font-semibold" style={{ color: C.text1 }}>
                      Son Haberler
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-semibold"
                        style={{
                          backgroundColor:
                            selected.newsSentiment > 0.15
                              ? "rgba(48,209,88,0.15)"
                              : selected.newsSentiment < -0.15
                              ? "rgba(255,69,58,0.15)"
                              : "rgba(255,255,255,0.08)",
                          color:
                            selected.newsSentiment > 0.15
                              ? C.green
                              : selected.newsSentiment < -0.15
                              ? C.red
                              : C.text3,
                        }}
                      >
                        {selected.newsSentiment > 0.15
                          ? "BULLISH"
                          : selected.newsSentiment < -0.15
                          ? "BEARISH"
                          : "NÖTR"}
                      </span>
                      <span style={{ color: C.text3, fontSize: 10 }}>
                        {selected.newsCount} haber (7g)
                      </span>
                    </div>
                  </div>

                  {/* Sentiment çubuğu */}
                  <div className="relative mb-4 h-1.5 rounded-full" style={{ backgroundColor: C.primary }}>
                    {/* Merkez çizgisi */}
                    <div
                      className="absolute top-0 h-1.5 w-px"
                      style={{ left: "50%", backgroundColor: C.border }}
                    />
                    {/* Sentiment dolgusu */}
                    {selected.newsSentiment >= 0 ? (
                      <div
                        className="absolute h-1.5 rounded-r-full"
                        style={{
                          left: "50%",
                          width: `${Math.min(50, selected.newsSentiment * 50)}%`,
                          backgroundColor: C.green,
                        }}
                      />
                    ) : (
                      <div
                        className="absolute h-1.5 rounded-l-full"
                        style={{
                          right: "50%",
                          width: `${Math.min(50, Math.abs(selected.newsSentiment) * 50)}%`,
                          backgroundColor: C.red,
                        }}
                      />
                    )}
                  </div>
                  <div
                    className="mb-3 flex justify-between text-[9px]"
                    style={{ color: C.text3 }}
                  >
                    <span>Çok Negatif</span>
                    <span>Sentiment: {selected.newsSentiment > 0 ? "+" : ""}{(selected.newsSentiment * 100).toFixed(0)}%</span>
                    <span>Çok Pozitif</span>
                  </div>

                  {/* Başlıklar */}
                  {selected.topHeadlines.length > 0 && (
                    <div className="space-y-1.5">
                      {selected.topHeadlines.map((headline, i) => (
                        <div
                          key={i}
                          className="rounded-lg px-2.5 py-2 text-[10px] leading-snug"
                          style={{ backgroundColor: C.primary, color: C.text2 }}
                        >
                          <span
                            className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full"
                            style={{
                              backgroundColor:
                                selected.newsSentiment > 0.15
                                  ? C.green
                                  : selected.newsSentiment < -0.15
                                  ? C.red
                                  : C.text3,
                              verticalAlign: "middle",
                            }}
                          />
                          {headline}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Risk Metrics */}
              {selected.fromAPI && selected.sharpe !== 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xs font-semibold" style={{ color: C.text1 }}>
                      Risk Metrics
                    </h3>
                    <span
                      className="rounded-full px-2 py-0.5 text-[9px] font-semibold"
                      style={{
                        backgroundColor: selected.riskDataQuality === "high"
                          ? "rgba(48,209,88,0.15)" : selected.riskDataQuality === "medium"
                          ? "rgba(255,214,10,0.15)" : "rgba(255,69,58,0.15)",
                        color: selected.riskDataQuality === "high" ? C.green
                          : selected.riskDataQuality === "medium" ? C.yellow : C.red,
                      }}
                    >
                      {selected.riskDataQuality?.toUpperCase()} DATA
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      { label: "Sharpe Ratio", value: selected.sharpe.toFixed(2), color: selected.sharpe >= 1.5 ? C.green : selected.sharpe >= 0.5 ? C.cyan : selected.sharpe > 0 ? C.yellow : C.red },
                      { label: "Sortino Ratio", value: selected.sortino.toFixed(2), color: selected.sortino >= 2 ? C.green : selected.sortino >= 1 ? C.cyan : C.yellow },
                      { label: "Calmar Ratio", value: selected.maxDD > 0 ? selected.sortino.toFixed(2) : "—", color: C.text1 },
                      { label: "Max Drawdown", value: selected.maxDD > 0 ? `${selected.maxDD.toFixed(1)}%` : "—", color: selected.maxDD < 15 ? C.green : selected.maxDD < 30 ? C.yellow : C.red },
                      { label: "Ann. Volatility", value: selected.annVol > 0 ? `${selected.annVol.toFixed(1)}%` : "—", color: selected.annVol < 20 ? C.green : selected.annVol < 35 ? C.yellow : C.red },
                      { label: "Ann. Return", value: selected.annReturn !== 0 ? `${selected.annReturn > 0 ? "+" : ""}${selected.annReturn.toFixed(1)}%` : "—", color: selected.annReturn >= 0 ? C.green : C.red },
                    ].map((item) => (
                      <div key={item.label} className="rounded-lg px-2.5 py-2" style={{ backgroundColor: C.primary }}>
                        <div style={{ color: C.text3, fontSize: 9 }}>{item.label}</div>
                        <div className="mt-0.5 font-bold" style={{ color: item.color }}>{item.value}</div>
                      </div>
                    ))}
                  </div>
                  {selected.evPerTrade !== 0 && (
                    <div className="mt-2 rounded-lg px-2.5 py-2 text-xs" style={{ backgroundColor: C.primary }}>
                      <div style={{ color: C.text3, fontSize: 9 }}>Expected Value / Trade</div>
                      <div className="mt-0.5 font-bold" style={{ color: selected.evPerTrade > 0 ? C.green : C.red }}>
                        {selected.evPerTrade > 0 ? "+" : ""}{selected.evPerTrade.toFixed(4)}% per period
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Trade Plan */}
              {selected.fromAPI && selected.stop > 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{
                    border: `1px solid ${C.border}`,
                    backgroundColor: C.card,
                  }}
                >
                  <h3
                    className="mb-3 text-xs font-semibold"
                    style={{ color: C.text1 }}
                  >
                    Trade Plan
                  </h3>
                  <div className="space-y-2">
                    <div
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-xs"
                      style={{ backgroundColor: "rgba(255,69,58,0.08)" }}
                    >
                      <span style={{ color: C.red }}>Stop Loss</span>
                      <span
                        className="font-bold"
                        style={{ color: C.red }}
                      >
                        ${selected.stop.toFixed(2)}
                      </span>
                    </div>
                    <div
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-xs"
                      style={{ backgroundColor: "rgba(48,209,88,0.08)" }}
                    >
                      <span style={{ color: C.green }}>Take Profit</span>
                      <span
                        className="font-bold"
                        style={{ color: C.green }}
                      >
                        ${selected.tp1.toFixed(2)}
                      </span>
                    </div>
                    {/* Dynamic position sizing (Task 3) */}
                    {selected.fromAPI && selected.dynShares > 0 ? (
                      <>
                        <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(0,212,255,0.08)", border: `1px solid rgba(0,212,255,0.2)` }}>
                          <div className="flex items-center justify-between mb-1">
                            <span style={{ color: C.cyan, fontWeight: 600 }}>Dynamic Size</span>
                            <span className="text-[9px] rounded px-1.5 py-0.5" style={{ backgroundColor: "rgba(0,212,255,0.15)", color: C.cyan }}>
                              {selected.dynRegimeScale !== 1.0 ? `×${selected.dynRegimeScale.toFixed(2)} regime` : "neutral regime"}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-1.5 mt-1">
                            <div>
                              <div style={{ color: C.text3, fontSize: 9 }}>Shares</div>
                              <div className="font-bold" style={{ color: C.text1 }}>{selected.dynShares.toLocaleString()}</div>
                            </div>
                            <div>
                              <div style={{ color: C.text3, fontSize: 9 }}>Risk %</div>
                              <div className="font-bold" style={{ color: selected.dynRiskPct <= 1 ? C.green : selected.dynRiskPct <= 2 ? C.yellow : C.red }}>
                                {selected.dynRiskPct.toFixed(2)}%
                              </div>
                            </div>
                            <div>
                              <div style={{ color: C.text3, fontSize: 9 }}>Position %</div>
                              <div className="font-bold" style={{ color: C.text1 }}>{selected.dynPositionPct.toFixed(1)}%</div>
                            </div>
                            <div>
                              <div style={{ color: C.text3, fontSize: 9 }}>Kelly %</div>
                              <div className="font-bold" style={{ color: C.text2 }}>{selected.dynKellyPct.toFixed(1)}%</div>
                            </div>
                          </div>
                          {!selected.dynPortfolioOk && (
                            <div className="mt-1.5 text-[10px] font-semibold" style={{ color: C.red }}>
                              ⚠ Portfolio heat limit reached
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <>
                        <div
                          className="flex items-center justify-between rounded-lg px-3 py-2 text-xs"
                          style={{ backgroundColor: C.cardHover }}
                        >
                          <span style={{ color: C.text3 }}>Position Size</span>
                          <span
                            className="font-medium"
                            style={{ color: C.text1 }}
                          >
                            ${selected.positionSize.toLocaleString()}
                          </span>
                        </div>
                        <div
                          className="flex items-center justify-between rounded-lg px-3 py-2 text-xs"
                          style={{ backgroundColor: C.cardHover }}
                        >
                          <span style={{ color: C.text3 }}>Kelly Fraction</span>
                          <span
                            className="font-medium"
                            style={{ color: C.text1 }}
                          >
                            {(selected.kellyFraction * 100).toFixed(0)}%
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                  {/* Buy on Alpaca button */}
                  {alpacaConnected && (
                    <button
                      onClick={() => placeAlpacaOrder(selected)}
                      disabled={orderPending}
                      className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-semibold transition-colors"
                      style={{
                        background: orderPending ? C.cardHover : "rgba(48,209,88,0.15)",
                        border: `1px solid ${orderPending ? C.border : C.green}`,
                        color: orderPending ? C.text3 : C.green,
                        cursor: orderPending ? "not-allowed" : "pointer",
                      }}
                    >
                      {orderPending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <ShoppingCart size={14} />
                      )}
                      {orderPending ? "Sending..." : "Buy on Alpaca (Paper)"}
                    </button>
                  )}
                </div>
              )}

              <button
                onClick={() => setExplainOpen(true)}
                className="flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold transition-opacity hover:opacity-80"
                style={{
                  background: `linear-gradient(to right, #bf5af2, #6e40c9)`,
                  color: "#fff",
                }}
              >
                <Brain size={16} /> Hızlı AI Analiz
              </button>

              {selected.fromAPI && (
                <button
                  onClick={() => addToWatchlist(selected)}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold"
                  style={{
                    background: "rgba(0,212,255,0.1)",
                    border: `1px solid ${C.cyan}`,
                    color: C.cyan,
                  }}
                >
                  <Eye size={16} /> Watchlist&apos;e Ekle
                </button>
              )}

              <Link
                href={`/dashboard/analysis?symbol=${selected.ticker}`}
                className="flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold"
                style={{
                  background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`,
                  color: "#000",
                }}
                onClick={() => {
                  const result = scanResults[selected.ticker];
                  if (result) {
                    try {
                      sessionStorage.setItem(
                        `finpilot_scan_${selected.ticker}`,
                        JSON.stringify({ data: result, ts: Date.now() }),
                      );
                    } catch {}
                  }
                }}
              >
                <Brain size={16} /> Full AI Analysis{" "}
                <ArrowUpRight size={14} />
              </Link>
            </>
          ) : (
            <div
              className="flex h-64 flex-col items-center justify-center gap-2 rounded-2xl text-sm"
              style={{
                border: `1px dashed ${C.border}`,
                color: C.text3,
              }}
            >
              <Brain size={24} />
              Select a stock or Run Scan
            </div>
          )}
        </div>
      </div>

      {explainOpen && selectedTicker && (
        <ExplainPanel
          symbol={selectedTicker}
          onClose={() => setExplainOpen(false)}
        />
      )}
    </div>
  );
}
