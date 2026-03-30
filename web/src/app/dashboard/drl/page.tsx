"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Brain,
  Play,
  RefreshCw,
  Loader2,
  TrendingUp,
  TrendingDown,
  Activity,
  Cpu,
  BarChart3,
  AlertCircle,
  Zap,
} from "lucide-react";
import { C } from "@/lib/stockData";

/* ── Types ──────────────────────────────────────────────────── */
interface DRLModel {
  model_id: string;
  algorithm: string;
  tags: string[];
  sharpe?: number;
  total_return?: number;
  max_drawdown?: number;
  training_episodes?: number;
  last_trained?: string;
}

interface InferenceResult {
  ai_score: number;
  signal: string;
  confidence: number;
  regime: string;
}

/* ── Signal badge ──────────────────────────────────────────── */
function Signal({ signal }: { signal: string }) {
  const m: Record<string, { color: string; bg: string }> = {
    BUY: { color: C.green, bg: "rgba(48,209,88,0.15)" },
    SELL: { color: C.red, bg: "rgba(255,69,58,0.15)" },
    HOLD: { color: C.cyan, bg: "rgba(0,212,255,0.15)" },
  };
  const c = m[signal] || m.HOLD;
  return (
    <span style={{ color: c.color, backgroundColor: c.bg, borderRadius: 9999, padding: "2px 10px", fontSize: 10, fontWeight: 700 }}>
      {signal}
    </span>
  );
}

/* ── Score bar ──────────────────────────────────────────────── */
function ScoreBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct >= 70 ? C.green : pct >= 40 ? C.cyan : C.red;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.08)" }}>
        <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-medium" style={{ color }}>{Math.round(value)}</span>
    </div>
  );
}

/* ── Algo color map ─────────────────────────────────────────── */
const algoColor: Record<string, string> = {
  PPO: "#00d4ff",
  A2C: "#30d158",
  SAC: "#a78bfa",
  TD3: "#ffd60a",
  DQN: "#ff9f0a",
};

