"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Activity, BarChart3, TrendingUp, Gauge, RefreshCw, AlertTriangle, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { C } from "@/lib/stockData";

interface BandDetail {
  lo: number;
  hi: number;
  n: number;
  raw_p: number;
  p: number;
}

interface DecileEntry {
  decile: number;
  n: number;
  score_range: [number, number];
  win_rate: number;
  lift: number;
}

interface BrierEntry {
  ts: number;
  brier: number;
}

interface CalibrationStats {
  fitted: boolean;
  n_samples: number;
  brier: number | null;
  ece: number | null;
  bands: BandDetail[];
  decile_lift: {
    overall_win_rate: number;
    n_resolved: number;
    n_deciles: number;
    deciles: DecileEntry[];
    top_decile_lift: number;
    bottom_decile_lift: number;
  };
  brier_history: BrierEntry[];
}

function HoverCard({ children, className = "", style = {}, ...rest }: React.ComponentProps<"div">) {
  return (
    <div
      className={className}
      style={{ border: `1px solid ${C.border}`, backgroundColor: C.card, transition: "border-color 0.2s, background-color 0.2s", ...style }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.borderHover; e.currentTarget.style.backgroundColor = C.cardHover; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.backgroundColor = C.card; }}
      {...rest}
    >
      {children}
    </div>
  );
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "#0a0a12", border: `1px solid ${C.border}` }}>
      <div className="text-xs mb-1" style={{ color: C.text3 }}>{label}</div>
      <div className="text-xl font-bold" style={{ color: color ?? C.text1 }}>{value}</div>
      {sub && <div className="text-xs mt-0.5" style={{ color: C.text3 }}>{sub}</div>}
    </div>
  );
}

