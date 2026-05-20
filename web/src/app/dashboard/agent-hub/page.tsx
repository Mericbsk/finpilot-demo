"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  Play,
  RefreshCw,
  CheckCircle2,
  Clock,
  Lightbulb,
  Network,
  Cpu,
  TrendingUp,
  Megaphone,
  ShieldCheck,
  Settings2,
  ChevronRight,
  Loader2,
  AlertCircle,
  Square,
  BarChart2,
  Target,
  Award,
} from "lucide-react";

/* ─── Types ──────────────────────────────────────────────────── */
interface AgentMeta {
  id: number;
  name: string;
  key: string;
  layer: string;
  description: string;
  status: "active" | "planned" | "advisory";
  capabilities: string[];
}

interface RegistryData {
  total: number;
  by_status: { active: number; planned: number; advisory: number };
  layers: Record<string, AgentMeta[]>;
  agents: AgentMeta[];
}

interface AgentEvent {
  ts: number;
  agent: string;
  task: string;
  status: "ok" | "error" | "running";
  duration_ms: number;
  summary: string;
  symbols: string[];
  layer: string;
}

interface KpiData {
  win_rate: number;
  profit_factor: number;
  avg_rr: number;
  total_signals: number;
  resolved_signals: number;
  total_wins: number;
  total_losses: number;
  total_profit_pct: number;
  total_loss_pct: number;
  last_updated: string | null;
}

interface CycleScore {
  score: number;
  grade: string;
  ts: number;
  recommendations: string[];
}

interface SchedulerStatus {
  running: boolean;
  cycle_count: number;
  last_run: string | null;
  last_status: string;
}

/* ─── Config ─────────────────────────────────────────────────── */
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

const LAYER_CONFIG: Record<string, { label: string; color: string; bg: string; Icon: React.ElementType }> = {
  management:  { label: "Yönetim",            color: "#bf5af2", bg: "rgba(191,90,242,0.10)",  Icon: Network     },
  engineering: { label: "Mühendislik",         color: "#ff9f0a", bg: "rgba(255,159,10,0.10)",  Icon: Cpu         },
  strategy:    { label: "Strateji & Araştırma",color: "#00d4ff", bg: "rgba(0,212,255,0.10)",   Icon: TrendingUp  },
  growth:      { label: "Büyüme",              color: "#30d158", bg: "rgba(48,209,88,0.10)",   Icon: Megaphone   },
  quality:     { label: "Kalite",              color: "#ffd60a", bg: "rgba(255,214,10,0.10)",  Icon: ShieldCheck },
  ops:         { label: "Operasyon",           color: "#0a84ff", bg: "rgba(10,132,255,0.10)",  Icon: Settings2   },
};

const LAYER_ORDER = ["management", "engineering", "strategy", "growth", "quality", "ops"];

const STATUS_CONFIG = {
  active:   { label: "Aktif",    color: "#30d158", dot: "🟢" },
  planned:  { label: "Planlı",   color: "#ffd60a", dot: "🟡" },
  advisory: { label: "Danışman", color: "#6e6e73", dot: "⚪" },
};

const CYCLE_STEPS = [
  { key: "market_intel",   label: "Market Intelligence", layer: "strategy" },
  { key: "research", label: "Quant Research",       layer: "strategy" },
  { key: "backtest", label: "Combo Testing",        layer: "strategy" },
  { key: "optimize", label: "Strategy Optimizer",   layer: "strategy" },
  { key: "monitor",  label: "Perf. Monitor",        layer: "strategy" },
];

const C = {
  bg: "#000000", card: "#111118", border: "rgba(255,255,255,0.10)",
  text1: "#f5f5f7", text2: "#a1a1a6", text3: "#6e6e73",
};

const GRADE_COLOR: Record<string, string> = { A: "#30d158", B: "#00d4ff", C: "#ffd60a", D: "#ff453a" };

/* ─── Helpers ────────────────────────────────────────────────── */
function timeAgo(tsMs: number): string {
  const s = Math.floor((Date.now() - tsMs) / 1000);
  if (s < 60)  return `${s}s önce`;
  if (s < 3600) return `${Math.floor(s / 60)}dk önce`;
  return `${Math.floor(s / 3600)}sa önce`;
}

function statusColor(s: string) {
  if (s === "ok")      return "#30d158";
  if (s === "error")   return "#ff453a";
  if (s === "running") return "#ffd60a";
  return "#6e6e73";
}

