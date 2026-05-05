"use client";

import { useState, useEffect, useRef } from "react";
import {
  Brain,
  FlaskConical,
  Cpu,
  Network,
  Settings2,
  RefreshCw,
  Search,
  ChevronDown,
} from "lucide-react";
import { C, hashStr, seededRandom, companyNames } from "@/lib/stockData";
import { useAuth } from "@/lib/auth";
import { useStockPrices, type LiveQuote } from "@/lib/useStockPrices";
import { Loader2, Play } from "lucide-react";
import DemoBanner from "@/components/DemoBanner";

/* ── Tabs ──────────────────────────────────────────────────── */
const labTabs = ["AI Research", "Hybrid Engine", "DRL Models", "Ensemble Router", "Optuna"];

/* ── Tag → emoji map ────────────────────────────────────────── */
const tagEmoji: Record<string, string> = {
  trend: "📈", momentum: "📈", conservative: "🛡️", aggressive: "🔥",
  breakout: "🚀", swing: "🔄", scalper: "⚡", range: "📐", volatile: "🌊",
  meanrev: "↩️",
};
const algoColor: Record<string, string> = { PPO: C.cyan, SAC: C.yellow, TD3: C.green, A2C: C.blue };

/* ── Types for real API data ────────────────────────────────── */
interface RealModel {
  model_id: string; name: string; algorithm: string; version: string;
  created_at: string; total_timesteps: number; is_active: boolean;
  metrics: Record<string, number>; hyperparameters: Record<string, any>;
  tags: string[]; training_symbols: string[];
}
interface OptunaResults {
  best_trial: number; best_value: number;
  best_params: Record<string, number>;
  best_attrs: Record<string, number>;
  all_trials: { number: number; value: number; params: Record<string, number>; attrs?: Record<string, number> }[];
}
interface InferenceEntry {
  ai_score: number; signal: string; confidence: number;
  regime: string; price: number; timestamp: string;
}

/* ── Generate research report (offline fallback) ─────────── */
function genReport(ticker: string, liveQuote?: LiveQuote, scanScore?: number | null) {
  const name = companyNames[ticker] || `${ticker} Corp`;
  const price = liveQuote?.price ?? 0;
  const score = scanScore ?? 0;
  const sentiment = score >= 65 ? "bullish" : score <= 40 ? "bearish" : "neutral";
  const target1 = price > 0 ? (price * 1.05).toFixed(2) : "N/A";
  const target2 = price > 0 ? (price * 1.10).toFixed(2) : "N/A";
  const target3 = price > 0 ? (price * 1.15).toFixed(2) : "N/A";
  const stop = price > 0 ? (price * 0.93).toFixed(2) : "N/A";
  const reco = score >= 65 ? "Strong buy" : score >= 50 ? "Moderate buy" : score >= 30 ? "Hold" : score > 0 ? "Caution" : "No data";
  return [
    {
      title: "📊 Market Sentiment",
      content: `Overall market sentiment for ${name} is ${sentiment} based on technical scanner analysis. Scanner Score: ${score}/100.${score === 0 ? " No scanner data available — run a scan first." : ""}`,
    },
    {
      title: "💰 Price & Targets",
      content: price > 0
        ? `Current price: $${price.toFixed(2)}. Targets: $${target1}, $${target2}, $${target3}. Stop loss: $${stop}.`
        : `Price data not available. Run a scan or wait for market data.`,
    },
    {
      title: "⚠️ Note",
      content: `This is an offline fallback report. For real AI-powered analysis, ensure the LLM backend is online (Groq/Claude/Gemini).`,
    },
    {
      title: "🎯 Conclusion",
      content: `${name}: Scanner Score ${score}/100. Recommendation: ${reco}.${score === 0 ? " Score unavailable — the ticker may not have been scanned yet." : ""}`,
    },
  ];
}

/* ── SVG: Equity Curve ─────────────────────────────────────── */
function EquityCurve({ seed, color, w = 160, h = 40 }: { seed: number; color: string; w?: number; h?: number }) {
  const pts: number[] = [];
  let val = 100;
  for (let i = 0; i < 30; i++) {
    val += (seededRandom(seed + i) - 0.42) * 5;
    pts.push(val);
  }
  const mn = Math.min(...pts);
  const mx = Math.max(...pts);
  const rng = mx - mn || 1;
  const points = pts.map((v, i) => `${(i / 29) * w},${h - ((v - mn) / rng) * h}`).join(" ");
  const fillPts = `0,${h} ${points} ${w},${h}`;
  const gId = `eq_${seed}`;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={gId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.3} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill={`url(#${gId})`} />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

/* ── SVG: Sharpe Bar Chart ─────────────────────────────────── */
function SharpeBarChart({ trials }: { trials: { trial: number; sharpe: number }[] }) {
  const w = 500, h = 100;
  const maxS = Math.max(...trials.map(t => t.sharpe));
  const barW = w / trials.length - 4;
  const bestIdx = trials.reduce((best, t, i) => t.sharpe > trials[best].sharpe ? i : best, 0);
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {trials.map((t, i) => {
        const barH = (t.sharpe / maxS) * (h - 20);
        const x = i * (w / trials.length) + 2;
        const isBest = i === bestIdx;
        return (
          <g key={t.trial}>
            <rect x={x} y={h - barH - 10} width={barW} height={barH} rx={3}
              fill={isBest ? C.cyan : "rgba(0,212,255,0.25)"} />
            <text x={x + barW / 2} y={h} textAnchor="middle" fill={C.text3} fontSize="8">#{t.trial}</text>
            <text x={x + barW / 2} y={h - barH - 14} textAnchor="middle"
              fill={isBest ? C.cyan : C.text3} fontSize="7" fontWeight={isBest ? "bold" : "normal"}>{t.sharpe}</text>
          </g>
        );
      })}
    </svg>
  );
}

