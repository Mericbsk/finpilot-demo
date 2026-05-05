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
  Star,
  CheckCircle,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { C } from "@/lib/stockData";

/* ── Types ──────────────────────────────────────────────────── */
interface DRLModel {
  model_id: string;
  name: string;
  algorithm: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
  total_timesteps: number;
  metrics: {
    sharpe_ratio?: number;
    total_return?: number;
    max_drawdown?: number;
    n_trades?: number;
  };
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
  const { isAdmin } = useAuth();
  const [tab, setTab] = useState<"models" | "inference" | "ensemble">("models");
  const [models, setModels] = useState<DRLModel[]>([]);
  const [inferenceCache, setInferenceCache] = useState<Record<string, InferenceResult>>({});
  const [ensembleResult, setEnsembleResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [inferenceLoading, setInferenceLoading] = useState(false);
  const [ensembleLoading, setEnsembleLoading] = useState(false);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [activatingBest, setActivatingBest] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ── Check API health ────────────────────────────── */
  useEffect(() => {
    fetch("/py-api/health")
      .then((r) => r.ok && setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  /* ── Load models ─────────────────────────────────── */
  const loadModels = useCallback(() => {
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

  useEffect(() => { loadModels(); }, [loadModels]);

  /* ── Activate single model ───────────────────────── */
  const activateModel = useCallback(async (modelId: string) => {
    if (!isAdmin) {
      setError("Only admin accounts can activate models.");
      return;
    }
    setActivatingId(modelId);
    try {
      const res = await fetch(`/py-api/models/${modelId}/activate`, { method: "POST" });
      if (res.status === 403) throw new Error("Admin role required");
      if (!res.ok) throw new Error("Activation failed");
      await loadModels();
    } catch (error) {
      setError(error instanceof Error ? error.message : `Failed to activate model ${modelId}`);
    } finally {
      setActivatingId(null);
    }
  }, [isAdmin, loadModels]);

  /* ── Activate best models ────────────────────────── */
  const activateBest = useCallback(async () => {
    if (!isAdmin) {
      setError("Only admin accounts can activate best models.");
      return;
    }
    setActivatingBest(true);
    try {
      const res = await fetch("/py-api/models/activate-best", { method: "POST" });
      if (res.status === 403) throw new Error("Admin role required");
      if (!res.ok) throw new Error("Activation failed");
      await loadModels();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to activate best models");
    } finally {
      setActivatingBest(false);
    }
  }, [isAdmin, loadModels]);

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
            · {models.filter(m => m.is_active).length} active
            {apiOnline ? (
              <span className="ml-2" style={{ color: C.green }}>● API Online</span>
            ) : (
              <span className="ml-2" style={{ color: C.red }}>● API Offline</span>
            )}
          </p>
        </div>
        {/* Activate Best button */}
        <button
          onClick={activateBest}
          disabled={activatingBest || !apiOnline || !isAdmin}
          className="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all disabled:opacity-40"
          style={{ background: `linear-gradient(to right, ${C.cyan}, ${C.blue})`, color: "#000" }}
          title={!isAdmin ? "Admin role required" : undefined}
        >
          {activatingBest ? <Loader2 size={14} className="animate-spin" /> : <Star size={14} />}
          Activate Best Models
        </button>
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
              {models
                .slice()
                .sort((a, b) => (b.metrics?.sharpe_ratio ?? -999) - (a.metrics?.sharpe_ratio ?? -999))
                .map((m) => (
                <div
                  key={m.model_id}
                  className="rounded-2xl p-5 transition-all"
                  style={{
                    border: `1px solid ${m.is_active ? C.cyan : C.border}`,
                    backgroundColor: C.card,
                    boxShadow: m.is_active ? `0 0 0 1px ${C.cyan}30` : undefined,
                  }}
                >
                  {/* Header row */}
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <div className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: algoColor[m.algorithm] || C.cyan }} />
                      <span className="truncate text-xs font-semibold" style={{ color: C.text1 }} title={m.model_id}>{m.name}</span>
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      {m.is_active && (
                        <span className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold" style={{ backgroundColor: `${C.green}20`, color: C.green }}>
                          <CheckCircle size={9} /> ACTIVE
                        </span>
                      )}
                      <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: `${algoColor[m.algorithm] || C.cyan}20`, color: algoColor[m.algorithm] || C.cyan }}>
                        {m.algorithm}
                      </span>
                    </div>
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
                    {m.metrics?.sharpe_ratio != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Sharpe Ratio</span>
                        <span style={{ color: m.metrics.sharpe_ratio >= 1 ? C.green : m.metrics.sharpe_ratio >= 0.5 ? "#f59e0b" : C.red }}
                          title={m.metrics.sharpe_ratio < 0.5 ? "Düşük risk-getiri oranı. Bu model canlı işlem için hazır değil." : undefined}>
                          {m.metrics.sharpe_ratio.toFixed(3)}{m.metrics.sharpe_ratio < 0.5 ? " ⚠️" : ""}
                        </span>
                      </div>
                    )}
                    {m.metrics?.total_return != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Total Return <span style={{ fontSize: 9, opacity: 0.6 }}>(backtest)</span></span>
                        <span style={{ color: m.metrics.total_return >= 0 ? C.green : C.red }}
                          title="Bu değer eğitim verisi üzerindeki backtest sonucudur. Gerçek canlı performansı yansıtmaz.">
                          {m.metrics.total_return >= 0 ? "+" : ""}{(m.metrics.total_return * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {m.metrics?.max_drawdown != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Max Drawdown</span>
                        <span style={{ color: C.red }}>{(m.metrics.max_drawdown * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {m.metrics?.n_trades != null && (
                      <div className="flex justify-between">
                        <span style={{ color: C.text3 }}>Trades</span>
                        <span style={{ color: C.text2 }}>{m.metrics.n_trades.toLocaleString()}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span style={{ color: C.text3 }}>Timesteps</span>
                      <span style={{ color: C.text2 }}>{(m.total_timesteps / 1_000_000).toFixed(1)}M</span>
                    </div>
                  </div>

                  {/* Activate button */}
                  {!m.is_active && (
                    <button
                      onClick={() => activateModel(m.model_id)}
                      disabled={activatingId === m.model_id || !isAdmin}
                      className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl py-2 text-xs font-semibold transition-all disabled:opacity-40"
                      style={{ border: `1px solid ${C.cyan}`, color: C.cyan }}
                      title={!isAdmin ? "Admin role required" : undefined}
                    >
                      {activatingId === m.model_id ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle size={12} />}
                      Set Active
                    </button>
                  )}
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