export default function CalibrationPage() {
  const [stats, setStats] = useState<CalibrationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [qualityGate, setQualityGate] = useState<{ degraded: boolean; reason: string | null } | null>(null);
  const [champion, setChampion] = useState<any>(null);

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const [statsRes, gateRes, edgeRes] = await Promise.all([
        fetch("/py-api/loop/calibration/stats"),
        fetch("/py-api/loop/status"),
        fetch("/py-api/loop/champion/edge"),
      ]);
      if (statsRes.ok) {
        const data = await statsRes.json() as CalibrationStats;
        setStats(data);
      }
      if (gateRes.ok) {
        const gateData = await gateRes.json();
        setQualityGate(gateData.quality_gate ?? null);
      }
      if (edgeRes.ok) {
        const edgeData = await edgeRes.json();
        setChampion(edgeData);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Activity size={28} className="animate-spin" style={{ color: C.cyan }} />
      </div>
    );
  }

  const brier = stats?.brier ?? null;
  const ece = stats?.ece ?? null;
  const topLift = stats?.decile_lift?.top_decile_lift ?? null;
  const overallWR = stats?.decile_lift?.overall_win_rate ?? 0;

  const brierColor = brier == null ? C.text3 : brier < 0.2 ? C.green : brier < 0.25 ? C.yellow : C.red;
  const eceColor = ece == null ? C.text3 : ece < 0.05 ? C.green : ece < 0.10 ? C.yellow : C.red;
  const liftColor = topLift == null ? C.text3 : topLift > 1.5 ? C.green : topLift > 1.0 ? C.yellow : C.red;

  const history = stats?.brier_history ?? [];
  const last7 = history.slice(-7);
  const last30 = history.slice(-30);
  const avg7 = last7.length ? last7.reduce((s, e) => s + e.brier, 0) / last7.length : null;
  const avg30 = last30.length ? last30.reduce((s, e) => s + e.brier, 0) / last30.length : null;

  const deciles = stats?.decile_lift?.deciles ?? [];
  const maxLift = deciles.length ? Math.max(...deciles.map((d) => d.lift), 1.5) : 2;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: C.text1 }}>Calibration Quality</h1>
          <p className="text-sm" style={{ color: C.text3 }}>
            Score → P(win) calibration metrics · {stats?.n_samples ?? 0} resolved signals
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm"
          style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, color: C.cyan }}
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Quality Gate Banner */}
      {qualityGate?.degraded && (
        <div className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ backgroundColor: "rgba(255,69,58,0.12)", border: `1px solid ${C.red}` }}>
          <AlertTriangle size={16} style={{ color: C.red }} />
          <div>
            <span className="text-sm font-semibold" style={{ color: C.red }}>Quality Gate DEGRADED</span>
            <span className="ml-2 text-xs" style={{ color: C.text3 }}>{qualityGate.reason}</span>
          </div>
          <Link href="/dashboard/autonomy" className="ml-auto text-xs" style={{ color: C.cyan }}>
            Manage →
          </Link>
        </div>
      )}

      {/* Sprint 16 (S16-06): Champion Edge Tile — live self-improving loop visibility */}
      {champion && (
        <HoverCard className="rounded-xl p-4">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wide" style={{ color: C.text3 }}>Champion Edge (30d)</div>
              <div className="text-sm font-semibold" style={{ color: C.text1 }}>
                {champion.champion?.name ?? "no champion promoted yet"}
                {champion.champion?.promoted_at && (
                  <span className="ml-2 text-xs font-normal" style={{ color: C.text3 }}>
                    · since {champion.champion.promoted_at}
                  </span>
                )}
              </div>
            </div>
            <Link href="/dashboard/autonomy" className="text-xs" style={{ color: C.cyan }}>Audit →</Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard
              label="Brier (30d)"
              value={champion.edge?.brier_30d != null ? champion.edge.brier_30d.toFixed(4) : "—"}
              sub={`${champion.edge?.resolved_signals_30d ?? 0} resolved`}
              color={champion.edge?.brier_30d == null ? C.text3 : champion.edge.brier_30d < 0.2 ? C.green : champion.edge.brier_30d < 0.25 ? C.yellow : C.red}
            />
            <MetricCard
              label="Paper PnL (30d)"
              value={champion.edge?.paper_pnl_30d_pct != null ? `${champion.edge.paper_pnl_30d_pct >= 0 ? "+" : ""}${champion.edge.paper_pnl_30d_pct.toFixed(2)}%` : "—"}
              sub="closed trades"
              color={champion.edge?.paper_pnl_30d_pct == null ? C.text3 : champion.edge.paper_pnl_30d_pct >= 0 ? C.green : C.red}
            />
            <MetricCard
              label="Paper PnL (all)"
              value={champion.edge?.paper_pnl_total_pct != null ? `${champion.edge.paper_pnl_total_pct >= 0 ? "+" : ""}${champion.edge.paper_pnl_total_pct.toFixed(2)}%` : "—"}
              sub="lifetime"
              color={champion.edge?.paper_pnl_total_pct == null ? C.text3 : champion.edge.paper_pnl_total_pct >= 0 ? C.green : C.red}
            />
            <MetricCard
              label="Win Rate (life)"
              value={champion.lifetime_kpis?.win_rate != null ? `${champion.lifetime_kpis.win_rate.toFixed(1)}%` : "—"}
              sub={`PF ${champion.lifetime_kpis?.profit_factor ?? "—"}`}
              color={champion.lifetime_kpis?.win_rate == null ? C.text3 : champion.lifetime_kpis.win_rate >= 55 ? C.green : champion.lifetime_kpis.win_rate >= 50 ? C.yellow : C.red}
            />
          </div>
        </HoverCard>
      )}

      {/* KPI Summary Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          label="Brier Score"
          value={brier != null ? brier.toFixed(4) : "—"}
          sub="< 0.20 = good"
          color={brierColor}
        />
        <MetricCard
          label="ECE"
          value={ece != null ? ece.toFixed(4) : "—"}
          sub="< 0.05 = well-calibrated"
          color={eceColor}
        />
        <MetricCard
          label="Top Decile Lift"
          value={topLift != null ? topLift.toFixed(2) + "×" : "—"}
          sub="> 1.5 = strong signal quality"
          color={liftColor}
        />
        <MetricCard
          label="Overall Win Rate"
          value={overallWR > 0 ? (overallWR * 100).toFixed(1) + "%" : "—"}
          sub={`${stats?.decile_lift?.n_resolved ?? 0} resolved`}
          color={overallWR >= 0.55 ? C.green : overallWR >= 0.45 ? C.yellow : overallWR > 0 ? C.red : C.text3}
        />
      </div>

      {/* Brier History Trend */}
      {history.length > 0 && (
        <HoverCard className="rounded-2xl p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={15} style={{ color: C.cyan }} />
              <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>Brier History</h2>
            </div>
            <div className="flex gap-4 text-xs" style={{ color: C.text3 }}>
              {avg7 != null && (
                <span>7d avg: <strong style={{ color: avg7 < 0.22 ? C.green : C.yellow }}>{avg7.toFixed(4)}</strong></span>
              )}
              {avg30 != null && (
                <span>30d avg: <strong style={{ color: avg30 < 0.22 ? C.green : C.yellow }}>{avg30.toFixed(4)}</strong></span>
              )}
            </div>
          </div>
          <div className="flex items-end gap-1 h-16">
            {last30.map((e, i) => {
              const vals = last30.map((h) => h.brier);
              const maxB = Math.max(...vals, 0.30);
              const minB = Math.min(...vals, 0.10);
              const pct = maxB > minB ? ((e.brier - minB) / (maxB - minB)) * 100 : 50;
              const barColor = e.brier < 0.20 ? C.green : e.brier < 0.25 ? C.yellow : C.red;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-sm"
                  title={`${new Date(e.ts * 1000).toLocaleDateString()} — Brier: ${e.brier.toFixed(4)}`}
                  style={{ height: `${Math.max(10, pct)}%`, backgroundColor: barColor, opacity: 0.8 }}
                />
              );
            })}
          </div>
          <div className="mt-1 text-xs" style={{ color: C.text3 }}>Last {last30.length} calibration runs (lower is better)</div>
        </HoverCard>
      )}

      {/* Score Bands Table */}
      {(stats?.bands ?? []).length > 0 && (
        <HoverCard className="rounded-2xl p-5">
          <div className="mb-4 flex items-center gap-2">
            <BarChart3 size={15} style={{ color: C.cyan }} />
            <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>Score Band Calibration</h2>
          </div>
          <div className="space-y-2">
            {(stats?.bands ?? []).map((band, i) => {
              const barPct = Math.round(band.p * 100);
              const rawPct = Math.round(band.raw_p * 100);
              const isMono = band.p >= band.raw_p;
              return (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-20 text-xs text-right font-mono" style={{ color: C.text3 }}>
                    {band.lo}–{band.hi}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-5 rounded"
                        style={{
                          width: `${Math.max(barPct, 2)}%`,
                          backgroundColor: barPct >= 60 ? C.green : barPct >= 45 ? C.cyan : C.yellow,
                          opacity: 0.85,
                        }}
                      />
                      <span className="text-xs font-semibold" style={{ color: C.text1 }}>{barPct}%</span>
                      <span className="text-xs" style={{ color: C.text3 }}>
                        raw {rawPct}% {!isMono && <span style={{ color: C.yellow }}>↗ mono</span>}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs w-14 text-right" style={{ color: C.text3 }}>n={band.n}</div>
                </div>
              );
            })}
          </div>
        </HoverCard>
      )}

      {/* Decile Lift */}
      {deciles.length > 0 && (
        <HoverCard className="rounded-2xl p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Gauge size={15} style={{ color: C.cyan }} />
              <h2 className="text-sm font-semibold" style={{ color: C.text1 }}>Decile Lift</h2>
            </div>
            <span className="text-xs" style={{ color: C.text3 }}>D1 = highest score bucket · lift vs. avg win rate</span>
          </div>
          <div className="space-y-1.5">
            {deciles.map((d) => {
              const pct = Math.min(100, (d.lift / maxLift) * 100);
              const color = d.lift > 1.5 ? C.green : d.lift > 1.0 ? C.cyan : d.lift > 0.7 ? C.yellow : C.red;
              return (
                <div key={d.decile} className="flex items-center gap-3">
                  <div className="w-10 text-xs text-right font-medium" style={{ color: C.text3 }}>D{d.decile}</div>
                  <div className="flex-1 h-5 rounded overflow-hidden" style={{ backgroundColor: "#0a0a12" }}>
                    <div className="h-full rounded" style={{ width: `${Math.max(pct, 2)}%`, backgroundColor: color, opacity: 0.8 }} />
                  </div>
                  <div className="w-14 text-xs font-semibold text-right" style={{ color }}>{d.lift.toFixed(2)}×</div>
                  <div className="w-16 text-xs text-right" style={{ color: C.text3 }}>{(d.win_rate * 100).toFixed(0)}% WR</div>
                  <div className="w-10 text-xs text-right" style={{ color: C.text3 }}>n={d.n}</div>
                </div>
              );
            })}
          </div>
          <div className="mt-3 flex gap-6 text-xs" style={{ color: C.text3 }}>
            <span>Top lift: <strong style={{ color: liftColor }}>{topLift?.toFixed(2) ?? "—"}×</strong></span>
            <span>Bottom lift: <strong style={{ color: C.text2 }}>{stats?.decile_lift?.bottom_decile_lift?.toFixed(2) ?? "—"}×</strong></span>
          </div>
        </HoverCard>
      )}

      {/* Empty state */}
      {!stats?.fitted && (
        <div className="flex flex-col items-center gap-3 rounded-2xl p-12" style={{ border: `1px solid ${C.border}`, backgroundColor: C.card }}>
          <Activity size={32} style={{ color: C.text3 }} />
          <p className="text-sm" style={{ color: C.text3 }}>No calibration model fitted yet.</p>
          <p className="text-xs text-center" style={{ color: C.text3 }}>
            Model is fitted daily at 23:30 UTC. Requires ≥20 resolved signals.
          </p>
        </div>
      )}
    </div>
  );
}