/* ─── Sub-components ─────────────────────────────────────────── */
function AgentCard({ agent, lastEvent }: { agent: AgentMeta; lastEvent?: AgentEvent }) {
  const lc = LAYER_CONFIG[agent.layer];
  const sc = STATUS_CONFIG[agent.status];

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* left accent bar */}
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: lc.color, borderRadius: "10px 0 0 10px" }} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: C.text1, paddingLeft: 4 }}>
          {agent.name}
        </span>
        <span style={{ fontSize: 10, color: sc.color, fontWeight: 600, background: `${sc.color}18`, borderRadius: 4, padding: "1px 6px" }}>
          {sc.dot} {sc.label}
        </span>
      </div>

      <p style={{ fontSize: 11, color: C.text3, lineHeight: 1.4, paddingLeft: 4, margin: 0 }}>
        {agent.description}
      </p>

      {/* capabilities */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 3, paddingLeft: 4 }}>
        {agent.capabilities.slice(0, 3).map((cap) => (
          <span key={cap} style={{ fontSize: 9, color: lc.color, background: lc.bg, borderRadius: 3, padding: "1px 5px" }}>
            {cap}
          </span>
        ))}
      </div>

      {/* last event badge */}
      {lastEvent && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, paddingLeft: 4, marginTop: 2 }}>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: statusColor(lastEvent.status), flexShrink: 0 }} />
          <span style={{ fontSize: 10, color: C.text3 }}>
            {timeAgo(lastEvent.ts)} · {Math.round(lastEvent.duration_ms)}ms
          </span>
        </div>
      )}

      {/* run link (active agents with real task key) */}
      {agent.status === "active" && agent.key !== "advisory" && (
        <Link
          href={`/dashboard/agent`}
          style={{ position: "absolute", bottom: 8, right: 10, fontSize: 10, color: lc.color, display: "flex", alignItems: "center", gap: 2 }}
        >
          Çalıştır <ChevronRight size={10} />
        </Link>
      )}
    </div>
  );
}

