/**
 * Centralized FinPilot API client.
 *
 * - Reads base URL from NEXT_PUBLIC_API_URL. When not set (Docker), /api/v1/* paths
 *   are automatically rewritten to /py-api/* for Next.js runtime proxy routing.
 * - Reads JWT from localStorage key "finpilot_token" (browser only).
 * - Injects `Authorization: Bearer <token>` header automatically when present.
 * - Exposes helpers for token persistence used by the auth flow.
 *
 * Usage:
 *   import { apiFetch, setAuthToken } from "@/lib/api";
 *   const r = await apiFetch("/api/v1/scanner/run", { method: "POST", body });
 */

export const API_BASE: string =
  process.env.NEXT_PUBLIC_API_URL || "";

const TOKEN_KEY = "finpilot_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    /* ignore quota / privacy errors */
  }
}

export function clearAuthToken(): void {
  setAuthToken(null);
}

/**
 * Build a full URL: relative paths are resolved against API_BASE,
 * absolute (http/https) paths are used as-is.
 */
function resolveUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  // When API_BASE is empty (Docker, no NEXT_PUBLIC_API_URL set) rewrite
  // /api/v1/<rest> → /py-api/<rest> so the Next.js runtime proxy handles it.
  if (!API_BASE && path.startsWith("/api/v1/"))
    return `/py-api/${path.slice(8)}`;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return `${API_BASE}/${path}`;
}

/**
 * Fetch wrapper that injects the bearer token (when available) and
 * preserves any caller-supplied headers / init options.
 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers || {});
  const token = getAuthToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  // Default to JSON when caller provides a body but no content-type.
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(resolveUrl(path), { ...init, headers });
}

/**
 * Convenience wrapper: parse JSON response or throw with status text.
 */
export async function apiJson<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const r = await apiFetch(path, init);
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`API ${r.status} ${r.statusText}: ${text}`);
  }
  return (await r.json()) as T;
}
