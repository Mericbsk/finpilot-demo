"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
  Eye,
  Trash2,
  Target,
  CheckCircle2,
  XCircle,
  Clock,
  BookmarkX,
} from "lucide-react";
import { C, hashStr, seededRandom, genStock, companyNames, genSparkline, withLivePrice } from "@/lib/stockData";
import { useStockPrices } from "@/lib/useStockPrices";
import { getCurrencySymbol } from "@/lib/userSettings";
import DemoBanner from "@/components/DemoBanner";

/* ══════════════════════════════════════════════════════════════
   SINYAL TAKİP — types & helpers
══════════════════════════════════════════════════════════════ */
interface TrackedSignal {
  symbol: string;
  signal: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  score: number;
  regime: string;
  sentiment: string;
  risk_reward: number;
  reason: string;
  explanation: string;
  added_at: string;
  current_price: number;
  change_pct: number;
  pnl_pct: number;
  status: "On Track" | "Stop Hit" | "TP Hit" | "Watching" | "Pending";
}

function StatusBadge({ status }: { status: TrackedSignal["status"] }) {
  const cfg: Record<TrackedSignal["status"], { label: string; icon: React.ReactNode; bg: string; color: string }> = {
    "On Track": { label: "On Track", icon: <CheckCircle2 size={11} />, bg: "rgba(48,209,88,0.15)", color: C.green },
    "TP Hit":   { label: "TP Hit",   icon: <Target size={11} />,       bg: "rgba(255,214,10,0.15)", color: C.yellow },
    "Stop Hit": { label: "Stop Hit", icon: <XCircle size={11} />,      bg: "rgba(255,69,58,0.15)",  color: C.red },
    "Watching": { label: "Watching", icon: <Eye size={11} />,           bg: "rgba(0,212,255,0.12)",  color: C.cyan },
    "Pending":  { label: "Pending",  icon: <Clock size={11} />,         bg: "rgba(161,161,166,0.12)",color: C.text2 },
  };
  const c = cfg[status] ?? cfg["Pending"];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px", borderRadius: 6, fontSize: 11, fontWeight: 600, background: c.bg, color: c.color }}>
      {c.icon}{c.label}
    </span>
  );
}

function PriceProgressBar({ item }: { item: TrackedSignal }) {
  const min = Math.min(item.stop_loss, item.current_price || item.entry_price, item.entry_price) * 0.995;
  const max = Math.max(item.take_profit, item.current_price || item.entry_price, item.entry_price) * 1.005;
  const range = max - min;
  if (range <= 0) return null;
  const pct = (v: number) => Math.max(0, Math.min(100, ((v - min) / range) * 100));
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ position: "relative", height: 6, background: "rgba(255,255,255,0.08)", borderRadius: 3 }}>
        <div style={{ position: "absolute", left: `${pct(item.stop_loss)}%`, width: `${pct(item.entry_price) - pct(item.stop_loss)}%`, height: "100%", background: `${C.red}40`, borderRadius: 3 }} />
        <div style={{ position: "absolute", left: `${pct(item.entry_price)}%`, width: `${pct(item.take_profit) - pct(item.entry_price)}%`, height: "100%", background: `${C.green}40`, borderRadius: 3 }} />
        <div style={{ position: "absolute", left: `${pct(item.stop_loss)}%`, top: -4, width: 2, height: 14, background: C.red }} title={`Stop: $${item.stop_loss}`} />
        <div style={{ position: "absolute", left: `${pct(item.entry_price)}%`, top: -4, width: 2, height: 14, background: C.yellow }} title={`Entry: $${item.entry_price}`} />
        <div style={{ position: "absolute", left: `${pct(item.take_profit)}%`, top: -4, width: 2, height: 14, background: C.green }} title={`TP: $${item.take_profit}`} />
        {item.current_price > 0 && (
          <div style={{ position: "absolute", left: `calc(${pct(item.current_price)}% - 5px)`, top: -3, width: 12, height: 12, borderRadius: "50%", background: C.cyan, border: "2px solid #000", zIndex: 2 }} title={`Now: $${item.current_price}`} />
        )}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5, fontSize: 10, color: C.text3 }}>
        <span style={{ color: C.red }}>STOP ${item.stop_loss.toFixed(2)}</span>
        <span style={{ color: C.yellow }}>GİRİŞ ${item.entry_price.toFixed(2)}</span>
        <span style={{ color: C.cyan }}>ŞİMDİ ${item.current_price > 0 ? item.current_price.toFixed(2) : "—"}</span>
        <span style={{ color: C.green }}>TP ${item.take_profit.toFixed(2)}</span>
      </div>
    </div>
  );
}

