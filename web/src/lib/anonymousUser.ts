/**
 * FinSense anonymous identity — VS-01 Phase 4.
 *
 * A per-browser, non-cryptographic identifier used only so a user's own
 * predictions can be found again after a refresh. This is NOT authentication:
 * anyone who clears localStorage (or opens a new browser) gets a fresh ID and
 * a fresh predict quota for the same case. That is an accepted v0 limitation,
 * not an oversight — see docs/strategy/FinSense_Vertical_Slice_Specification_v1_2026-08-11.md
 * §5 (Identity) and the Architecture Contract's identity-integrity vs.
 * prediction-immutability distinction: what IS guaranteed is that a given
 * (anonymous_user_id, case_id) pair can never produce a second prediction or
 * silently edit the first one (server-side UNIQUE constraint, 409 on repeat).
 *
 * Deliberately namespaced separately from FinPilot's own auth session
 * (`finpilot_auth_session` in lib/auth.tsx) — these are two different
 * identity systems that must not collide or be confused with each other.
 * A future `auth_user_id` (tied to real FinPilot login) is a v1+ concern,
 * out of scope here.
 */

const STORAGE_KEY = "finsense_anonymous_user_id";

/**
 * Returns this browser's FinSense anonymous_user_id, creating and persisting
 * one on first call if none exists yet. Stable across reloads (same browser,
 * same localStorage); different per browser/profile/incognito session.
 *
 * Returns null during SSR (no `window`) — callers must only invoke this from
 * client-side code (e.g. inside a "use client" component's event handler or
 * useEffect), matching the pattern already used in lib/api.ts's getAuthToken().
 */
export function getAnonymousUserId(): string | null {
  if (typeof window === "undefined") return null;

  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing) return existing;

    const fresh = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    // localStorage unavailable (privacy mode, quota, etc.) — fall back to an
    // in-memory-only id for this call. Not persisted, so a refresh will lose
    // continuity, but predict/outcome calls still work for the current page view.
    return crypto.randomUUID();
  }
}
