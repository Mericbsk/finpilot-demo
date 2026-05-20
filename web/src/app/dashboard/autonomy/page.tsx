"use client";

/**
 * Autonomy dashboard — Faz 3 control surface.
 *
 *   • Pending Approvals: human-in-the-loop queue for risky autonomous
 *     decisions (approve / reject via /api/v1/loop/{approve,reject}).
 *   • Audit Log: append-only feed of every autonomous decision
 *     (GET /api/v1/loop/audit).
 *
 * Auto-refreshes every 15 seconds. Approve/Reject calls require admin JWT
 * (apiFetch automatically attaches the bearer token from localStorage).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ShieldCheck,
  ClipboardList,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";

import { apiFetch, apiJson } from "@/lib/api";

interface PendingAction {
  id: string;
  kind: string;
  payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  requested_by: string;
  reason?: string;
  created_at: number;
  decided_by?: string;
  decided_at?: number;
}

interface AuditEntry {
  ts: number;
  actor: string;
  action: string;
  decision: string;
  payload: Record<string, unknown>;
}

const C = {
  bg: "#000",
  card: "#111118",
  border: "rgba(255,255,255,0.10)",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  text3: "#6e6e73",
  cyan: "#00d4ff",
  green: "#30d158",
  red: "#ff453a",
  yellow: "#ffd60a",
  cyanBg: "rgba(0,212,255,0.10)",
  greenBg: "rgba(48,209,88,0.10)",
  redBg: "rgba(255,69,58,0.10)",
  yellowBg: "rgba(255,214,10,0.10)",
};

const REFRESH_MS = 15_000;

function fmtTime(ts: number | undefined): string {
  if (!ts) return "—";
  try {
    return new Date(ts * 1000).toLocaleString("tr-TR");
  } catch {
    return String(ts);
  }
}

function decisionColor(decision: string): { fg: string; bg: string } {
  const d = decision.toLowerCase();
  if (d.includes("approve") || d === "promoted") return { fg: C.green, bg: C.greenBg };
  if (d.includes("reject") || d.includes("rolled_back") || d.includes("degrade"))
    return { fg: C.red, bg: C.redBg };
  if (d.includes("pending") || d.includes("enqueued")) return { fg: C.yellow, bg: C.yellowBg };
  return { fg: C.cyan, bg: C.cyanBg };
}

export default function AutonomyPage() {
  const [pending, setPending] = useState<PendingAction[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<number>(0);

  const refresh = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([
        apiJson<{ actions: PendingAction[] }>("/api/v1/loop/pending"),
        apiJson<{ entries: AuditEntry[] }>("/api/v1/loop/audit?limit=50"),
      ]);
      setPending(p.actions || []);
      setAudit((a.entries || []).slice().reverse());
      setError(null);
      setLastRefresh(Date.now());
    } catch (e: any) {
      setError(e?.message || "Bağlantı hatası");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(t);
  }, [refresh]);

  const handleDecide = async (id: string, action: "approve" | "reject") => {
    setBusyId(id);
    try {
      const res = await apiFetch(`/api/v1/loop/${action}/${id}`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      toast.success(action === "approve" ? "Onaylandı" : "Reddedildi");
      await refresh();
    } catch (e: any) {
      toast.error(e?.message || "İşlem başarısız");
    } finally {
      setBusyId(null);
    }
  };

  const pendingOnly = useMemo(
    () => pending.filter((p) => p.status === "pending"),
    [pending],
  );

  return (
    <div style={{ color: C.text1, minHeight: "100vh" }}>
      <div className="mb-6 flex items-start justify-between gap-3">
        <div>
          <div className="mb-1 flex items-center gap-3">
            <div
              className="rounded-xl p-2"
              style={{ background: C.cyanBg, border: `1px solid ${C.cyan}30` }}
            >
              <ShieldCheck size={22} style={{ color: C.cyan }} />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: C.text1 }}>
              Otonomi Kontrol Paneli
            </h1>
          </div>
          <p style={{ color: C.text2, fontSize: 14 }}>
            Bekleyen onaylar + tüm otonom kararların denetim kaydı (her 15 sn yenilenir)
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors"
          style={{
            background: C.card,
            border: `1px solid ${C.border}`,
            color: C.text2,
          }}
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Yenile
        </button>
      </div>

      {error && (
        <div
          className="mb-4 flex items-center gap-2 rounded-lg p-3 text-sm"
          style={{ background: C.redBg, border: `1px solid ${C.red}40`, color: C.red }}
        >
          <AlertCircle size={16} /> {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section
          className="rounded-2xl p-5"
          style={{ background: C.card, border: `1px solid ${C.border}` }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <ClipboardList size={18} style={{ color: C.cyan }} /> Bekleyen Onaylar
            </h2>
            <span
              className="rounded-full px-2 py-0.5 text-xs"
              style={{ background: C.cyanBg, color: C.cyan }}
            >
              {pendingOnly.length}
            </span>
          </div>

          {pendingOnly.length === 0 ? (
            <p style={{ color: C.text3, fontSize: 13 }}>Şu an bekleyen otonom karar yok.</p>
          ) : (
            <ul className="space-y-3">
              {pendingOnly.map((p) => (
                <li
                  key={p.id}
                  className="rounded-xl p-3"
                  style={{ background: C.bg, border: `1px solid ${C.border}` }}
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span
                          className="rounded px-2 py-0.5 text-[11px] font-medium uppercase"
                          style={{ background: C.yellowBg, color: C.yellow }}
                        >
                          {p.kind}
                        </span>
                        <span style={{ color: C.text3, fontSize: 11 }}>
                          {fmtTime(p.created_at)}
                        </span>
                      </div>
                      {p.reason && (
                        <p className="mt-1.5 text-sm" style={{ color: C.text1 }}>
                          {p.reason}
                        </p>
                      )}
                      <p className="mt-0.5 text-xs" style={{ color: C.text3 }}>
                        İsteyen: {p.requested_by}
                      </p>
                    </div>
                  </div>

                  <details className="mb-2">
                    <summary className="cursor-pointer text-xs" style={{ color: C.text3 }}>
                      Payload
                    </summary>
                    <pre
                      className="mt-1 overflow-x-auto rounded p-2 text-[11px]"
                      style={{ background: C.card, color: C.text2 }}
                    >
                      {JSON.stringify(p.payload, null, 2)}
                    </pre>
                  </details>

                  <div className="flex gap-2">
                    <button
                      disabled={busyId === p.id}
                      onClick={() => handleDecide(p.id, "approve")}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{
                        background: C.greenBg,
                        border: `1px solid ${C.green}40`,
                        color: C.green,
                      }}
                    >
                      {busyId === p.id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <CheckCircle2 size={12} />
                      )}
                      Onayla
                    </button>
                    <button
                      disabled={busyId === p.id}
                      onClick={() => handleDecide(p.id, "reject")}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{
                        background: C.redBg,
                        border: `1px solid ${C.red}40`,
                        color: C.red,
                      }}
                    >
                      <XCircle size={12} /> Reddet
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section
          className="rounded-2xl p-5"
          style={{ background: C.card, border: `1px solid ${C.border}` }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <ClipboardList size={18} style={{ color: C.cyan }} /> Denetim Kaydı
            </h2>
            <span style={{ color: C.text3, fontSize: 11 }}>son {audit.length} giriş</span>
          </div>

          {audit.length === 0 ? (
            <p style={{ color: C.text3, fontSize: 13 }}>Henüz kayıt yok.</p>
          ) : (
            <ul className="space-y-2 overflow-y-auto pr-1" style={{ maxHeight: 540 }}>
              {audit.map((e, i) => {
                const col = decisionColor(e.decision);
                return (
                  <li
                    key={`${e.ts}-${i}`}
                    className="rounded-lg p-2.5"
                    style={{ background: C.bg, border: `1px solid ${C.border}` }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 text-[12px]">
                          <span style={{ color: C.text2 }}>{e.actor}</span>
                          <span style={{ color: C.text3 }}>·</span>
                          <span style={{ color: C.text1 }}>{e.action}</span>
                        </div>
                        <span
                          className="mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium"
                          style={{ background: col.bg, color: col.fg }}
                        >
                          {e.decision}
                        </span>
                      </div>
                      <span className="shrink-0 text-[11px]" style={{ color: C.text3 }}>
                        {fmtTime(e.ts)}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>

      {lastRefresh > 0 && (
        <p className="mt-4 text-xs" style={{ color: C.text3 }}>
          Son güncelleme: {new Date(lastRefresh).toLocaleTimeString("tr-TR")}
        </p>
      )}
    </div>
  );
}