/* ── Signal Chip ───────────────────────────────────────────── */
function SignalChip({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.1)" },
    "STRONG BUY": { color: C.green, bg: "rgba(48,209,88,0.15)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.1)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.1)" },
    CAUTION: { color: C.yellow, bg: "rgba(255,214,10,0.1)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span style={{ color: c.color, backgroundColor: c.bg, borderRadius: 9999, padding: "2px 8px", fontSize: 10, fontWeight: 700 }}>
      {signal}
    </span>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN PAGE
   ══════════════════════════════════════════════════════════════ */
export default function AILabPage() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState("AI Research");
  const [strategyMode, setHybridMode] = useState("hybrid");
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  const [researchTicker, setResearchTicker] = useState("");
  const [researchReport, setResearchReport] = useState<ReturnType<typeof genReport> | null>(null);
  const [researchProvider, setResearchProvider] = useState<string | null>(null);
  const [researchLoading, setResearchLoading] = useState(false);
  const [scannerScore, setScannerScore] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [hoverCard, setHoverCard] = useState<string | null>(null);
  const [hoverRow, setHoverRow] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  /* ── Real API state ──────────────────────────────────────── */
  const [realModels, setRealModels] = useState<RealModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);

  const [hybridData, setHybridData] = useState<any[]>([]);
  const [hybridLoading, setHybridLoading] = useState(false);
  const [hybridTimestamp, setHybridTimestamp] = useState<string | null>(null);
  const [inferenceRunning, setInferenceRunning] = useState(false);

  const [ensembleData, setEnsembleData] = useState<any[]>([]);
  const [ensembleLoading, setEnsembleLoading] = useState(false);
  const [customSymbols, setCustomSymbols] = useState("AAPL,MSFT,NVDA,GOOGL,TSLA");

  const [optunaAgents, setOptunaAgents] = useState<string[]>([]);
  const [optunaAgent, setOptunaAgent] = useState("conservative");
  const [optunaData, setOptunaData] = useState<OptunaResults | null>(null);
  const [optunaLoading, setOptunaLoading] = useState(false);
  const [optunaJob, setOptunaJob] = useState<{ job_id: string; status: string; progress: number; error?: string } | null>(null);
  const [optunaTrials, setOptunaTrials] = useState(10);

  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  /* ── Check if Python API is online ──────────────────────── */
  useEffect(() => {
    fetch("/py-api/health")
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  /* ── Load stock presets ─────────────────────────────────── */
  useEffect(() => {
    fetch("/stock_presets.json")
      .then((r) => r.json())
      .then((data) => {
        const syms = new Set<string>();
        Object.values(data).forEach((p: any) => p.symbols?.forEach((s: string) => syms.add(s)));
        setAllSymbols(Array.from(syms).sort());
      })
      .catch(() => {});
  }, []);

  /* ── Load real DRL models from registry ─────────────────── */
  useEffect(() => {
    if (apiOnline !== true) return;
    setModelsLoading(true);
    fetch("/py-api/models")
      .then((r) => r.json())
      .then((data: RealModel[]) => setRealModels(data))
      .catch(() => {})
      .finally(() => setModelsLoading(false));
  }, [apiOnline]);

  /* ── Load Hybrid data from inference cache ──────────────── */
  const fetchInferenceCache = () => {
    setHybridLoading(true);
    fetch("/py-api/inference-cache")
      .then((r) => r.json())
      .then((cache: Record<string, InferenceEntry>) => {
        const entries = Object.entries(cache);
        const rows = entries
          .map(([sym, d]) => ({
            ticker: sym,
            scanner: d.signal,
            drl: d.signal,
            consensus: d.signal === "BUY" ? "STRONG BUY" : d.signal,
            confidence: Math.round(d.confidence * 100),
            posSize: d.signal === "BUY" ? "5%" : d.signal === "HOLD" ? "2%" : "0%",
            aiScore: d.ai_score,
            regime: d.regime === "0" ? "Trend" : d.regime === "1" ? "Range" : "Volatile",
          }))
          .sort((a, b) => b.confidence - a.confidence);
        setHybridData(rows);
        // Extract freshest timestamp
        if (entries.length > 0) {
          const ts = entries.map(([, d]) => d.timestamp).sort().pop();
          setHybridTimestamp(ts || null);
        }
      })
      .catch(() => {})
      .finally(() => setHybridLoading(false));
  };

  useEffect(() => {
    if (apiOnline !== true) return;
    fetchInferenceCache();
  }, [apiOnline]);

  /* ── Load Optuna agents list → results ──────────────────── */
  useEffect(() => {
    if (apiOnline !== true) return;
    fetch("/py-api/optuna/agents")
      .then((r) => r.json())
      .then((agents: string[]) => {
        setOptunaAgents(agents);
        if (agents.length > 0 && !agents.includes(optunaAgent)) setOptunaAgent(agents[0]);
      })
      .catch(() => {});
  }, [apiOnline]);

  useEffect(() => {
    if (apiOnline !== true || !optunaAgent) return;
    setOptunaLoading(true);
    fetch(`/py-api/optuna/results?agent=${optunaAgent}`)
      .then((r) => r.json())
      .then((data: OptunaResults) => setOptunaData(data))
      .catch(() => {})
      .finally(() => setOptunaLoading(false));
  }, [apiOnline, optunaAgent]);

  /* ── Poll Optuna job status ──────────────────────────────── */
  useEffect(() => {
    if (!optunaJob || optunaJob.status === "done" || optunaJob.status === "error") return;
    const interval = setInterval(() => {
      fetch(`/py-api/optuna/status/${optunaJob.job_id}`)
        .then((r) => r.json())
        .then((j: { job_id: string; status: string; progress: number }) => {
          setOptunaJob(j);
          if (j.status === "done") {
            // Reload results after completion
            setOptunaLoading(true);
            fetch(`/py-api/optuna/results?agent=${optunaAgent}`)
              .then((r) => r.json())
              .then((data: OptunaResults) => setOptunaData(data))
              .catch(() => {})
              .finally(() => setOptunaLoading(false));
          }
        })
        .catch(() => {});
    }, 1500);
    return () => clearInterval(interval);
  }, [optunaJob, optunaAgent]);

  function triggerOptunaRun() {
    if (!isAdmin) {
      setOptunaJob({ job_id: "", status: "error", progress: 0, error: "Admin role required to start Optuna runs." });
      return;
    }
    fetch("/py-api/optuna/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent: optunaAgent, n_trials: optunaTrials }),
    })
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${r.status}`);
        return body;
      })
      .then((j: { job_id: string; status: string; progress: number; error?: string }) => setOptunaJob({ ...j, progress: 0 }))
      .catch((error) => setOptunaJob({ job_id: "", status: "error", progress: 0, error: error instanceof Error ? error.message : "Optuna trigger failed." }))
  }

  /* ── Outside click to close dropdown ────────────────────── */
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setDropdownOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filteredSymbols = searchQuery
    ? allSymbols.filter((s) => s.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 20)
    : allSymbols.slice(0, 20);

  /* Live prices for research ticker */
  const { data: live } = useStockPrices(researchTicker ? [researchTicker] : []);

  function doResearch(ticker: string) {
    if (!ticker) return;
    setResearchTicker(ticker);
    setDropdownOpen(false);
    setSearchQuery("");
    setResearchProvider(null);
    setScannerScore(null);
    setResearchLoading(true);

    // Step 1: Fetch scanner score for the ticker (parallel with LLM)
    const scanPromise = apiOnline
      ? fetch("/py-api/scan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbols: [ticker] }),
        })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data && data[ticker]) {
              const r = data[ticker];
              const raw = Math.max(r.filter_score || 0, r.score || 0);
              const normalized = Math.round((raw / 5) * 100);
              setScannerScore(normalized);
              return normalized;
            }
            return null;
          })
          .catch(() => null)
      : Promise.resolve(null);

    // Step 2: Try real LLM with scanner context
    if (apiOnline) {
      scanPromise.then((scScore) => {
        const context = scScore != null
          ? `Scanner technical score: ${scScore}/100. Use this as reference for your analysis.`
          : "";
        return fetch("/py-api/llm/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbol: ticker, language: "en", context }),
        })
          .then((r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          })
          .then((data: { sections: { title: string; content: string }[]; provider: string; latency_ms: number }) => {
            setResearchReport(data.sections.map((s) => ({ title: s.title, content: s.content })));
            setResearchProvider(`${data.provider} — ${Math.round(data.latency_ms)}ms`);
          })
          .catch(() => {
            // Fallback to local genReport with real scanner score
            setResearchReport(genReport(ticker, live[ticker], scScore));
            setResearchProvider(null);
          });
      }).finally(() => setResearchLoading(false));
    } else {
      scanPromise.then((scScore) => {
        setResearchReport(genReport(ticker, live[ticker], scScore));
      }).finally(() => setResearchLoading(false));
    }
  }

  /* Re-generate report when live data arrives (only for fallback/offline mode) */
  useEffect(() => {
    if (researchTicker && live[researchTicker] && !researchProvider) {
      setResearchReport(genReport(researchTicker, live[researchTicker], scannerScore));
    }
  }, [live, researchTicker]);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px" }}>
      <DemoBanner connected={apiOnline === true} label="Demo / Beta" />
      {/* ── Header ────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <FlaskConical size={20} style={{ color: C.cyan }} />
          <h1 style={{ fontSize: 20, fontWeight: 600, color: C.text1 }}>AI Laboratory</h1>
        </div>
        <p style={{ fontSize: 13, color: C.text3, marginTop: 4 }}>
          Advanced AI research, DRL models, and ensemble consensus
        </p>
        {/* API status badge */}
        {apiOnline !== null && (
          <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: apiOnline ? C.green : C.red }} />
            <span style={{ fontSize: 11, color: apiOnline ? C.green : C.red }}>
              {apiOnline ? "Python API Connected — Real Data" : "Python API Offline — Demo Mode"}
            </span>
          </div>
        )}
      </div>

      {/* ── Tab bar ───────────────────────────────────────── */}
      <div
        style={{
          display: "flex", gap: 4, overflowX: "auto", borderRadius: 12,
          backgroundColor: C.card, padding: 4, marginBottom: 24,
        }}
      >
        {labTabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            style={{
              flexShrink: 0, borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 500,
              border: "none", cursor: "pointer", transition: "all 0.2s",
              backgroundColor: activeTab === t ? C.primary : "transparent",
              color: activeTab === t ? C.text1 : C.text3,
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════════════════════════
          TAB: AI RESEARCH
          ══════════════════════════════════════════════════════ */}
      {activeTab === "AI Research" && (
        <div>
          {/* Search + Research bar */}
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 24, marginBottom: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Brain size={18} style={{ color: C.cyan }} />
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>AI-Powered Research</h2>
            </div>
            <p style={{ fontSize: 12, color: C.text3, marginBottom: 16 }}>
              Multi-source news aggregation with LLM analysis. Powered by Groq → Claude → Gemini failover chain.
            </p>
            <div style={{ display: "flex", gap: 12, position: "relative" }}>
              <div ref={dropdownRef} style={{ flex: 1, position: "relative" }}>
                <div
                  style={{
                    display: "flex", alignItems: "center", gap: 8, borderRadius: 12,
                    border: `1px solid ${C.border}`, backgroundColor: C.primary, padding: "10px 16px",
                  }}
                >
                  <Search size={14} style={{ color: C.text3 }} />
                  <input
                    type="text"
                    placeholder={`Search from ${allSymbols.length.toLocaleString()} stocks...`}
                    value={searchQuery || researchTicker}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setDropdownOpen(true);
                      setResearchTicker("");
                    }}
                    onFocus={() => setDropdownOpen(true)}
                    style={{
                      flex: 1, background: "none", border: "none", outline: "none",
                      fontSize: 13, color: C.text1,
                    }}
                  />
                  <ChevronDown size={14} style={{ color: C.text3 }} />
                </div>
                {dropdownOpen && (
                  <div
                    style={{
                      position: "absolute", top: "100%", left: 0, right: 0, zIndex: 50,
                      marginTop: 4, borderRadius: 12, border: `1px solid ${C.border}`,
                      backgroundColor: C.card, maxHeight: 240, overflowY: "auto",
                    }}
                  >
                    {filteredSymbols.map((s) => (
                      <button
                        key={s}
                        onClick={() => doResearch(s)}
                        style={{
                          display: "block", width: "100%", textAlign: "left", padding: "8px 16px",
                          fontSize: 12, color: C.text1, background: "none", border: "none",
                          cursor: "pointer", borderBottom: `1px solid ${C.border}`,
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = C.cardHover)}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                      >
                        <span style={{ fontWeight: 600 }}>{s}</span>
                        {companyNames[s] && (
                          <span style={{ color: C.text3, marginLeft: 8 }}>{companyNames[s]}</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={() => {
                  if (researchTicker || searchQuery)
                    doResearch(researchTicker || searchQuery.toUpperCase());
                }}
                disabled={researchLoading}
                style={{
                  display: "flex", alignItems: "center", gap: 6, borderRadius: 12,
                  padding: "10px 20px", fontSize: 12, fontWeight: 600, color: "#000",
                  border: "none", cursor: researchLoading ? "not-allowed" : "pointer",
                  background: researchLoading ? C.text3 : `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
                  opacity: researchLoading ? 0.7 : 1,
                }}
              >
                {researchLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Brain size={14} />}
                {researchLoading ? "Analyzing..." : "Research"}
              </button>
            </div>
          </div>

          {/* Report output */}
          {researchLoading ? (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 48, textAlign: "center" }}>
              <Loader2 size={28} style={{ color: C.cyan, animation: "spin 1s linear infinite", margin: "0 auto 12px" }} />
              <p style={{ fontSize: 13, color: C.text3 }}>Analyzing {researchTicker} with LLM...</p>
              <p style={{ fontSize: 11, color: C.text3, marginTop: 4 }}>Groq → Claude → Gemini failover</p>
            </div>
          ) : researchReport ? (
            <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 24 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                <div
                  style={{
                    width: 36, height: 36, borderRadius: 10,
                    background: `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 14, fontWeight: 700, color: "#000",
                  }}
                >
                  {researchTicker.slice(0, 2)}
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>{researchTicker}</h3>
                  <p style={{ fontSize: 11, color: C.text3 }}>
                    {companyNames[researchTicker] || `${researchTicker} Corp`} — AI Research Report
                  </p>
                </div>
                {scannerScore != null && (
                  <span style={{
                    borderRadius: 9999,
                    backgroundColor: scannerScore >= 60 ? "rgba(48,209,88,0.15)" : scannerScore >= 40 ? "rgba(255,214,10,0.15)" : "rgba(255,69,58,0.15)",
                    padding: "4px 10px", fontSize: 10, fontWeight: 600,
                    color: scannerScore >= 60 ? C.green : scannerScore >= 40 ? C.yellow : C.red,
                  }}>
                    Scanner: {scannerScore}/100
                  </span>
                )}
                {researchProvider && (
                  <span style={{
                    borderRadius: 9999, backgroundColor: "rgba(48,209,88,0.1)",
                    padding: "4px 10px", fontSize: 10, fontWeight: 600, color: C.green,
                  }}>
                    ✦ {researchProvider}
                  </span>
                )}
                {!researchProvider && (
                  <span style={{
                    borderRadius: 9999, backgroundColor: "rgba(255,214,10,0.1)",
                    padding: "4px 10px", fontSize: 10, fontWeight: 600, color: C.yellow,
                  }}>
                    ⚠ Offline Fallback
                  </span>
                )}
              </div>
              {researchReport.map((s) => (
                <div key={s.title} style={{ marginBottom: 16 }}>
                  <h4 style={{ fontSize: 12, fontWeight: 600, color: C.text1, marginBottom: 4 }}>{s.title}</h4>
                  <p style={{ fontSize: 12, color: C.text2, lineHeight: 1.7 }}>{s.content}</p>
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                borderRadius: 16, border: `1px dashed ${C.border}`, backgroundColor: C.card,
                padding: 48, textAlign: "center",
              }}
            >
              <Brain size={36} style={{ color: C.text3, margin: "0 auto 12px" }} />
              <p style={{ fontSize: 13, color: C.text3 }}>Select a ticker and click Research to generate an AI report</p>
              <p style={{ fontSize: 11, color: C.text3, marginTop: 4 }}>
                {allSymbols.length.toLocaleString()} stocks available
              </p>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: HYBRID ENGINE
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Hybrid Engine" && (
        <div>
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Network size={16} style={{ color: C.cyan }} />
                <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Scanner + DRL Consensus</h2>
                <span style={{ fontSize: 11, color: apiOnline ? C.green : C.text3 }}>
                  {apiOnline ? `${hybridData.length} signals from inference cache` : "Demo mode"}
                </span>
                {hybridTimestamp && (
                  <span style={{ fontSize: 10, color: C.text3 }}>
                    • Updated: {(() => {
                      const diff = Date.now() - new Date(hybridTimestamp).getTime();
                      const mins = Math.floor(diff / 60000);
                      if (mins < 1) return "just now";
                      if (mins < 60) return `${mins}m ago`;
                      const hours = Math.floor(mins / 60);
                      if (hours < 24) return `${hours}h ago`;
                      return `${Math.floor(hours / 24)}d ago`;
                    })()}
                  </span>
                )}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {/* Refresh inference button */}
                <button
                  onClick={() => {
                    if (inferenceRunning) return;
                    setInferenceRunning(true);
                    const syms = hybridData.length
                      ? hybridData.map((r) => r.ticker)
                      : customSymbols.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean).slice(0, 20);
                    fetch("/py-api/inference/run", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ symbols: syms }),
                    })
                      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
                      .then(() => fetchInferenceCache())
                      .catch(() => {})
                      .finally(() => setInferenceRunning(false));
                  }}
                  disabled={!apiOnline || inferenceRunning}
                  style={{
                    display: "flex", alignItems: "center", gap: 4, borderRadius: 8,
                    border: `1px solid ${C.border}`, backgroundColor: C.card,
                    padding: "4px 10px", fontSize: 11, fontWeight: 500,
                    color: inferenceRunning ? C.cyan : C.text2,
                    cursor: inferenceRunning || !apiOnline ? "not-allowed" : "pointer",
                    opacity: !apiOnline ? 0.4 : 1,
                  }}
                >
                  {inferenceRunning
                    ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
                    : <RefreshCw size={12} />}
                  {inferenceRunning ? "Running DRL..." : "↻ Refresh"}
                </button>
                <div style={{ display: "flex", gap: 2, borderRadius: 8, backgroundColor: C.primary, padding: 2 }}>
                {["hybrid", "scanner", "drl"].map((m) => (
                  <button
                    key={m}
                    onClick={() => setHybridMode(m)}
                    style={{
                      borderRadius: 6, padding: "4px 12px", fontSize: 10, fontWeight: 500,
                      border: "none", cursor: "pointer",
                      backgroundColor: strategyMode === m ? C.card : "transparent",
                      color: strategyMode === m ? C.text1 : C.text3,
                    }}
                  >
                    {m.charAt(0).toUpperCase() + m.slice(1)}
                  </button>
                ))}
              </div>
              </div>
            </div>
            {hybridLoading ? (
              <div style={{ padding: 40, textAlign: "center" }}>
                <Loader2 size={24} style={{ color: C.cyan, animation: "spin 1s linear infinite" }} />
                <p style={{ fontSize: 12, color: C.text3, marginTop: 8 }}>Loading real inference data...</p>
              </div>
            ) : hybridData.length === 0 ? (
              <div style={{ padding: 40, textAlign: "center" }}>
                <Network size={28} style={{ color: C.text3, margin: "0 auto 8px" }} />
                <p style={{ fontSize: 12, color: C.text3 }}>
                  {apiOnline ? "No inference data cached yet. Run DRL inference first." : "Start Python API to see real signals."}
                </p>
              </div>
            ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", textAlign: "left", fontSize: 12, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {["Symbol", "Signal", "Regime", "Confidence", "AI Score", "Position"].map((h) => (
                      <th key={h} style={{ padding: "8px 12px", fontWeight: 500, fontSize: 10, color: C.text3 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {hybridData.map((r) => (
                    <tr
                      key={r.ticker}
                      style={{
                        borderBottom: `1px solid ${C.border}`,
                        backgroundColor: hoverRow === `h_${r.ticker}` ? C.cardHover : "transparent",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={() => setHoverRow(`h_${r.ticker}`)}
                      onMouseLeave={() => setHoverRow(null)}
                    >
                      <td style={{ padding: "10px 12px", fontWeight: 600, color: C.text1 }}>{r.ticker}</td>
                      <td style={{ padding: "10px 12px" }}><SignalChip signal={r.consensus} /></td>
                      <td style={{ padding: "10px 12px", fontSize: 11, color: C.text2 }}>{r.regime}</td>
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: C.primary }}>
                            <div
                              style={{
                                width: `${r.confidence}%`, height: 4, borderRadius: 2, backgroundColor: C.cyan,
                              }}
                            />
                          </div>
                          <span style={{ color: C.text2, fontSize: 11 }}>{r.confidence}%</span>
                        </div>
                      </td>
                      <td style={{ padding: "10px 12px", color: C.text2, fontFamily: "monospace" }}>{r.aiScore?.toFixed(1)}</td>
                      <td style={{ padding: "10px 12px", color: C.text2 }}>{r.posSize}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: DRL MODELS
          ══════════════════════════════════════════════════════ */}
      {activeTab === "DRL Models" && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span
                style={{
                  borderRadius: 9999, backgroundColor: "rgba(48,209,88,0.1)",
                  padding: "4px 12px", fontSize: 12, fontWeight: 500, color: C.green,
                }}
              >
                {realModels.filter((m) => m.is_active).length} Active
              </span>
              <span style={{ fontSize: 12, color: C.text3 }}>{realModels.length} total models</span>
              {apiOnline && <span style={{ fontSize: 10, color: C.green }}>● Real Registry</span>}
            </div>
            <button
              style={{
                display: "flex", alignItems: "center", gap: 4, borderRadius: 12,
                border: `1px solid ${C.border}`, backgroundColor: C.card, padding: "6px 12px",
                fontSize: 12, color: C.text2, cursor: "pointer",
              }}
            >
              <RefreshCw size={12} />
              Retrain
            </button>
          </div>
          {modelsLoading ? (
            <div style={{ padding: 40, textAlign: "center" }}>
              <Loader2 size={24} style={{ color: C.cyan, animation: "spin 1s linear infinite" }} />
              <p style={{ fontSize: 12, color: C.text3, marginTop: 8 }}>Loading model registry...</p>
            </div>
          ) : (
          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(3, 1fr)" }}>
            {realModels.map((m) => {
              const color = algoColor[m.algorithm] || C.cyan;
              const mainTag = m.tags[0] || m.name.replace("ppo_", "").replace("sac_", "").replace("td3_", "");
              const emoji = tagEmoji[mainTag] || "🤖";
              const sharpe = m.metrics.sharpe_ratio ?? 0;
              const totalReturn = m.metrics.total_return ?? 0;
              const maxDD = m.metrics.max_drawdown ?? 0;
              const nTrades = m.metrics.n_trades ?? 0;
              const trainedDate = m.created_at ? new Date(m.created_at).toLocaleDateString() : "—";
              return (
              <div
                key={m.model_id}
                style={{
                  borderRadius: 16,
                  border: `1px solid ${hoverCard === m.model_id ? C.borderHover : C.border}`,
                  backgroundColor: hoverCard === m.model_id ? C.cardHover : C.card,
                  padding: 20, transition: "all 0.25s", cursor: "pointer",
                }}
                onMouseEnter={() => setHoverCard(m.model_id)}
                onMouseLeave={() => setHoverCard(null)}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                  <span style={{ fontSize: 18 }}>{emoji} {mainTag}</span>
                  <span
                    style={{
                      borderRadius: 9999,
                      backgroundColor: m.is_active ? "rgba(48,209,88,0.1)" : "rgba(255,69,58,0.1)",
                      padding: "2px 8px", fontSize: 10, fontWeight: 500,
                      color: m.is_active ? C.green : C.red,
                    }}
                  >
                    {m.is_active ? "active" : "inactive"}
                  </span>
                </div>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text1, marginBottom: 4 }}>
                  {m.algorithm} — {m.name}
                </h3>
                <p style={{ fontSize: 10, color: C.text3, marginBottom: 12 }}>
                  {m.version} • Trained: {trainedDate} • {(m.total_timesteps / 1000).toFixed(0)}K steps
                </p>

                {/* Mini equity curve */}
                <div
                  style={{
                    marginBottom: 12, borderRadius: 8, overflow: "hidden",
                    backgroundColor: C.primary, padding: "8px 4px",
                  }}
                >
                  <EquityCurve seed={hashStr(m.model_id)} color={color} w={200} h={50} />
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, padding: "0 4px" }}>
                    <span style={{ fontSize: 9, color: C.text3 }}>Equity Curve</span>
                    <span style={{ fontSize: 9, color: totalReturn >= 0 ? C.green : C.red, fontWeight: 600 }}>
                      {totalReturn >= 0 ? "+" : ""}{(totalReturn * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                {[
                  { label: "Sharpe Ratio", value: sharpe.toFixed(4), color: C.cyan },
                  { label: "Total Return", value: `${(totalReturn * 100).toFixed(1)}%`, color: totalReturn >= 0 ? C.green : C.red },
                  { label: "Max Drawdown", value: `${(maxDD * 100).toFixed(1)}%`, color: C.red },
                  { label: "Total Trades", value: nTrades.toString(), color: C.text1 },
                ].map((s) => (
                  <div key={s.label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 12 }}>
                    <span style={{ color: C.text3 }}>{s.label}</span>
                    <span style={{ fontWeight: 500, color: s.color }}>{s.value}</span>
                  </div>
                ))}

                <div style={{ marginTop: 12, display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {m.tags.map((t) => (
                    <span
                      key={t}
                      style={{ borderRadius: 6, backgroundColor: C.primary, padding: "2px 6px", fontSize: 10, color: C.text3 }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              );
            })}
          </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: ENSEMBLE ROUTER
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Ensemble Router" && (
        <div>
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Cpu size={16} style={{ color: C.cyan }} />
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Multi-Agent Ensemble Router</h2>
              <span style={{ fontSize: 11, color: apiOnline ? C.green : C.text3 }}>
                {apiOnline ? `${ensembleData.length} predictions via real DRL agents` : "Demo mode — start Python API"}
              </span>
            </div>
            {!apiOnline ? (
              <div style={{ padding: 40, textAlign: "center" }}>
                <Cpu size={28} style={{ color: C.text3, margin: "0 auto 8px" }} />
                <p style={{ fontSize: 12, color: C.text3 }}>
                  Ensemble Router requires Python API. Start with: uvicorn api.main:app --port 8000
                </p>
              </div>
            ) : ensembleLoading ? (
              <div style={{ padding: 40, textAlign: "center" }}>
                <Loader2 size={24} style={{ color: C.cyan, animation: "spin 1s linear infinite" }} />
                <p style={{ fontSize: 12, color: C.text3, marginTop: 8 }}>Running ensemble predictions...</p>
              </div>
            ) : ensembleData.length === 0 ? (
              <div style={{ padding: 32, textAlign: "center" }}>
                <p style={{ fontSize: 12, color: C.text3, marginBottom: 12 }}>
                  {hybridData.length > 0
                    ? "Run ensemble on inference-cached symbols to see agent votes."
                    : "Enter symbols below to run ensemble predictions."}
                </p>
                {hybridData.length === 0 && (
                  <div style={{ maxWidth: 400, margin: "0 auto 16px" }}>
                    <input
                      type="text"
                      value={customSymbols}
                      onChange={(e) => setCustomSymbols(e.target.value)}
                      placeholder="AAPL, MSFT, NVDA, GOOGL, TSLA"
                      style={{
                        width: "100%", borderRadius: 8, border: `1px solid ${C.border}`,
                        backgroundColor: C.primary, padding: "8px 12px", fontSize: 12,
                        color: C.text1, outline: "none", textAlign: "center",
                      }}
                    />
                    <p style={{ fontSize: 10, color: C.text3, marginTop: 4 }}>
                      Comma-separated symbols (max 20)
                    </p>
                  </div>
                )}
                <button
                  onClick={() => {
                    setEnsembleLoading(true);
                    const syms = hybridData.length
                      ? hybridData.map((r) => r.ticker)
                      : customSymbols.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean).slice(0, 20);
                    if (syms.length === 0) { setEnsembleLoading(false); return; }
                    fetch("/py-api/ensemble", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ symbols: syms, max_symbols: 20 }),
                    })
                      .then((r) => r.json())
                      .then((data: Record<string, any>) => {
                        const rows = Object.entries(data).map(([sym, d]) => ({
                          ticker: sym,
                          action: d.action || "HOLD",
                          confidence: Math.round((d.confidence ?? 0) * 100),
                          regime: d.regime || "—",
                          agreement: d.agreement_score != null ? `${d.agreement_score.toFixed(1)}` : "—",
                          ensemble: d.ensemble ? "Yes" : "No",
                          position: d.suggested_position != null ? `${(d.suggested_position * 100).toFixed(0)}%` : "—",
                        }));
                        setEnsembleData(rows.sort((a, b) => b.confidence - a.confidence));
                      })
                      .catch(() => {})
                      .finally(() => setEnsembleLoading(false));
                  }}
                  style={{
                    borderRadius: 12, padding: "8px 20px", fontSize: 12, fontWeight: 600,
                    color: "#000", border: "none", cursor: "pointer",
                    background: `linear-gradient(135deg, ${C.cyan}, ${C.blue})`,
                  }}
                >
                  Run Ensemble
                </button>
              </div>
            ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", textAlign: "left", fontSize: 12, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {["Symbol", "Action", "Confidence", "Regime", "Agreement", "Position"].map(
                      (h) => (
                        <th key={h} style={{ padding: "8px 12px", fontWeight: 500, fontSize: 10, color: C.text3 }}>
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {ensembleData.map((v) => (
                    <tr
                      key={v.ticker}
                      style={{
                        borderBottom: `1px solid ${C.border}`,
                        backgroundColor: hoverRow === `e_${v.ticker}` ? C.cardHover : "transparent",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={() => setHoverRow(`e_${v.ticker}`)}
                      onMouseLeave={() => setHoverRow(null)}
                    >
                      <td style={{ padding: "10px 12px", fontWeight: 600, color: C.text1 }}>{v.ticker}</td>
                      <td style={{ padding: "10px 12px" }}><SignalChip signal={v.action} /></td>
                      <td style={{ padding: "10px 12px", color: C.text2 }}>{v.confidence}%</td>
                      <td style={{ padding: "10px 12px", fontSize: 11, color: C.text2 }}>{v.regime}</td>
                      <td style={{ padding: "10px 12px" }}>
                        <span style={{ fontSize: 12, fontWeight: 500, color: C.text2 }}>
                          {v.agreement}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px", color: C.text2 }}>{v.position}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          TAB: OPTUNA
          ══════════════════════════════════════════════════════ */}
      {activeTab === "Optuna" && (
        <div>
          <div style={{ borderRadius: 16, border: `1px solid ${C.border}`, backgroundColor: C.card, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
              <Settings2 size={16} style={{ color: C.cyan }} />
              <h2 style={{ fontSize: 14, fontWeight: 600, color: C.text1 }}>Hyperparameter Optimization</h2>
              {/* Agent selector */}
              <div style={{ display: "flex", gap: 2, borderRadius: 8, backgroundColor: C.primary, padding: 2, marginLeft: "auto" }}>
                {optunaAgents.map((a) => (
                  <button
                    key={a}
                    onClick={() => setOptunaAgent(a)}
                    style={{
                      borderRadius: 6, padding: "4px 10px", fontSize: 10, fontWeight: 500,
                      border: "none", cursor: "pointer", textTransform: "capitalize",
                      backgroundColor: optunaAgent === a ? C.card : "transparent",
                      color: optunaAgent === a ? C.text1 : C.text3,
                    }}
                  >
                    {a}
                  </button>
                ))}
              </div>
              {/* Trials input + Run button */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <label style={{ fontSize: 10, color: C.text3 }}>Trials:</label>
                <input
                  type="number" min={1} max={100} value={optunaTrials}
                  onChange={(e) => setOptunaTrials(Math.max(1, Math.min(100, Number(e.target.value))))}
                  style={{ width: 52, borderRadius: 6, border: `1px solid ${C.border}`, backgroundColor: C.primary, color: C.text1, fontSize: 11, padding: "3px 6px", textAlign: "center" }}
                />
                <button
                  onClick={triggerOptunaRun}
                  disabled={optunaJob?.status === "running"}
                  style={{
                    display: "flex", alignItems: "center", gap: 4,
                    borderRadius: 8, padding: "5px 12px", fontSize: 11, fontWeight: 600,
                    border: "none", cursor: optunaJob?.status === "running" ? "not-allowed" : "pointer",
                    background: optunaJob?.status === "running" ? C.border : `linear-gradient(135deg, ${C.cyan}, #0088cc)`,
                    color: optunaJob?.status === "running" ? C.text3 : "#000",
                  }}
                >
                  {optunaJob?.status === "running" ? (
                    <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
                  ) : (
                    <Play size={12} />
                  )}
                  {optunaJob?.status === "running" ? "Running..." : "Run Optimization"}
                </button>
              </div>
            </div>

            {/* Job progress bar */}
            {optunaJob && optunaJob.status === "running" && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: C.text3 }}>Optimization in progress — {optunaJob.progress}%</span>
                  <span style={{ fontSize: 11, color: C.cyan }}>Trial {Math.round(optunaJob.progress / 100 * optunaTrials)}/{optunaTrials}</span>
                </div>
                <div style={{ height: 6, borderRadius: 3, backgroundColor: C.primary }}>
                  <div style={{ height: 6, borderRadius: 3, backgroundColor: C.cyan, width: `${optunaJob.progress}%`, transition: "width 0.4s ease" }} />
                </div>
              </div>
            )}
            {optunaJob && optunaJob.status === "done" && (
              <div style={{ marginBottom: 12, padding: "8px 12px", borderRadius: 8, backgroundColor: "rgba(48,209,88,0.08)", border: `1px solid rgba(48,209,88,0.2)`, fontSize: 11, color: C.green }}>
                ✓ Optimization complete — results refreshed
              </div>
            )}
            {optunaJob && optunaJob.status === "error" && (
              <div style={{ marginBottom: 12, padding: "8px 12px", borderRadius: 8, backgroundColor: "rgba(255,69,58,0.08)", border: `1px solid rgba(255,69,58,0.2)`, fontSize: 11, color: C.red }}>
                ✗ {optunaJob.error || "Optimization failed"}
              </div>
            )}
            {!optunaData ? (
              <p style={{ fontSize: 12, color: C.text3, marginTop: 8 }}>Loading Optuna results...</p>
            ) : (
              <div>
            {/* Summary cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: C.cyan }}>{optunaData.best_value.toFixed(4)}</div>
                <div style={{ fontSize: 10, color: C.text3 }}>Best Sharpe (Trial #{optunaData.best_trial})</div>
              </div>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: C.green }}>
                  {((optunaData.best_attrs?.total_return ?? 0) * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: 10, color: C.text3 }}>Best Return</div>
              </div>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: C.red }}>
                  {((optunaData.best_attrs?.max_drawdown ?? 0) * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: 10, color: C.text3 }}>Max Drawdown</div>
              </div>
              <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: C.text1 }}>{optunaData.all_trials?.length || 0}</div>
                <div style={{ fontSize: 10, color: C.text3 }}>Total Trials</div>
              </div>
            </div>

            {/* SVG Sharpe distribution bar chart */}
            <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: 16, marginBottom: 16 }}>
              <p style={{ fontSize: 11, color: C.text3, marginBottom: 8 }}>Sharpe Ratio Distribution — {optunaAgent}</p>
              <SharpeBarChart trials={(optunaData.all_trials || []).map((t) => ({ trial: t.number, sharpe: t.value }))} />
            </div>

            {/* Best params */}
            <div style={{ borderRadius: 12, backgroundColor: C.primary, padding: 16, marginBottom: 16 }}>
              <p style={{ fontSize: 11, color: C.text3, marginBottom: 8 }}>Best Hyperparameters</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {Object.entries(optunaData.best_params || {}).slice(0, 12).map(([k, v]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                    <span style={{ color: C.text3 }}>{k}</span>
                    <span style={{ color: C.text1, fontFamily: "monospace" }}>
                      {typeof v === "number" ? (v < 0.01 ? v.toExponential(2) : v.toFixed(4)) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Trials table */}
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", textAlign: "left", fontSize: 12, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {["#", "Learning Rate", "Gamma", "Batch Size", "Sharpe", "Return", "Trades"].map((h) => (
                      <th key={h} style={{ padding: "8px 12px", fontWeight: 500, fontSize: 10, color: C.text3 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(optunaData.all_trials || []).map((t) => {
                    const isBest = t.number === optunaData.best_trial;
                    return (
                      <tr
                        key={t.number}
                        style={{
                          borderBottom: `1px solid ${C.border}`,
                          backgroundColor: isBest
                            ? "rgba(0,212,255,0.06)"
                            : hoverRow === `o_${t.number}`
                              ? C.cardHover
                              : "transparent",
                          transition: "background-color 0.2s",
                        }}
                        onMouseEnter={() => setHoverRow(`o_${t.number}`)}
                        onMouseLeave={() => setHoverRow(null)}
                      >
                        <td
                          style={{
                            padding: "10px 12px",
                            color: isBest ? C.cyan : C.text2,
                            fontWeight: isBest ? 700 : 400,
                          }}
                        >
                          {t.number}
                          {isBest ? " ⭐" : ""}
                        </td>
                        <td style={{ padding: "10px 12px", fontFamily: "monospace", color: C.text1 }}>
                          {t.params?.learning_rate?.toExponential(2) || "—"}
                        </td>
                        <td style={{ padding: "10px 12px", fontFamily: "monospace", color: C.text1 }}>
                          {t.params?.gamma?.toFixed(4) || "—"}
                        </td>
                        <td style={{ padding: "10px 12px", color: C.text1 }}>{t.params?.batch_size || "—"}</td>
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: isBest ? C.cyan : C.text1 }}>
                          {t.value?.toFixed(4)}
                        </td>
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: C.green }}>
                          {t.attrs?.total_return != null ? `${(t.attrs.total_return * 100).toFixed(1)}%` : "—"}
                        </td>
                        <td style={{ padding: "10px 12px", color: C.text2 }}>{t.attrs?.trades || "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