function ActivityFeed({ events }: { events: AgentEvent[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {events.length === 0 && (
        <p style={{ color: C.text3, fontSize: 12, textAlign: "center", padding: "20px 0" }}>
          Henüz aktivite yok — bir görev çalıştır
        </p>
      )}
      {events.map((ev, i) => {
        const lc = LAYER_CONFIG[ev.layer] || LAYER_CONFIG.ops;
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              padding: "8px 0",
              borderBottom: i < events.length - 1 ? `1px solid ${C.border}` : "none",
            }}
          >
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor(ev.status), flexShrink: 0, marginTop: 4 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: lc.color }}>{ev.agent}</span>
                <span style={{ fontSize: 10, color: C.text3 }}>{ev.task}</span>
                <span style={{ fontSize: 10, color: C.text3, marginLeft: "auto" }}>{timeAgo(ev.ts)}</span>
              </div>
              {ev.summary && (
                <p style={{ fontSize: 11, color: C.text2, margin: "2px 0 0", lineHeight: 1.35 }}>
                  {ev.summary}
                </p>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                <span style={{ fontSize: 10, color: C.text3 }}>{Math.round(ev.duration_ms)}ms</span>
                {ev.symbols.length > 0 && (
                  <span style={{ fontSize: 10, color: C.text3 }}>· {ev.symbols.slice(0, 3).join(", ")}</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StrategyCycle({ events }: { events: AgentEvent[] }) {
  const lastTaskMap: Record<string, AgentEvent> = {};
  events.forEach((e) => {
    if (!lastTaskMap[e.task]) lastTaskMap[e.task] = e;
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto", padding: "4px 0" }}>
      {CYCLE_STEPS.map((step, i) => {
        const ev = lastTaskMap[step.key];
        const done = !!ev && ev.status === "ok";
        const err  = !!ev && ev.status === "error";
        const lc   = LAYER_CONFIG[step.layer];
        return (
          <div key={step.key} style={{ display: "flex", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, minWidth: 68 }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: done ? lc.color : err ? "#ff453a22" : C.card,
                border: `2px solid ${done ? lc.color : err ? "#ff453a" : C.border}`,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {done ? <CheckCircle2 size={14} color="#000" /> : err ? <AlertCircle size={14} color="#ff453a" /> : <Clock size={14} color={C.text3} />}
              </div>
              <span style={{ fontSize: 9, color: done ? lc.color : C.text3, textAlign: "center", lineHeight: 1.2 }}>
                {step.label}
              </span>
            </div>
            {i < CYCLE_STEPS.length - 1 && (
              <div style={{ width: 20, height: 1, background: done ? lc.color : C.border, flexShrink: 0, marginBottom: 16 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Score Sparkline ────────────────────────────────────────── */
function ScoreSparkline({ scores }: { scores: CycleScore[] }) {
  if (scores.length < 2) return null;
  const data = [...scores].reverse(); // chronological order
  const W = 260, H = 40, PAD = 4;
  const minV = Math.min(...data.map(d => d.score));
  const maxV = Math.max(...data.map(d => d.score));
  const range = Math.max(maxV - minV, 10);
  const xStep = (W - PAD * 2) / (data.length - 1);

  const points = data.map((d, i) => {
    const x = PAD + i * xStep;
    const y = PAD + (1 - (d.score - minV) / range) * (H - PAD * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  const last = data[data.length - 1];
  const lx = PAD + (data.length - 1) * xStep;
  const ly = PAD + (1 - (last.score - minV) / range) * (H - PAD * 2);
  const dotColor = GRADE_COLOR[last.grade] || "#00d4ff";

  return (
    <div style={{ marginTop: 4 }}>
      <div style={{ fontSize: 10, color: C.text3, marginBottom: 4 }}>
        Skor Trendi (son {data.length} cycle)
      </div>
      <svg width={W} height={H} style={{ display: "block", overflow: "visible" }}>
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Fill area */}
        <polygon
          points={`${PAD},${H} ${points} ${PAD + (data.length - 1) * xStep},${H}`}
          fill="url(#sparkGrad)"
        />
        {/* Line */}
        <polyline points={points} fill="none" stroke="#00d4ff" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
        {/* Last point dot */}
        <circle cx={lx} cy={ly} r={3} fill={dotColor} />
      </svg>
    </div>
  );
}

/* ─── KPI Panel ──────────────────────────────────────────────── */
function KpiPanel({ kpis, cycleScores }: { kpis: KpiData | null; cycleScores: CycleScore[] }) {
  if (!kpis) return (
    <p style={{ fontSize: 12, color: C.text3, textAlign: "center", padding: "12px 0" }}>KPI verisi yok</p>
  );

  const latestScore = cycleScores[0];
  const gradeColor = latestScore ? (GRADE_COLOR[latestScore.grade] || C.text3) : C.text3;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {/* Score badge */}
      {latestScore && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, background: `${gradeColor}10`, border: `1px solid ${gradeColor}33`, borderRadius: 8, padding: "8px 12px" }}>
          <Award size={16} color={gradeColor} />
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: gradeColor }}>
              {latestScore.score}/100
              <span style={{ fontSize: 12, marginLeft: 6, background: `${gradeColor}22`, borderRadius: 4, padding: "1px 6px" }}>
                {latestScore.grade}
              </span>
            </div>
            <div style={{ fontSize: 10, color: C.text3 }}>Son Cycle Değerlendirmesi</div>
          </div>
        </div>
      )}

      {/* Score trend sparkline */}
      {cycleScores.length >= 2 && (
        <ScoreSparkline scores={cycleScores} />
      )}

      {/* KPI metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        {[
          { label: "Kazanma Oranı", value: `${kpis.win_rate}%`, color: kpis.win_rate >= 55 ? "#30d158" : kpis.win_rate >= 40 ? "#ffd60a" : "#ff453a" },
          { label: "Profit Factor", value: kpis.profit_factor >= 999 ? "∞" : kpis.profit_factor.toFixed(2), color: kpis.profit_factor >= 1.5 ? "#30d158" : "#ffd60a" },
          { label: "Ort. R/R",      value: kpis.avg_rr.toFixed(2), color: "#00d4ff" },
          { label: "Toplam Sinyal", value: kpis.total_signals.toString(), color: C.text2 },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "#0a0a0f", borderRadius: 7, padding: "7px 10px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: 10, color: C.text3 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Win/Loss bar */}
      {kpis.resolved_signals > 0 && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: C.text3, marginBottom: 4 }}>
            <span>✅ {kpis.total_wins} kazanç</span>
            <span>❌ {kpis.total_losses} kayıp</span>
          </div>
          <div style={{ height: 5, borderRadius: 3, background: "#ff453a44", overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${kpis.win_rate}%`, background: "#30d158", borderRadius: 3 }} />
          </div>
        </div>
      )}

      {/* Recommendations */}
      {latestScore?.recommendations.length > 0 && (
        <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 8 }}>
          {latestScore.recommendations.map((rec, i) => (
            <p key={i} style={{ fontSize: 10, color: C.text2, margin: "2px 0", lineHeight: 1.4 }}>
              💡 {rec}
            </p>
          ))}
        </div>
      )}

      {kpis.last_updated && (
        <p style={{ fontSize: 10, color: C.text3, margin: 0 }}>Güncelleme: {kpis.last_updated}</p>
      )}
    </div>
  );
}

/* ─── Scheduler Panel ────────────────────────────────────────── */
function SchedulerPanel({ status, onRefresh }: { status: SchedulerStatus | null; onRefresh: () => void }) {
  const [symbols, setSymbols] = useState("THYAO.IS, KCHOL.IS, SISE.IS");
  const [interval, setIntervalMin] = useState(60);
  const [busy, setBusy] = useState(false);

  const start = async () => {
    setBusy(true);
    try {
      const syms = symbols.split(",").map(s => s.trim()).filter(Boolean);
      const params = new URLSearchParams();
      syms.forEach(s => params.append("symbols", s));
      params.append("interval_minutes", String(interval));
      await fetch(`${API}/api/v1/agent/scheduler/start?${params}`, { method: "POST" });
      onRefresh();
    } finally { setBusy(false); }
  };

  const stop = async () => {
    setBusy(true);
    try {
      await fetch(`${API}/api/v1/agent/scheduler/stop`, { method: "POST" });
      onRefresh();
    } finally { setBusy(false); }
  };

  const isRunning = status?.running ?? false;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {/* Status indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: isRunning ? "#30d158" : C.text3, boxShadow: isRunning ? "0 0 6px #30d158" : "none" }} />
        <span style={{ fontSize: 13, color: isRunning ? "#30d158" : C.text2, fontWeight: 600 }}>
          {isRunning ? "Çalışıyor" : "Durduruldu"}
        </span>
        {status && (
          <span style={{ fontSize: 11, color: C.text3, marginLeft: "auto" }}>
            #{status.cycle_count} cycle
          </span>
        )}
      </div>

      {status?.last_run && (
        <p style={{ fontSize: 11, color: C.text3, margin: 0 }}>Son çalışma: {status.last_run}</p>
      )}

      {/* Controls */}
      {!isRunning && (
        <>
          <div>
            <label style={{ fontSize: 10, color: C.text3, display: "block", marginBottom: 4 }}>Semboller</label>
            <input
              value={symbols}
              onChange={e => setSymbols(e.target.value)}
              style={{ width: "100%", background: "#0a0a0f", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 8px", color: C.text1, fontSize: 11, boxSizing: "border-box" }}
              placeholder="THYAO.IS, KCHOL.IS"
            />
          </div>
          <div>
            <label style={{ fontSize: 10, color: C.text3, display: "block", marginBottom: 4 }}>Aralık (dakika)</label>
            <input
              type="number"
              value={interval}
              onChange={e => setIntervalMin(Number(e.target.value))}
              min={5} max={1440}
              style={{ width: "100%", background: "#0a0a0f", border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 8px", color: C.text1, fontSize: 11, boxSizing: "border-box" }}
            />
          </div>
        </>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        {!isRunning ? (
          <button
            onClick={start}
            disabled={busy}
            style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, background: "rgba(48,209,88,0.12)", border: "1px solid rgba(48,209,88,0.3)", borderRadius: 7, padding: "8px 0", color: "#30d158", fontSize: 12, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer" }}
          >
            {busy ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
            Başlat
          </button>
        ) : (
          <button
            onClick={stop}
            disabled={busy}
            style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, background: "rgba(255,69,58,0.12)", border: "1px solid rgba(255,69,58,0.3)", borderRadius: 7, padding: "8px 0", color: "#ff453a", fontSize: 12, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer" }}
          >
            {busy ? <Loader2 size={12} className="animate-spin" /> : <Square size={12} />}
            Durdur
          </button>
        )}
        <button
          onClick={onRefresh}
          style={{ background: "#1a1a24", border: `1px solid ${C.border}`, borderRadius: 7, padding: "8px 10px", color: C.text3, cursor: "pointer", display: "flex", alignItems: "center" }}
          title="Durumu yenile"
        >
          <RefreshCw size={13} />
        </button>
      </div>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────────── */
export default function AgentHubPage() {
  const [registry, setRegistry] = useState<RegistryData | null>(null);
  const [events,   setEvents]   = useState<AgentEvent[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [lastRefresh, setLastRefresh] = useState(0);
  const [kpis,     setKpis]     = useState<KpiData | null>(null);
  const [cycleScores, setCycleScores] = useState<CycleScore[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);

  const fetchRegistry = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/registry`);
      if (!res.ok) throw new Error(`${res.status}`);
      setRegistry(await res.json());
    } catch (e) {
      setError(`Registry yüklenemedi: ${e}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/events?limit=30`);
      if (!res.ok) return;
      const data = await res.json();
      setEvents(data.events || []);
      setLastRefresh(Date.now());
    } catch {
      // silently ignore — events are non-critical
    }
  }, []);

  const fetchKpis = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/kpis`);
      if (!res.ok) return;
      const data = await res.json();
      setKpis(data.kpis || null);
      setCycleScores(data.cycle_scores || []);
    } catch { /* non-critical */ }
  }, []);

  const fetchSchedulerStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/scheduler`);
      if (!res.ok) return;
      setSchedulerStatus(await res.json());
    } catch { /* non-critical */ }
  }, []);

  useEffect(() => {
    fetchRegistry();
    fetchEvents();
    fetchKpis();
    fetchSchedulerStatus();
    const interval = setInterval(() => {
      fetchEvents();
      fetchKpis();
      fetchSchedulerStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchRegistry, fetchEvents, fetchKpis, fetchSchedulerStatus]);

  // Build "last event per agent" lookup
  const lastEventByAgent: Record<string, AgentEvent> = {};
  events.forEach((ev) => {
    if (!lastEventByAgent[ev.agent]) lastEventByAgent[ev.agent] = ev;
  });

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", color: C.text2 }}>
      <Loader2 size={20} className="animate-spin" style={{ marginRight: 10 }} />
      Agent Hub yükleniyor…
    </div>
  );

  if (error && !registry) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", color: "#ff453a", flexDirection: "column", gap: 8 }}>
      <AlertCircle size={28} />
      <span style={{ fontSize: 14 }}>{error}</span>
      <span style={{ fontSize: 12, color: C.text3 }}>API çalışıyor mu? <code>http://localhost:8001/api/v1/agent/registry</code></span>
    </div>
  );

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text1, padding: "24px 20px" }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Network size={22} color="#00d4ff" />
            <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text1, margin: 0 }}>FinPilot Agent Hub</h1>
          </div>
          <p style={{ fontSize: 13, color: C.text2, margin: "4px 0 0" }}>
            23-agent sanal şirket — 6 katman, tek orkestratör
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link
            href="/dashboard/agent"
            style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#00d4ff", background: "rgba(0,212,255,0.10)", border: "1px solid rgba(0,212,255,0.25)", borderRadius: 8, padding: "7px 14px", textDecoration: "none" }}
          >
            <Play size={13} /> Görev Çalıştır
          </Link>
          <button
            onClick={fetchEvents}
            style={{ background: "#1a1a24", border: `1px solid ${C.border}`, borderRadius: 8, padding: "7px 10px", color: C.text3, cursor: "pointer", display: "flex", alignItems: "center" }}
            title="Olayları yenile"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* ── Status bar ── */}
      {registry && (
        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          {[
            { label: "Aktif Agent",    count: registry.by_status.active,   color: "#30d158", icon: CheckCircle2 },
            { label: "Planlı",         count: registry.by_status.planned,  color: "#ffd60a", icon: Clock        },
            { label: "Danışman",       count: registry.by_status.advisory, color: "#6e6e73", icon: Lightbulb    },
            { label: "Son Aktivite",   count: events.length,               color: "#0a84ff", icon: Activity     },
          ].map(({ label, count, color, icon: Icon }) => (
            <div key={label} style={{ flex: 1, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
              <Icon size={16} color={color} />
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color }}>{count}</div>
                <div style={{ fontSize: 11, color: C.text3 }}>{label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Main layout ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, alignItems: "start" }}>

        {/* LEFT — Agent grid */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {registry && LAYER_ORDER.map((layerKey) => {
            const agents = registry.layers[layerKey] || [];
            const lc = LAYER_CONFIG[layerKey];
            const { Icon } = lc;
            return (
              <div key={layerKey}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Icon size={14} color={lc.color} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: lc.color, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    {lc.label}
                  </span>
                  <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${lc.color}44, transparent)` }} />
                  <span style={{ fontSize: 11, color: C.text3 }}>{agents.length} agent</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
                  {agents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      lastEvent={lastEventByAgent[agent.name]}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* RIGHT — Sidebar panels */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, position: "sticky", top: 20 }}>

          {/* Scheduler kontrolü */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
              <Activity size={14} color="#30d158" />
              <span style={{ fontSize: 12, fontWeight: 700, color: "#30d158", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Otonom Scheduler
              </span>
            </div>
            <SchedulerPanel status={schedulerStatus} onRefresh={() => { fetchSchedulerStatus(); fetchEvents(); }} />
          </div>

          {/* KPI & self-evaluation */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
              <BarChart2 size={14} color="#bf5af2" />
              <span style={{ fontSize: 12, fontWeight: 700, color: "#bf5af2", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                KPI & Değerlendirme
              </span>
            </div>
            <KpiPanel kpis={kpis} cycleScores={cycleScores} />
          </div>

          {/* Strateji döngüsü */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
              <TrendingUp size={14} color="#00d4ff" />
              <span style={{ fontSize: 12, fontWeight: 700, color: "#00d4ff", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Strateji Döngüsü
              </span>
            </div>
            <StrategyCycle events={events} />
            <p style={{ fontSize: 10, color: C.text3, margin: "10px 0 0", lineHeight: 1.4 }}>
              Market Intel → Quant → Combo Test → Optimizer → Monitor
            </p>
          </div>

          {/* Aktivite akışı */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Activity size={14} color="#0a84ff" />
                <span style={{ fontSize: 12, fontWeight: 700, color: "#0a84ff", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  Canlı Aktivite
                </span>
              </div>
              {lastRefresh > 0 && (
                <span style={{ fontSize: 10, color: C.text3 }}>
                  {timeAgo(lastRefresh)}
                </span>
              )}
            </div>
            <ActivityFeed events={events.slice(0, 15)} />
          </div>

          {/* Quick stats */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: C.text2, margin: "0 0 10px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Hızlı Erişim
            </p>
            {[
              { label: "Görev Çalıştır",   href: "/dashboard/agent",    color: "#00d4ff" },
              { label: "Advisory Panel",   href: "/dashboard/advisory", color: "#bf5af2" },
              { label: "Scanner",          href: "/dashboard/scanner",  color: "#6e6e73" },
              { label: "AI Analysis",      href: "/dashboard/analysis", color: "#0a84ff" },
              { label: "Backtest",         href: "/dashboard/backtest", color: "#30d158" },
            ].map(({ label, href, color }) => (
              <Link
                key={href}
                href={href}
                style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid ${C.border}`, color, textDecoration: "none", fontSize: 13 }}
              >
                {label} <ChevronRight size={12} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Types ──────────────────────────────────────────────────── */
interface AgentMeta {
  id: number;
  name: string;
  key: string;
  layer: string;
  description: string;
  status: "active" | "planned" | "advisory";
  capabilities: string[];
}

interface RegistryData {
  total: number;
  by_status: { active: number; planned: number; advisory: number };
  layers: Record<string, AgentMeta[]>;
  agents: AgentMeta[];
}

interface AgentEvent {
  ts: number;
  agent: string;
  task: string;
  status: "ok" | "error" | "running";
  duration_ms: number;
  summary: string;
  symbols: string[];
  layer: string;
}

/* ─── Config ─────────────────────────────────────────────────── */
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

const LAYER_CONFIG: Record<string, { label: string; color: string; bg: string; Icon: React.ElementType }> = {
  management:  { label: "Yönetim",            color: "#bf5af2", bg: "rgba(191,90,242,0.10)",  Icon: Network     },
  engineering: { label: "Mühendislik",         color: "#ff9f0a", bg: "rgba(255,159,10,0.10)",  Icon: Cpu         },
  strategy:    { label: "Strateji & Araştırma",color: "#00d4ff", bg: "rgba(0,212,255,0.10)",   Icon: TrendingUp  },
  growth:      { label: "Büyüme",              color: "#30d158", bg: "rgba(48,209,88,0.10)",   Icon: Megaphone   },
  quality:     { label: "Kalite",              color: "#ffd60a", bg: "rgba(255,214,10,0.10)",  Icon: ShieldCheck },
  ops:         { label: "Operasyon",           color: "#0a84ff", bg: "rgba(10,132,255,0.10)",  Icon: Settings2   },
};

const LAYER_ORDER = ["management", "engineering", "strategy", "growth", "quality", "ops"];

const STATUS_CONFIG = {
  active:   { label: "Aktif",    color: "#30d158", dot: "🟢" },
  planned:  { label: "Planlı",   color: "#ffd60a", dot: "🟡" },
  advisory: { label: "Danışman", color: "#6e6e73", dot: "⚪" },
};

const CYCLE_STEPS = [
  { key: "market_intel",   label: "Market Intelligence", layer: "strategy" },
  { key: "research", label: "Quant Research",       layer: "strategy" },
  { key: "backtest", label: "Combo Testing",        layer: "strategy" },
  { key: "optimize", label: "Strategy Optimizer",   layer: "strategy" },
  { key: "monitor",  label: "Perf. Monitor",        layer: "strategy" },
];

const C = {
  bg: "#000000", card: "#111118", border: "rgba(255,255,255,0.10)",
  text1: "#f5f5f7", text2: "#a1a1a6", text3: "#6e6e73",
};

/* ─── Helpers ────────────────────────────────────────────────── */
function timeAgo(tsMs: number): string {
  const s = Math.floor((Date.now() - tsMs) / 1000);
  if (s < 60)  return `${s}s önce`;
  if (s < 3600) return `${Math.floor(s / 60)}dk önce`;
  return `${Math.floor(s / 3600)}sa önce`;
}

function statusColor(s: string) {
  if (s === "ok")      return "#30d158";
  if (s === "error")   return "#ff453a";
  if (s === "running") return "#ffd60a";
  return "#6e6e73";
}

/* ─── Sub-components ─────────────────────────────────────────── */
function AgentCard({ agent, lastEvent }: { agent: AgentMeta; lastEvent?: AgentEvent }) {
  const lc = LAYER_CONFIG[agent.layer];
  const sc = STATUS_CONFIG[agent.status];

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* left accent bar */}
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: lc.color, borderRadius: "10px 0 0 10px" }} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: C.text1, paddingLeft: 4 }}>
          {agent.name}
        </span>
        <span style={{ fontSize: 10, color: sc.color, fontWeight: 600, background: `${sc.color}18`, borderRadius: 4, padding: "1px 6px" }}>
          {sc.dot} {sc.label}
        </span>
      </div>

      <p style={{ fontSize: 11, color: C.text3, lineHeight: 1.4, paddingLeft: 4, margin: 0 }}>
        {agent.description}
      </p>

      {/* capabilities */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 3, paddingLeft: 4 }}>
        {agent.capabilities.slice(0, 3).map((cap) => (
          <span key={cap} style={{ fontSize: 9, color: lc.color, background: lc.bg, borderRadius: 3, padding: "1px 5px" }}>
            {cap}
          </span>
        ))}
      </div>

      {/* last event badge */}
      {lastEvent && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, paddingLeft: 4, marginTop: 2 }}>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: statusColor(lastEvent.status), flexShrink: 0 }} />
          <span style={{ fontSize: 10, color: C.text3 }}>
            {timeAgo(lastEvent.ts)} · {Math.round(lastEvent.duration_ms)}ms
          </span>
        </div>
      )}

      {/* run link (active agents with real task key) */}
      {agent.status === "active" && agent.key !== "advisory" && (
        <Link
          href={`/dashboard/agent`}
          style={{ position: "absolute", bottom: 8, right: 10, fontSize: 10, color: lc.color, display: "flex", alignItems: "center", gap: 2 }}
        >
          Çalıştır <ChevronRight size={10} />
        </Link>
      )}
    </div>
  );
}

