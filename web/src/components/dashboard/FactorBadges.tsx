"use client";

/**
 * FactorBadges — inline badges for the 3 new signal enrichment factors:
 *   🔥 Squeeze  — float/short-squeeze potential (0–1)
 *   📋 Catalyst — SEC EDGAR recent filings (-1..1)
 *   📊 Macro    — FRED macro regime (risk_on / neutral / risk_off)
 *
 * Each badge is designed to fit in a scanner table row (compact mode)
 * or in a card column (full mode).
 */

import { C } from "@/lib/stockData";
import { Flame, FileText, Activity } from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type MacroRegime = "risk_on" | "neutral" | "risk_off";

export interface FactorData {
  squeeze_factor: number;   // 0.0–1.0
  catalyst_factor: number;  // -1.0..1.0
  macro_regime: MacroRegime;
  macro_vix?: number | null;
  macro_spread?: number | null;
  macro_multiplier?: number;
  flags_active?: {
    squeeze: boolean;
    edgar: boolean;
    fred: boolean;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Squeeze Badge
// ─────────────────────────────────────────────────────────────────────────────

/** Shows only when squeeze_factor ≥ 0.35 (meaningful level). */
export function SqueezeBadge({ value }: { value: number }) {
  if (value < 0.35) return null;

  const intensity = value >= 0.7 ? "high" : value >= 0.5 ? "medium" : "low";
  const color =
    intensity === "high" ? C.red : intensity === "medium" ? C.yellow : "#FF9F0A";
  const bg =
    intensity === "high"
      ? "rgba(255,69,58,0.15)"
      : intensity === "medium"
        ? "rgba(255,214,10,0.12)"
        : "rgba(255,159,10,0.12)";
  const label =
    intensity === "high" ? "SQUEEZE" : intensity === "medium" ? "Squeeze" : "Squeeze?";

  return (
    <span
      title={`Short-squeeze potential: ${(value * 100).toFixed(0)}%`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        backgroundColor: bg,
        color,
        borderRadius: 9999,
        padding: "2px 7px",
        fontSize: 10,
        fontWeight: 700,
        whiteSpace: "nowrap",
        border: `1px solid ${color}33`,
      }}
    >
      <Flame size={9} />
      {label} {(value * 100).toFixed(0)}%
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Catalyst Badge
// ─────────────────────────────────────────────────────────────────────────────

/** Shows only when catalyst_factor ≠ 0. Green for positive (8-K), red for negative (S-1). */
export function CatalystBadge({ value }: { value: number }) {
  if (Math.abs(value) < 0.05) return null;

  const positive = value > 0;
  const color = positive ? C.green : C.red;
  const bg = positive ? "rgba(48,209,88,0.12)" : "rgba(255,69,58,0.12)";
  const sign = positive ? "+" : "";
  const label = positive ? "Filing+" : "Dilution";

  return (
    <span
      title={`SEC EDGAR catalyst: ${sign}${(value * 100).toFixed(0)}% (8-K/Form4 positive, S-1/424B negative)`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        backgroundColor: bg,
        color,
        borderRadius: 9999,
        padding: "2px 7px",
        fontSize: 10,
        fontWeight: 700,
        whiteSpace: "nowrap",
        border: `1px solid ${color}33`,
      }}
    >
      <FileText size={9} />
      {label}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Macro Regime Chip
// ─────────────────────────────────────────────────────────────────────────────

const REGIME_CONFIG: Record<
  MacroRegime,
  { label: string; color: string; bg: string }
> = {
  risk_on: {
    label: "Risk-On",
    color: C.green,
    bg: "rgba(48,209,88,0.12)",
  },
  neutral: {
    label: "Neutral",
    color: C.cyan,
    bg: "rgba(0,212,255,0.10)",
  },
  risk_off: {
    label: "Risk-Off",
    color: C.red,
    bg: "rgba(255,69,58,0.12)",
  },
};

export function MacroRegimeChip({
  regime,
  vix,
  spread,
  multiplier,
}: {
  regime: MacroRegime;
  vix?: number | null;
  spread?: number | null;
  multiplier?: number;
}) {
  const cfg = REGIME_CONFIG[regime] ?? REGIME_CONFIG.neutral;
  const tooltipParts = ["FRED Macro Regime"];
  if (vix != null) tooltipParts.push(`VIX: ${vix.toFixed(2)}`);
  if (spread != null) tooltipParts.push(`10Y-2Y: ${spread.toFixed(2)}%`);
  if (multiplier != null && multiplier !== 1.0)
    tooltipParts.push(`Pos. size ×${multiplier.toFixed(1)}`);

  return (
    <span
      title={tooltipParts.join(" | ")}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        backgroundColor: cfg.bg,
        color: cfg.color,
        borderRadius: 9999,
        padding: "2px 7px",
        fontSize: 10,
        fontWeight: 700,
        whiteSpace: "nowrap",
        border: `1px solid ${cfg.color}33`,
      }}
    >
      <Activity size={9} />
      {cfg.label}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Macro Regime Banner  (full-width strip for dashboard / top bar)
// ─────────────────────────────────────────────────────────────────────────────

export function MacroRegimeBanner({
  regime,
  vix,
  spread,
}: {
  regime: MacroRegime;
  vix?: number | null;
  spread?: number | null;
}) {
  const cfg = REGIME_CONFIG[regime] ?? REGIME_CONFIG.neutral;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 14px",
        borderRadius: 8,
        backgroundColor: cfg.bg,
        border: `1px solid ${cfg.color}44`,
        fontSize: 11,
        fontWeight: 600,
        color: cfg.color,
      }}
    >
      <Activity size={12} />
      <span>
        FRED Macro: <strong>{cfg.label}</strong>
      </span>
      {vix != null && (
        <span style={{ opacity: 0.7, fontWeight: 400 }}>VIX {vix.toFixed(1)}</span>
      )}
      {spread != null && (
        <span style={{ opacity: 0.7, fontWeight: 400 }}>
          10Y-2Y {spread >= 0 ? "+" : ""}
          {spread.toFixed(2)}%
        </span>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// FactorBadgeRow  (squeeze + catalyst side-by-side, compact)
// ─────────────────────────────────────────────────────────────────────────────

/** Drop this anywhere a scan row / stock card exists. */
export function FactorBadgeRow({ data }: { data: FactorData }) {
  const hasSqueeze = data.flags_active?.squeeze !== false;
  const hasEdgar = data.flags_active?.edgar !== false;

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
      {hasSqueeze && <SqueezeBadge value={data.squeeze_factor} />}
      {hasEdgar && <CatalystBadge value={data.catalyst_factor} />}
    </span>
  );
}