function SinyalTakipTab() {
  const [items, setItems] = useState<TrackedSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchList = useCallback(async (silent = false) => {
    if (!silent) setLoading(true); else setRefreshing(true);
    try {
      const res = await fetch("/py-api/watchlist");
      if (!res.ok) throw new Error();
      const data = await res.json();
      setItems(data.items ?? []);
      setRefreshedAt(data.refreshed_at ?? null);
    } catch { /* silent */ }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    fetchList();
    const id = setInterval(() => fetchList(true), 60_000);
    return () => clearInterval(id);
  }, [fetchList]);

  const removeItem = async (symbol: string) => {
    try {
      await fetch(`/py-api/watchlist/${symbol}`, { method: "DELETE" });
      setItems((prev) => prev.filter((i) => i.symbol !== symbol));
    } catch { /* silent */ }
  };

  const clearAll = async () => {
    if (!confirm("Tüm sinyal kaydı silinsin mi?")) return;
    await fetch("/py-api/watchlist/clear", { method: "DELETE" });
    setItems([]);
  };

  const onTrack  = items.filter((i) => i.status === "On Track").length;
  const tpHit    = items.filter((i) => i.status === "TP Hit").length;
  const stopHit  = items.filter((i) => i.status === "Stop Hit").length;
  const avgPnl   = items.length > 0 ? items.reduce((s, i) => s + i.pnl_pct, 0) / items.length : 0;

  if (loading) return <div style={{ textAlign: "center", padding: 60, color: C.text2 }}>Yükleniyor…</div>;

  if (items.length === 0) return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: C.text3, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
      <BookmarkX size={44} style={{ opacity: 0.4 }} />
      <p style={{ fontSize: 15, color: C.text2 }}>Sinyal takip listesi boş</p>
      <p style={{ fontSize: 12 }}>
        <strong style={{ color: C.cyan }}>Scanner</strong> sayfasında tarama yaptıktan sonra
        satır başındaki <strong style={{ color: C.cyan }}>+</strong> ikonuna veya
        <strong style={{ color: C.cyan }}> Watchlist'e Ekle</strong> butonuna basın.
      </p>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Stats + actions */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        {[
          { label: "TOPLAM",    value: items.length, color: C.text1 },
          { label: "ON TRACK",  value: onTrack,      color: C.green },
          { label: "TP HIT",    value: tpHit,        color: C.yellow },
          { label: "STOP HIT",  value: stopHit,      color: C.red },
          { label: "ORT. P&L",  value: `${avgPnl >= 0 ? "+" : ""}${avgPnl.toFixed(2)}%`, color: avgPnl >= 0 ? C.green : C.red },
        ].map((s) => (
          <div key={s.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 16px" }}>
            <div style={{ fontSize: 10, color: C.text3 }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {refreshedAt && <span style={{ fontSize: 10, color: C.text3, alignSelf: "center" }}>{new Date(refreshedAt).toLocaleTimeString("tr-TR")}</span>}
          <button onClick={() => fetchList(true)} disabled={refreshing} style={{ display: "flex", alignItems: "center", gap: 5, borderRadius: 10, border: `1px solid ${C.border}`, background: C.card, padding: "6px 12px", fontSize: 12, color: C.cyan, cursor: "pointer", fontWeight: 600 }}>
            <RefreshCw size={13} style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} /> Yenile
          </button>
          <button onClick={clearAll} style={{ display: "flex", alignItems: "center", gap: 5, borderRadius: 10, border: "1px solid rgba(255,69,58,0.3)", background: "rgba(255,69,58,0.08)", padding: "6px 12px", fontSize: 12, color: C.red, cursor: "pointer", fontWeight: 600 }}>
            <Trash2 size={13} /> Temizle
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: C.primary }}>
                {["HİSSE", "SİNYAL", "DURUM", "GİRİŞ", "GÜNCEL", "P&L", "DEĞ%", "STOP", "TP", "SKOR", "EKLENDİ", ""].map((h) => (
                  <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: C.text3, fontSize: 11, fontWeight: 600, borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <>
                  <tr
                    key={item.symbol}
                    style={{ borderBottom: `1px solid ${C.border}`, background: item.status === "Stop Hit" ? "rgba(255,69,58,0.04)" : item.status === "TP Hit" ? "rgba(255,214,10,0.04)" : "transparent", cursor: "pointer" }}
                    onClick={() => setExpanded(expanded === item.symbol ? null : item.symbol)}
                  >
                    <td style={{ padding: "11px 12px" }}>
                      <div style={{ fontWeight: 700 }}>{item.symbol}</div>
                      <div style={{ fontSize: 10, color: C.text3 }}>{companyNames[item.symbol] ?? ""}</div>
                    </td>
                    <td style={{ padding: "11px 12px" }}>
                      <span style={{ padding: "2px 8px", borderRadius: 5, fontSize: 11, fontWeight: 700, background: item.signal === "BUY" ? "rgba(48,209,88,0.15)" : item.signal === "SELL" ? "rgba(255,69,58,0.15)" : "rgba(255,214,10,0.15)", color: item.signal === "BUY" ? C.green : item.signal === "SELL" ? C.red : C.yellow }}>{item.signal}</span>
                    </td>
                    <td style={{ padding: "11px 12px" }}><StatusBadge status={item.status} /></td>
                    <td style={{ padding: "11px 12px", fontWeight: 600 }}>{item.entry_price > 0 ? `$${item.entry_price.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "11px 12px", fontWeight: 600 }}>{item.current_price > 0 ? `$${item.current_price.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "11px 12px" }}>
                      {item.pnl_pct !== 0 ? (
                        <span style={{ color: item.pnl_pct > 0 ? C.green : C.red, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 3 }}>
                          {item.pnl_pct > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                          {item.pnl_pct > 0 ? "+" : ""}{item.pnl_pct.toFixed(2)}%
                        </span>
                      ) : <span style={{ color: C.text3 }}>—</span>}
                    </td>
                    <td style={{ padding: "11px 12px", color: item.change_pct >= 0 ? C.green : C.red, fontWeight: 500 }}>{item.change_pct >= 0 ? "+" : ""}{item.change_pct.toFixed(2)}%</td>
                    <td style={{ padding: "11px 12px", color: C.red, fontSize: 12 }}>{item.stop_loss > 0 ? `$${item.stop_loss.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "11px 12px", color: C.green, fontSize: 12 }}>{item.take_profit > 0 ? `$${item.take_profit.toFixed(2)}` : "—"}</td>
                    <td style={{ padding: "11px 12px", fontWeight: 700, color: item.score >= 70 ? C.green : item.score >= 50 ? C.yellow : C.text2 }}>{item.score > 0 ? Math.round(item.score) : "—"}</td>
                    <td style={{ padding: "11px 12px", color: C.text3, fontSize: 11, whiteSpace: "nowrap" }}>{new Date(item.added_at).toLocaleString("tr-TR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</td>
                    <td style={{ padding: "11px 12px" }} onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => removeItem(item.symbol)} style={{ background: "none", border: "none", cursor: "pointer", color: C.red, padding: "4px 6px", borderRadius: 6, display: "flex", alignItems: "center" }}><Trash2 size={13} /></button>
                    </td>
                  </tr>
                  {expanded === item.symbol && (
                    <tr key={`${item.symbol}-exp`}>
                      <td colSpan={12} style={{ padding: "0 12px 12px", background: C.cardHover }}>
                        <div style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 14px", fontSize: 12, color: C.text2, lineHeight: 1.6 }}>
                          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 6 }}>
                            <div><span style={{ color: C.text3 }}>Regime:</span> <strong style={{ color: C.text1 }}>{item.regime || "—"}</strong></div>
                            <div><span style={{ color: C.text3 }}>Sentiment:</span> <strong style={{ color: C.text1 }}>{item.sentiment || "—"}</strong></div>
                            <div><span style={{ color: C.text3 }}>R/R:</span> <strong style={{ color: C.cyan }}>{item.risk_reward > 0 ? `1:${item.risk_reward.toFixed(1)}` : "—"}</strong></div>
                          </div>
                          {item.reason && <div style={{ marginBottom: 4 }}><span style={{ color: C.text3 }}>Sebep: </span>{item.reason}</div>}
                          {item.explanation && <div><span style={{ color: C.text3 }}>Açıklama: </span>{item.explanation}</div>}
                          {item.entry_price > 0 && item.stop_loss > 0 && item.take_profit > 0 && <PriceProgressBar item={item} />}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

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
  const [activeTab, setActiveTab] = useState<"hisselerim" | "sinyal-takip">("hisselerim");
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
  const [scanResults, setScanResults] = useState<Record<string, { score: number; signal: string }>>({});
  const [currency, setCurrency] = useState("$");
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("finpilot_settings");
      if (stored) setCurrency(getCurrencySymbol(JSON.parse(stored).market || "US"));
    } catch {}
  }, []);

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

  /* Derived watchlist data — merge scan results */
  const watchlist = tickers.map((t) => {
    const base = withLivePrice(genStock(t), live[t]);
    const sr = scanResults[t];
    if (sr) {
      return { ...base, score: sr.score, signal: sr.signal };
    }
    return base;
  });

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

  /* Scan watchlist — REAL API */
  const runScan = async () => {
    if (scanning || tickers.length === 0) return;
    setScanning(true);
    setScanDone(false);
    setScanPct(0);
    try {
      setScanPct(20);
      const res = await fetch("/py-api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: tickers }),
      });
      setScanPct(80);
      if (res.ok) {
        const data = await res.json();
        const results: Record<string, { score: number; signal: string }> = {};
        for (const [sym, d] of Object.entries(data)) {
          const r = d as Record<string, unknown>;
          const sc = Math.max(Number(r.filter_score ?? 0), Number(r.score ?? 0));
          const normalized = r.composite_score != null
            ? Number(r.composite_score)
            : Math.round((sc / 4) * 100);
          const signal = normalized >= 70 ? "BUY" : normalized >= 45 ? "HOLD" : normalized >= 25 ? "CAUTION" : "SELL";
          results[sym] = { score: normalized, signal };
        }
        setScanResults(results);
      }
      setScanPct(100);
      setScanDone(true);
    } catch {
      /* silent */
    } finally {
      setScanning(false);
    }
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
      <DemoBanner connected={Object.keys(live).length > 0} />

      {/* ── Tabs ──────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 4, borderBottom: `1px solid ${C.border}`, paddingBottom: 0 }}>
        {([
          { key: "hisselerim",   label: "★ Hisselerim",    icon: <Star size={14} /> },
          { key: "sinyal-takip", label: "⦿ Sinyal Takip",  icon: <Eye size={14} /> },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "10px 18px", fontSize: 13, fontWeight: 600,
              background: "none", border: "none", cursor: "pointer",
              color: activeTab === tab.key ? C.cyan : C.text2,
              borderBottom: activeTab === tab.key ? `2px solid ${C.cyan}` : "2px solid transparent",
              marginBottom: -1,
              transition: "color 0.15s",
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "sinyal-takip" && <SinyalTakipTab />}
      {activeTab === "hisselerim" && (<>
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
                    <span style={{ fontSize: 18, fontWeight: 700, color: C.text1 }}>{currency}{w.price.toFixed(2)}</span>
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
      </>)}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