function ActivityFeed({ events }: { events: AgentEvent[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {events.length === 0 && (
        <p style={{ color: C.text3, fontSize: 12, textAlign: "center", padding: "20px 0" }}>
          Henüz aktivite yok — bir görev çalıştır
        </p>
      )}
      {events.map((ev, i) => {
        const lc = LAYER_CONFIG[ev.layer] || LAYER_CONFIG.ops;
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              padding: "8px 0",
              borderBottom: i < events.length - 1 ? `1px solid ${C.border}` : "none",
            }}
          >
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor(ev.status), flexShrink: 0, marginTop: 4 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: lc.color }}>{ev.agent}</span>
                <span style={{ fontSize: 10, color: C.text3 }}>{ev.task}</span>
                <span style={{ fontSize: 10, color: C.text3, marginLeft: "auto" }}>{timeAgo(ev.ts)}</span>
              </div>
              {ev.summary && (
                <p style={{ fontSize: 11, color: C.text2, margin: "2px 0 0", lineHeight: 1.35 }}>
                  {ev.summary}
                </p>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                <span style={{ fontSize: 10, color: C.text3 }}>{Math.round(ev.duration_ms)}ms</span>
                {ev.symbols.length > 0 && (
                  <span style={{ fontSize: 10, color: C.text3 }}>· {ev.symbols.slice(0, 3).join(", ")}</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StrategyCycle({ events }: { events: AgentEvent[] }) {
  const lastTaskMap: Record<string, AgentEvent> = {};
  events.forEach((e) => {
    if (!lastTaskMap[e.task]) lastTaskMap[e.task] = e;
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto", padding: "4px 0" }}>
      {CYCLE_STEPS.map((step, i) => {
        const ev = lastTaskMap[step.key];
        const done = !!ev && ev.status === "ok";
        const err  = !!ev && ev.status === "error";
        const lc   = LAYER_CONFIG[step.layer];
        return (
          <div key={step.key} style={{ display: "flex", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, minWidth: 68 }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: done ? lc.color : err ? "#ff453a22" : C.card,
                border: `2px solid ${done ? lc.color : err ? "#ff453a" : C.border}`,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {done ? <CheckCircle2 size={14} color="#000" /> : err ? <AlertCircle size={14} color="#ff453a" /> : <Clock size={14} color={C.text3} />}
              </div>
              <span style={{ fontSize: 9, color: done ? lc.color : C.text3, textAlign: "center", lineHeight: 1.2 }}>
                {step.label}
              </span>
            </div>
            {i < CYCLE_STEPS.length - 1 && (
              <div style={{ width: 20, height: 1, background: done ? lc.color : C.border, flexShrink: 0, marginBottom: 16 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────────── */
export default function AgentHubPage() {
  const [registry, setRegistry] = useState<RegistryData | null>(null);
  const [events,   setEvents]   = useState<AgentEvent[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [lastRefresh, setLastRefresh] = useState(0);

  const fetchRegistry = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/registry`);
      if (!res.ok) throw new Error(`${res.status}`);
      setRegistry(await res.json());
    } catch (e) {
      setError(`Registry yüklenemedi: ${e}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/agent/events?limit=30`);
      if (!res.ok) return;
      const data = await res.json();
      setEvents(data.events || []);
      setLastRefresh(Date.now());
    } catch {
      // silently ignore — events are non-critical
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
    fetchEvents();
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, [fetchRegistry, fetchEvents]);

  // Build "last event per agent" lookup
  const lastEventByAgent: Record<string, AgentEvent> = {};
  const agentNameToKey: Record<string, string> = {
    "CEO": "full", "Quant Research": "research", "Combination Testing": "backtest",
    "Documentation": "report", "CEO orchestrated": "full",
  };
  events.forEach((ev) => {
    if (!lastEventByAgent[ev.agent]) lastEventByAgent[ev.agent] = ev;
  });

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", color: C.text2 }}>
      <Loader2 size={20} className="animate-spin" style={{ marginRight: 10 }} />
      Agent Hub yükleniyor…
    </div>
  );

  if (error && !registry) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", color: "#ff453a", flexDirection: "column", gap: 8 }}>
      <AlertCircle size={28} />
      <span style={{ fontSize: 14 }}>{error}</span>
      <span style={{ fontSize: 12, color: C.text3 }}>API çalışıyor mu? <code>http://localhost:8001/api/v1/agent/registry</code></span>
    </div>
  );

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text1, padding: "24px 20px" }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Network size={22} color="#00d4ff" />
            <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text1, margin: 0 }}>FinPilot Agent Hub</h1>
          </div>
          <p style={{ fontSize: 13, color: C.text2, margin: "4px 0 0" }}>
            23-agent sanal şirket — 6 katman, tek orkestratör
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link
            href="/dashboard/agent"
            style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#00d4ff", background: "rgba(0,212,255,0.10)", border: "1px solid rgba(0,212,255,0.25)", borderRadius: 8, padding: "7px 14px", textDecoration: "none" }}
          >
            <Play size={13} /> Görev Çalıştır
          </Link>
          <button
            onClick={fetchEvents}
            style={{ background: "#1a1a24", border: `1px solid ${C.border}`, borderRadius: 8, padding: "7px 10px", color: C.text3, cursor: "pointer", display: "flex", alignItems: "center" }}
            title="Olayları yenile"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* ── Status bar ── */}
      {registry && (
        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          {[
            { label: "Aktif Agent",    count: registry.by_status.active,   color: "#30d158", icon: CheckCircle2 },
            { label: "Planlı",         count: registry.by_status.planned,  color: "#ffd60a", icon: Clock        },
            { label: "Danışman",       count: registry.by_status.advisory, color: "#6e6e73", icon: Lightbulb    },
            { label: "Son Aktivite",   count: events.length,               color: "#0a84ff", icon: Activity     },
          ].map(({ label, count, color, icon: Icon }) => (
            <div key={label} style={{ flex: 1, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
              <Icon size={16} color={color} />
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color }}>{count}</div>
                <div style={{ fontSize: 11, color: C.text3 }}>{label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Main layout ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, alignItems: "start" }}>

        {/* LEFT — Agent grid */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {registry && LAYER_ORDER.map((layerKey) => {
            const agents = registry.layers[layerKey] || [];
            const lc = LAYER_CONFIG[layerKey];
            const { Icon } = lc;
            return (
              <div key={layerKey}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Icon size={14} color={lc.color} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: lc.color, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    {lc.label}
                  </span>
                  <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${lc.color}44, transparent)` }} />
                  <span style={{ fontSize: 11, color: C.text3 }}>{agents.length} agent</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
                  {agents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      lastEvent={lastEventByAgent[agent.name]}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* RIGHT — Activity feed + cycle */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, position: "sticky", top: 20 }}>

          {/* Strateji döngüsü */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
              <TrendingUp size={14} color="#00d4ff" />
              <span style={{ fontSize: 12, fontWeight: 700, color: "#00d4ff", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Strateji Döngüsü
              </span>
            </div>
            <StrategyCycle events={events} />
            <p style={{ fontSize: 10, color: C.text3, margin: "10px 0 0", lineHeight: 1.4 }}>
              Market Intel → Quant → Combo Test → Optimizer → Monitor
            </p>
          </div>

          {/* Aktivite akışı */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Activity size={14} color="#0a84ff" />
                <span style={{ fontSize: 12, fontWeight: 700, color: "#0a84ff", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  Canlı Aktivite
                </span>
              </div>
              {lastRefresh > 0 && (
                <span style={{ fontSize: 10, color: C.text3 }}>
                  {timeAgo(lastRefresh)}
                </span>
              )}
            </div>
            <ActivityFeed events={events.slice(0, 15)} />
          </div>

          {/* Quick stats */}
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: C.text2, margin: "0 0 10px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Hızlı Erişim
            </p>
            {[
              { label: "Görev Çalıştır",   href: "/dashboard/agent",    color: "#00d4ff" },
              { label: "Scanner",          href: "/dashboard/scanner",  color: "#bf5af2" },
              { label: "AI Analysis",      href: "/dashboard/analysis", color: "#0a84ff" },
              { label: "Backtest",         href: "/dashboard/backtest", color: "#30d158" },
            ].map(({ label, href, color }) => (
              <Link
                key={href}
                href={href}
                style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid ${C.border}`, color, textDecoration: "none", fontSize: 13 }}
              >
                {label} <ChevronRight size={12} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
