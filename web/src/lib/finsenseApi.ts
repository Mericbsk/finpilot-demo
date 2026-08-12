/**
 * FinSense reasoning-layer API client — VS-01 Phase 4.
 *
 * Thin wrapper around the shared `apiFetch`/`apiJson` helpers (lib/api.ts) —
 * same base-URL resolution / py-api proxy rewriting as the rest of the app,
 * no separate fetch logic. Talks to `/api/v1/finsense/*`
 * (api/routers/reasoning.py). Ready for the Classroom UI (Phase 5) to
 * consume; this file intentionally contains no UI/React code.
 *
 * Identity: every call that needs to identify "this browser" reads
 * `getAnonymousUserId()` (lib/anonymousUser.ts) itself — callers never pass
 * an id in by hand, so there is exactly one place a predict/outcome call
 * could get the wrong id from.
 *
 * Tamper-resistance note: this client never sends `committed_at` or any
 * outcome field in the predict request — those fields don't even exist on
 * `PredictPayload` below, matching the server's `PredictRequest` schema
 * (api/routers/reasoning.py), which also has no such fields. There is
 * nothing for a caller to "forget not to send".
 */

import { apiFetch, apiJson } from "@/lib/api";
import { getAnonymousUserId } from "@/lib/anonymousUser";

export type Direction = "UP" | "DOWN" | "FLAT";

export interface FinSenseCase {
  id: string;
  asset: string;
  event_timestamp: string;
  snapshot: Record<string, unknown>;
  context: string;
  horizon_days: number;
  // Deliberately no outcome/grade field — see reasoning.py CaseOut / LOCK-03.
  // Present only when this browser already has a committed prediction on
  // this case (refresh-safe locked state) — never carries outcome data.
  my_prediction: FinSensePrediction | null;
}

export interface PredictPayload {
  direction: Direction;
  probability: number;
  reason: string;
}

export interface FinSensePrediction {
  id: string;
  case_id: string;
  direction: Direction;
  probability: number;
  reason: string;
  committed_at: string;
}

export interface FinSenseEvaluation {
  direction_correct: boolean;
  binary_outcome: number;
  probability_error: number;
}

export interface FinSenseOutcome {
  case_id: string;
  actual_direction: Direction;
  actual_return_pct: number | null;
  resolved_at: string;
  your_prediction: FinSensePrediction | null;
  evaluation: FinSenseEvaluation | null;
}

/**
 * GET /finsense/case/today — null when there is no open case (204). Always
 * sends this browser's anonymous_user_id so the response can include
 * `my_prediction` when one already exists — this is what makes a refresh
 * after commit land on the locked screen instead of the form again.
 */
export async function getCaseToday(): Promise<FinSenseCase | null> {
  const anonymousUserId = getAnonymousUserId();
  const qs = anonymousUserId
    ? `?anonymous_user_id=${encodeURIComponent(anonymousUserId)}`
    : "";
  const r = await apiFetch(`/api/v1/finsense/case/today${qs}`);
  if (r.status === 204) return null;
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`case/today ${r.status}: ${text}`);
  }
  return (await r.json()) as FinSenseCase;
}

/**
 * GET /finsense/cases — every open case (Phase 8 content expansion). Used by
 * the Classroom landing page instead of assuming a single "today" case.
 */
export async function listCases(): Promise<FinSenseCase[]> {
  const anonymousUserId = getAnonymousUserId();
  const qs = anonymousUserId
    ? `?anonymous_user_id=${encodeURIComponent(anonymousUserId)}`
    : "";
  return apiJson<FinSenseCase[]>(`/api/v1/finsense/cases${qs}`);
}

/**
 * GET /finsense/case/{id} — fetch one specific case by id, regardless of
 * whether it's the most recently created one. Null on 404 (not open / not
 * found) rather than throwing, since "this case isn't available" is a normal
 * state for the case detail page to render (not an error).
 */
export async function getCase(caseId: string): Promise<FinSenseCase | null> {
  const anonymousUserId = getAnonymousUserId();
  const qs = anonymousUserId
    ? `?anonymous_user_id=${encodeURIComponent(anonymousUserId)}`
    : "";
  const r = await apiFetch(`/api/v1/finsense/case/${encodeURIComponent(caseId)}${qs}`);
  if (r.status === 404) return null;
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`case/${caseId} ${r.status}: ${text}`);
  }
  return (await r.json()) as FinSenseCase;
}

/**
 * POST /finsense/case/{id}/predict — commits this browser's prediction.
 * Throws on 409 (already predicted on this case) so the caller can show a
 * "you already predicted" state rather than a generic error.
 */
export async function predictCase(
  caseId: string,
  payload: PredictPayload,
): Promise<FinSensePrediction> {
  const anonymousUserId = getAnonymousUserId();
  if (!anonymousUserId) {
    throw new Error("predictCase() must be called from the browser");
  }
  return apiJson<FinSensePrediction>(
    `/api/v1/finsense/case/${encodeURIComponent(caseId)}/predict`,
    {
      method: "POST",
      body: JSON.stringify({
        anonymous_user_id: anonymousUserId,
        ...payload,
      }),
    },
  );
}

/**
 * GET /finsense/case/{id}/outcome — null while the case is still unresolved
 * (server 404 = "outcome pending", not an error condition here). Includes
 * this browser's own prediction + evaluation when one exists.
 */
export async function getOutcome(caseId: string): Promise<FinSenseOutcome | null> {
  const anonymousUserId = getAnonymousUserId();
  const qs = anonymousUserId
    ? `?anonymous_user_id=${encodeURIComponent(anonymousUserId)}`
    : "";
  const r = await apiFetch(
    `/api/v1/finsense/case/${encodeURIComponent(caseId)}/outcome${qs}`,
  );
  if (r.status === 404) return null;
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`case/outcome ${r.status}: ${text}`);
  }
  return (await r.json()) as FinSenseOutcome;
}
