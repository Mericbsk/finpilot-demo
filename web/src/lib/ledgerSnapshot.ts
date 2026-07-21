/**
 * Server-side reader for the distribution snapshot (`web/public/demo_snapshot.json`).
 * Published by `distribution/jobs.py::_push_snapshot_to_web()` (via `publish_web`
 * hook, `FINPILOT_WEB_PUBLISH_CMD`). Read directly off disk at render time —
 * no network fetch needed since it's a static file in the same deploy.
 *
 * Schema v1.1 (see distribution/snapshot_builder.py::build_snapshot):
 * adds `concept`, `edition_no`, `context_line` on top of the v1 fields.
 * All v1.1 fields are optional here so older snapshots (schema 1, pre-Ledger)
 * still render — honest empty-state instead of a crash.
 */
import fs from "node:fs";
import path from "node:path";

export interface LedgerCandidate {
  ticker: string;
  company?: string;
  grade: string;
  prob_band?: string;
  badges?: string[];
  rationale?: string;
  premium_only?: boolean;
  risk_note?: string;
}

export interface LedgerKarne {
  toplam_aday_bugun?: Record<string, number>;
  by_grade?: Record<string, { n?: number; count?: number; hit_rate?: number; success_rate?: number; hit5?: number }>;
  window?: string;
}

export interface LedgerConcept {
  name: string;
  line: string;
}

export interface LedgerSnapshot {
  schema: number;
  date: string;
  generated_at: string;
  config_sha: string;
  universe: number;
  candidates: LedgerCandidate[];
  karne: LedgerKarne | null;
  warnings: string[];
  // v1.1+
  concept?: LedgerConcept;
  edition_no?: number;
  context_line?: string;
}

let cached: { snapshot: LedgerSnapshot | null; mtimeMs: number } | null = null;

/**
 * Reads and parses the public snapshot. Returns `null` if the file is
 * missing or malformed — callers MUST handle this with an honest
 * "no edition yet" state, never fabricate data.
 */
function getLocalLedgerSnapshot(): LedgerSnapshot | null {
  const file = path.join(process.cwd(), "public", "demo_snapshot.json");
  let stat: fs.Stats;
  try {
    stat = fs.statSync(file);
  } catch {
    return null;
  }
  if (cached && cached.mtimeMs === stat.mtimeMs) {
    return cached.snapshot;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("snapshot must be a single JSON object");
    }
    const snapshot = parsed as LedgerSnapshot;
    if (isSnapshotStale(snapshot)) {
      cached = { snapshot: null, mtimeMs: stat.mtimeMs };
      return null;
    }
    cached = { snapshot, mtimeMs: stat.mtimeMs };
    return snapshot;
  } catch {
    cached = { snapshot: null, mtimeMs: stat.mtimeMs };
    return null;
  }
}

/** Read the Render-owned snapshot first so web and Telegram share one edition. */
export async function getLedgerSnapshot(): Promise<LedgerSnapshot | null> {
  const backendUrl = process.env.API_HOST ?? process.env.BACKEND_URL;
  if (backendUrl) {
    try {
      const response = await fetch(`${backendUrl}/api/v1/distribution/snapshot`, {
        cache: "no-store",
        signal: AbortSignal.timeout(8_000),
      });
      if (response.ok) {
        const parsed: unknown = await response.json();
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          const snapshot = parsed as LedgerSnapshot;
          if (!isSnapshotStale(snapshot)) return snapshot;
        }
      }
    } catch {
      // The local published file remains a deployment fallback.
    }
  }
  return getLocalLedgerSnapshot();
}

/** True if the snapshot is missing, or stale (not today / no candidates). */
export function isSnapshotStale(snap: LedgerSnapshot | null): boolean {
  if (!snap) return true;
  const expectedUniverse = Number(process.env.FINPILOT_EXPECTED_UNIVERSE ?? "1812");
  const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Vienna" }).format(new Date());
  return snap.date !== today || snap.universe !== expectedUniverse || !Array.isArray(snap.candidates);
}