/* ═══ Main Page ═══════════════════════════════════════════════ */
export default function DRLPage() {
  const [tab, setTab] = useState<"models" | "inference" | "ensemble">("models");
  const [models, setModels] = useState<DRLModel[]>([]);
  const [inferenceCache, setInferenceCache] = useState<Record<string, InferenceResult>>({});
  const [ensembleResult, setEnsembleResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [inferenceLoading, setInferenceLoading] = useState(false);
  const [ensembleLoading, setEnsembleLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ── Check API health ────────────────────────────── */
  useEffect(() => {
    fetch("/py-api/health")
      .then((r) => r.ok && setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  /* ── Load models ─────────────────────────────────── */
  useEffect(() => {
    setLoading(true);
    fetch("/py-api/models")
      .then((r) => r.json())
      .then((data) => {
        setModels(Array.isArray(data) ? data : []);
        setError(null);
      })
      .catch(() => setError("Could not load DRL models"))
      .finally(() => setLoading(false));
  }, []);

  /* ── Load inference cache ────────────────────────── */
  useEffect(() => {
    fetch("/py-api/inference-cache")
      .then((r) => r.json())
      .then((data) => {
        if (data && typeof data === "object") setInferenceCache(data);
      })
      .catch(() => {});
  }, []);

  /* ── Run live inference ──────────────────────────── */
  const runInference = useCallback(async () => {
    setInferenceLoading(true);
    try {
      const res = await fetch("/py-api/inference/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: [], model_version: "active" }),
      });
      if (!res.ok) throw new Error("Inference failed");
      const data = await res.json();
      if (data.results) setInferenceCache(data.results);
    } catch {
      setError("Live inference failed — model may not be loaded");
    } finally {
      setInferenceLoading(false);
    }
  }, []);

  /* ── Run ensemble ────────────────────────────────── */
  const runEnsemble = useCallback(async () => {
    const symbols = Object.keys(inferenceCache).slice(0, 20);
    if (symbols.length === 0) {
      setError("Run inference first to get symbols");
      return;
    }
    setEnsembleLoading(true);
    try {
      const res = await fetch("/py-api/ensemble", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols, max_symbols: 20 }),
      });
      if (!res.ok) throw new Error("Ensemble failed");
      const data = await res.json();
      setEnsembleResult(data);
    } catch {
      setError("Ensemble prediction failed");
    } finally {
      setEnsembleLoading(false);
    }
  }, [inferenceCache]);

  const tabs = [
    { id: "models" as const, label: "Model Registry", icon: Cpu },
    { id: "inference" as const, label: "Live Inference", icon: Zap },
    { id: "ensemble" as const, label: "Ensemble Router", icon: Brain },
  ];

  const inferenceSymbols = Object.entries(inferenceCache);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Brain size={20} style={{ color: C.cyan }} />
            <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>DRL Agents</h1>
          </div>
          <p className="text-sm" style={{ color: C.text3 }}>
            Deep Reinforcement Learning models · {models.length} registered
            {apiOnline ? (
              <span className="ml-2" style={{ color: C.green }}>● API Online</span>
            ) : (
              <span className="ml-2" style={{ color: C.red }}>● API Offline</span>
            )}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl p-1" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-xs font-medium transition-all"
            style={{
              backgroundColor: tab === t.id ? C.primary : "transparent",
              color: tab === t.id ? C.cyan : C.text3,
            }}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl px-4 py-3 text-xs" style={{ backgroundColor: "rgba(255,69,58,0.1)", color: C.red }}>
          <AlertCircle size={14} />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-xs underline">Dismiss</button>
        </div>
      )}

      {/* ─── Models Tab ───────────────────────────────── */}
      {tab === "models" && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 size={24} className="animate-spin" style={{ color: C.cyan }} />
            </div>
          ) : models.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <Brain size={32} style={{ color: C.text3 }} />
              <p className="text-sm" style={{ color: C.text3 }}>No DRL models registered yet</p>
              <p className="text-xs" style={{ color: C.text3 }}>Train a model to see it here</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {models.map((m) => (
                <div
                  key={m.model_id}
                  className="rounded-2xl p-5 transition-all"
                  style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full" style={{ backgroundColor: algoColor[m.algorithm] || C.cyan }} />
                      <span className="text-sm font-semibold" style={{ color: C.text1 }}>{m.model_id}</span>
                    </div>
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: `${algoColor[m.algorithm] || C.cyan}20`, color: algoColor[m.algorithm] || C.cyan }}>
                      {m.algorithm}
                    </span>
                  </div>

                  {/* Tags */}
                  <div className="mb-3 flex flex-wrap gap-1">
                    {m.tags.map((tag) => (
                      <span key={tag} className="rounded px-1.5 py-0.5 text-[9px]" style={{ backgroundColor: C.primary, color: C.text3 }}>
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Metrics */}
                  <div className="space-y-2 text-xs">
                    {m.sharpe != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Sharpe Ratio</span>
                        <span style={{ color: m.sharpe >= 1 ? C.green : C.text2 }}>{m.sharpe.toFixed(2)}</span>
                      </div>
                    )}
                    {m.total_return != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Total Return</span>
                        <span style={{ color: m.total_return >= 0 ? C.green : C.red }}>
                          {m.total_return >= 0 ? "+" : ""}{(m.total_return * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {m.max_drawdown != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Max Drawdown</span>
                        <span style={{ color: C.red }}>{(m.max_drawdown * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {m.training_episodes != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Training Episodes</span>
                        <span style={{ color: C.text2 }}>{m.training_episodes.toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── Inference Tab ────────────────────────────── */}
      {tab === "inference" && (
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex items-center justify-between rounded-2xl p-4" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
            <div>
              <p className="text-sm font-medium" style={{ color: C.text1 }}>
                {inferenceSymbols.length > 0 ? `${inferenceSymbols.length} symbols in cache` : "No inference results yet"}
              </p>
              <p className="text-xs" style={{ color: C.text3 }}>Run inference on cached symbols or re-run with active model</p>
            </div>
            <button
              onClick={runInference}
              disabled={inferenceLoading || !apiOnline}
              className="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all disabled:opacity-40"
              style={{ background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`, color: "#000" }}
            >
              {inferenceLoading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              Run Inference
            </button>
          </div>

          {/* Results grid */}
          {inferenceSymbols.length > 0 ? (
            <div className="rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-[10px]" style={{ borderBottom: `1px solid ${C.border}`, color: C.text3 }}>
                    <th className="px-5 py-3">Symbol</th>
                    <th className="px-3 py-3">AI Score</th>
                    <th className="px-3 py-3">Signal</th>
                    <th className="px-3 py-3">Confidence</th>
                    <th className="px-3 py-3">Regime</th>
                  </tr>
                </thead>
                <tbody>
                  {inferenceSymbols
                    .sort((a, b) => (b[1]?.ai_score ?? 0) - (a[1]?.ai_score ?? 0))
                    .map(([sym, data]) => (
                      <tr key={sym} style={{ borderBottom: `1px solid ${C.border}` }}>
                        <td className="px-5 py-3 font-semibold" style={{ color: C.text1 }}>{sym}</td>
                        <td className="w-32 px-3 py-3">
                          <ScoreBar value={data?.ai_score ?? 0} />
                        </td>
                        <td className="px-3 py-3">
                          <Signal signal={data?.signal ?? "HOLD"} />
                        </td>
                        <td className="px-3 py-3" style={{ color: C.text2 }}>
                          {((data?.confidence ?? 0) * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-3">
                          <span className="rounded px-2 py-0.5 text-[10px]" style={{ backgroundColor: C.primary, color: C.text3 }}>
                            {data?.regime ?? "—"}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <Activity size={32} style={{ color: C.text3 }} />
              <p className="text-sm" style={{ color: C.text3 }}>No inference results</p>
              <p className="text-xs" style={{ color: C.text3 }}>Click "Run Inference" to generate predictions</p>
            </div>
          )}
        </div>
      )}

      {/* ─── Ensemble Tab ─────────────────────────────── */}
      {tab === "ensemble" && (
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex items-center justify-between rounded-2xl p-4" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
            <div>
              <p className="text-sm font-medium" style={{ color: C.text1 }}>Multi-Agent Ensemble Router</p>
              <p className="text-xs" style={{ color: C.text3 }}>
                Combines multiple DRL agents with regime-based voting
              </p>
            </div>
            <button
              onClick={runEnsemble}
              disabled={ensembleLoading || !apiOnline || inferenceSymbols.length === 0}
              className="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all disabled:opacity-40"
              style={{ background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`, color: "#000" }}
            >
              {ensembleLoading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Run Ensemble
            </button>
          </div>

          {inferenceSymbols.length === 0 && (
            <div className="rounded-xl px-4 py-3 text-xs" style={{ backgroundColor: "rgba(255,214,10,0.1)", color: C.yellow }}>
              Run inference first (Inference tab) to get symbols for ensemble prediction
            </div>
          )}

          {/* Ensemble results */}
          {ensembleResult ? (
            <div className="rounded-2xl p-5" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <h3 className="mb-3 text-sm font-semibold" style={{ color: C.text1 }}>Ensemble Results</h3>
              <pre className="overflow-x-auto rounded-xl p-4 text-xs" style={{ backgroundColor: C.primary, color: C.text2 }}>
                {JSON.stringify(ensembleResult, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
              <BarChart3 size={32} style={{ color: C.text3 }} />
              <p className="text-sm" style={{ color: C.text3 }}>No ensemble results yet</p>
              <p className="text-xs" style={{ color: C.text3 }}>Run ensemble to see multi-agent consensus</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
