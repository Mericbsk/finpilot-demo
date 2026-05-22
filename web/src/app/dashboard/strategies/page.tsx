"use client";

import { useState, useEffect, useCallback } from "react";
import { Trophy, TrendingUp, TrendingDown, RefreshCw, CheckCircle2, XCircle, Activity } from "lucide-react";
import { C } from "@/lib/stockData";

interface RegistryEntry {
  id: number;
  name: string;
  status: "champion" | "challenger" | "retired";
  weights: Record<string, number> | null;
  brier_score: number | null;
  win_rate: number | null;
  profit_factor: number | null;
  n_samples: number | null;
  promoted_at: string | null;
  created_at: string;
  promotion_notes: Record<string, unknown> | null;
  strike_count: number | null;
}

interface RegistryResponse {
  champion: RegistryEntry | null;
  challengers: RegistryEntry[];
}

const ROW_STYLE: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  padding: "12px 16px",
  borderBottom: `1px solid ${C.border}`,
};

const CARD: React.CSSProperties = {
  background: C.card,
  border: `1px solid ${C.border}`,
  borderRadius: 12,
  overflow: "hidden",
};

function MetricCell({ label, value, good, fmt }: {
  label: string;
  value: number | null | undefined;
  good?: "low" | "high";
  fmt?: (v: number) => string;
}) {
  const formatted = value != null ? (fmt ? fmt(value) : value.toFixed(4)) : "—";
  const colored =
    value != null && good
      ? good === "low"
        ? value < 0.22 ? C.green : value > 0.28 ? C.red : "#f5a623"
        : value > 0.55 ? C.green : value < 0.45 ? C.red : "#f5a623"
      : C.text2;

  return (
    <div style={{ minWidth: 90 }}>
      <div style={{ fontSize: 11, color: C.text3, marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 600, color: colored }}>{formatted}</div>
    </div>
  );
}

function WeightsRow({ weights }: { weights: Record<string, number> | null }) {
  if (!weights) return <span style={{ color: C.text3, fontSize: 12 }}>—</span>;
  const entries = Object.entries(weights).filter(([, v]) => v > 0);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
      {entries.map(([k, v]) => (
        <span key={k} style={{
          fontSize: 11,
          background: "rgba(0,212,255,0.08)",
          border: `1px solid rgba(0,212,255,0.2)`,
          borderRadius: 6,
          padding: "2px 8px",
          color: C.cyan,
        }}>
          {k.replace(/^_?[Ww]_/, "")}: {v.toFixed(3)}
        </span>
      ))}
    </div>
  );
}

function EntryCard({ entry, isChampion }: { entry: RegistryEntry; isChampion?: boolean }) {
  const accent = isChampion ? "#f5a623" : C.cyan;

  return (
    <div style={{ ...CARD, marginBottom: 12, borderColor: isChampion ? "#f5a623" : C.border }}>
      <div style={{ ...ROW_STYLE, borderBottom: `1px solid ${C.border}`, background: isChampion ? "rgba(245,166,35,0.06)" : undefined }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
          {isChampion
            ? <Trophy size={16} color="#f5a623" />
            : <Activity size={16} color={C.cyan} />}
          <span style={{ fontWeight: 700, color: accent, fontSize: 15 }}>{entry.name}</span>
          <span style={{
            fontSize: 11,
            padding: "2px 8px",
            borderRadius: 20,
            background: isChampion ? "rgba(245,166,35,0.15)" : "rgba(0,212,255,0.1)",
            color: accent,
            border: `1px solid ${accent}40`,
          }}>
            {isChampion ? "Champion" : "Challenger"}
          </span>
          {(entry.strike_count ?? 0) > 0 && (
            <span style={{
              fontSize: 11,
              padding: "2px 8px",
              borderRadius: 20,
              background: "rgba(255,69,58,0.15)",
              color: C.red,
              border: `1px solid rgba(255,69,58,0.3)`,
            }}>
              {entry.strike_count} strike{(entry.strike_count ?? 0) > 1 ? "s" : ""}
            </span>
          )}
        </div>
        <span style={{ fontSize: 11, color: C.text3 }}>
          {isChampion && entry.promoted_at ? `Promoted ${entry.promoted_at}` : `Created ${entry.created_at}`}
        </span>
      </div>

      <div style={{ padding: "12px 16px" }}>
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 8 }}>
          <MetricCell label="Brier ↓" value={entry.brier_score} good="low" />
          <MetricCell label="Win Rate ↑" value={entry.win_rate} good="high" fmt={(v) => `${(v * 100).toFixed(1)}%`} />
          <MetricCell label="Profit Factor ↑" value={entry.profit_factor} fmt={(v) => v.toFixed(2)} />
          <MetricCell label="Samples" value={entry.n_samples} fmt={(v) => v.toFixed(0)} />
        </div>
        <WeightsRow weights={entry.weights} />
      </div>
    </div>
  );
}

