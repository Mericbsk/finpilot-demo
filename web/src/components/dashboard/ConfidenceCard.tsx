"use client";

import { C } from "@/lib/stockData";
import { ShieldCheck, ShieldAlert, Shield, ShieldX } from "lucide-react";

/* ── Brier → reliability mapping ─────────────────────────── *
 * Brier = 0.00 → perfect (100% reliable)
 * Brier = 0.25 → no-skill baseline (0% reliable)
 * Scores above 0.25 are clamped to 0.
 */
export function brierToReliability(brier: number): number {
  return Math.max(0, Math.round(((0.25 - brier) / 0.25) * 100));
}

export interface ConfidenceTier {
  label: string;
  color: string;
  bg: string;
  Icon: typeof Shield;
}

export function getConfidenceTier(brier: number | null): ConfidenceTier {
  if (brier == null) return { label: "Unknown", color: C.text3, bg: "rgba(255,255,255,0.05)", Icon: Shield };
  if (brier < 0.15) return { label: "Excellent", color: C.green,  bg: "rgba(48,209,88,0.12)",   Icon: ShieldCheck };
  if (brier < 0.20) return { label: "Good",      color: C.cyan,   bg: "rgba(0,212,255,0.10)",   Icon: ShieldCheck };
  if (brier < 0.25) return { label: "Fair",      color: C.yellow, bg: "rgba(255,214,10,0.10)",  Icon: ShieldAlert };
  return                     { label: "Poor",     color: C.red,    bg: "rgba(255,69,58,0.12)",   Icon: ShieldX };
}

/* ── Compact inline badge (for scanner rows, signal cards) ── */
export function ConfidenceBadge({ brier }: { brier: number | null }) {
  const tier = getConfidenceTier(brier);
  const pct = brier != null ? brierToReliability(brier) : null;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        backgroundColor: tier.bg,
        color: tier.color,
        borderRadius: 9999,
        padding: "2px 8px",
        fontSize: 10,
        fontWeight: 700,
        whiteSpace: "nowrap",
      }}
    >
      <tier.Icon size={10} />
      {pct != null ? `${pct}%` : "—"} {tier.label}
    </span>
  );
}

/* ── Arc gauge ────────────────────────────────────────────── */
function ArcGauge({ pct, color }: { pct: number; color: string }) {
  const r = 36;
  const cx = 44;
  const cy = 44;
  const circumference = Math.PI * r; // half circle
  const filled = (pct / 100) * circumference;
  return (
    <svg width={88} height={54} viewBox="0 0 88 54">
      {/* Track */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={8}
        strokeLinecap="round"
      />
      {/* Fill */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke={color}
        strokeWidth={8}
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference}`}
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
    </svg>
  );
}

/* ── Full card ────────────────────────────────────────────── */
export interface ConfidenceCardProps {
  brier: number | null;
  ece?: number | null;
  resolvedSignals?: number;
  label?: string;
}

export function ConfidenceCard({
  brier,
  ece,
  resolvedSignals,
  label = "Model Reliability",
}: ConfidenceCardProps) {
  const tier = getConfidenceTier(brier);
  const pct = brier != null ? brierToReliability(brier) : null;

  return (
    <div
      className="rounded-2xl p-5"
      style={{
        backgroundColor: C.card,
        border: `1px solid ${C.border}`,
        minWidth: 200,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wide" style={{ color: C.text3 }}>
          {label}
        </span>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            backgroundColor: tier.bg,
            color: tier.color,
            borderRadius: 9999,
            padding: "2px 8px",
            fontSize: 10,
            fontWeight: 700,
          }}
        >
          <tier.Icon size={10} />
          {tier.label}
        </span>
      </div>

      {/* Gauge + number */}
      <div className="flex flex-col items-center gap-1 mb-3">
        <div className="relative">
          <ArcGauge pct={pct ?? 0} color={tier.color} />
          <div
            className="absolute inset-x-0 bottom-0 text-center"
            style={{ fontSize: 22, fontWeight: 800, color: tier.color, lineHeight: 1 }}
          >
            {pct != null ? `${pct}%` : "—"}
          </div>
        </div>
      </div>

      {/* Detail metrics */}
      <div className="grid grid-cols-2 gap-2 mt-1">
        <div className="rounded-lg p-2" style={{ backgroundColor: "#0a0a12" }}>
          <div className="text-xs mb-0.5" style={{ color: C.text3 }}>Brier Score</div>
          <div className="text-sm font-semibold" style={{ color: brier != null ? tier.color : C.text3 }}>
            {brier != null ? brier.toFixed(4) : "—"}
          </div>
          <div className="text-xs" style={{ color: C.text3 }}>{"< 0.20 ideal"}</div>
        </div>
        {ece != null ? (
          <div className="rounded-lg p-2" style={{ backgroundColor: "#0a0a12" }}>
            <div className="text-xs mb-0.5" style={{ color: C.text3 }}>ECE</div>
            <div
              className="text-sm font-semibold"
              style={{ color: ece < 0.05 ? C.green : ece < 0.10 ? C.yellow : C.red }}
            >
              {ece.toFixed(4)}
            </div>
            <div className="text-xs" style={{ color: C.text3 }}>{"< 0.05 ideal"}</div>
          </div>
        ) : resolvedSignals != null ? (
          <div className="rounded-lg p-2" style={{ backgroundColor: "#0a0a12" }}>
            <div className="text-xs mb-0.5" style={{ color: C.text3 }}>Resolved</div>
            <div className="text-sm font-semibold" style={{ color: C.text2 }}>{resolvedSignals}</div>
            <div className="text-xs" style={{ color: C.text3 }}>signals</div>
          </div>
        ) : null}
      </div>

      {/* Scale legend */}
      <div className="mt-3 flex justify-between text-xs" style={{ color: C.text3 }}>
        <span style={{ color: C.red }}>Poor ≥0.25</span>
        <span style={{ color: C.yellow }}>Fair</span>
        <span style={{ color: C.green }}>Excellent {"<"}0.15</span>
      </div>
    </div>
  );
}