function DiffRow({ label, champion, challenger }: {
  label: string;
  champion: number | null | undefined;
  challenger: number | null | undefined;
}) {
  const diff = champion != null && challenger != null ? challenger - champion : null;
  const isGoodDiff = label.includes("Brier") ? (diff ?? 0) < 0 : (diff ?? 0) > 0;

  return (
    <div style={{ ...ROW_STYLE, borderBottom: `1px solid ${C.border}` }}>
      <span style={{ color: C.text2, fontSize: 13, width: 120 }}>{label}</span>
      <span style={{ color: C.text1, fontSize: 13, width: 80, textAlign: "right" }}>
        {champion != null ? champion.toFixed(4) : "—"}
      </span>
      <span style={{ color: C.text1, fontSize: 13, width: 80, textAlign: "right" }}>
        {challenger != null ? challenger.toFixed(4) : "—"}
      </span>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 4 }}>
        {diff != null && (
          <>
            {isGoodDiff
              ? <TrendingUp size={14} color={C.green} />
              : <TrendingDown size={14} color={C.red} />}
            <span style={{ fontSize: 12, color: isGoodDiff ? C.green : C.red }}>
              {diff > 0 ? "+" : ""}{diff.toFixed(4)}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

export default function StrategiesPage() {
  const [data, setData] = useState<RegistryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [promoting, setPromoting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [promoteResult, setPromoteResult] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/py-api/research/registry?limit=5");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const t = setInterval(fetchData, 30_000);
    return () => clearInterval(t);
  }, [fetchData]);

  const handlePromote = async () => {
    setPromoting(true);
    setPromoteResult(null);
    try {
      const res = await fetch("/py-api/research/registry/promote-best", { method: "POST" });
      const body = await res.json();
      setPromoteResult(body.promoted ? "✓ New champion promoted" : "No eligible challenger found");
      fetchData();
    } catch (e) {
      setPromoteResult(`Error: ${e}`);
    } finally {
      setPromoting(false);
    }
  };

  const champion = data?.champion ?? null;
  const challengers = data?.challengers ?? [];
  const bestChallenger = challengers.length > 0 ? challengers[0] : null;

  return (
    <div style={{ padding: "24px 32px", maxWidth: 900 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Trophy size={22} color="#f5a623" />
        <h1 style={{ color: C.text1, fontSize: 22, fontWeight: 700, margin: 0 }}>
          Strategies — Champion / Challenger
        </h1>
        <button
          onClick={fetchData}
          disabled={loading}
          style={{
            marginLeft: "auto",
            background: "transparent",
            border: `1px solid ${C.border}`,
            borderRadius: 8,
            padding: "6px 14px",
            color: C.text2,
            cursor: loading ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 13,
          }}
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
        <button
          onClick={handlePromote}
          disabled={promoting || loading}
          style={{
            background: "rgba(0,212,255,0.1)",
            border: `1px solid rgba(0,212,255,0.3)`,
            borderRadius: 8,
            padding: "6px 14px",
            color: C.cyan,
            cursor: promoting ? "not-allowed" : "pointer",
            fontSize: 13,
          }}
        >
          {promoting ? "Evaluating..." : "Evaluate Gate"}
        </button>
      </div>

      {promoteResult && (
        <div style={{
          padding: "10px 16px",
          borderRadius: 8,
          marginBottom: 16,
          background: promoteResult.startsWith("✓") ? "rgba(48,209,88,0.1)" : "rgba(255,69,58,0.1)",
          border: `1px solid ${promoteResult.startsWith("✓") ? "rgba(48,209,88,0.3)" : "rgba(255,69,58,0.3)"}`,
          color: promoteResult.startsWith("✓") ? C.green : C.red,
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 14,
        }}>
          {promoteResult.startsWith("✓") ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
          {promoteResult}
        </div>
      )}

      {error && (
        <div style={{ color: C.red, marginBottom: 16, fontSize: 13 }}>
          Error loading data: {error}
        </div>
      )}

      {/* Champion */}
      <section style={{ marginBottom: 28 }}>
        <h2 style={{ color: C.text2, fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>
          Current Champion
        </h2>
        {champion
          ? <EntryCard entry={champion} isChampion />
          : <div style={{ color: C.text3, fontSize: 14, padding: 12 }}>No champion yet.</div>}
      </section>

      {/* Live diff table */}
      {champion && bestChallenger && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ color: C.text2, fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>
            Live Diff — Champion vs Best Challenger
          </h2>
          <div style={{ ...CARD }}>
            <div style={{ ...ROW_STYLE, borderBottom: `1px solid ${C.border}`, background: "rgba(255,255,255,0.02)" }}>
              <span style={{ color: C.text3, fontSize: 12, width: 120 }}>Metric</span>
              <span style={{ color: "#f5a623", fontSize: 12, width: 80, textAlign: "right" }}>Champion</span>
              <span style={{ color: C.cyan, fontSize: 12, width: 80, textAlign: "right" }}>Challenger</span>
              <span style={{ color: C.text3, fontSize: 12, marginLeft: "auto" }}>Δ</span>
            </div>
            <DiffRow label="Brier ↓" champion={champion.brier_score} challenger={bestChallenger.brier_score} />
            <DiffRow label="Win Rate ↑" champion={champion.win_rate} challenger={bestChallenger.win_rate} />
            <DiffRow label="Profit Factor ↑" champion={champion.profit_factor} challenger={bestChallenger.profit_factor} />
          </div>
        </section>
      )}

      {/* Challengers list */}
      {challengers.length > 0 && (
        <section>
          <h2 style={{ color: C.text2, fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>
            Challengers ({challengers.length})
          </h2>
          {challengers.map((c) => (
            <EntryCard key={c.id} entry={c} />
          ))}
        </section>
      )}

      {!loading && !champion && challengers.length === 0 && (
        <div style={{ color: C.text3, fontSize: 14, padding: 24, textAlign: "center" }}>
          No models in registry yet. Run the research pipeline to generate candidates.
        </div>
      )}
    </div>
  );
}
