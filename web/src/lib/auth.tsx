"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  display_name: string;
  avatar_url?: string | null;
  role: string;
  is_active?: boolean;
  is_verified?: boolean;
}

export interface StoredAuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: string | null;
  user: AuthUser;
}

type AuthActionResult =
  | { ok: true }
  | { ok: false; error: string };

interface LoginPayload {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  displayName?: string;
}

interface AuthContextValue {
  session: StoredAuthSession | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  status: "guest" | "authenticated" | "loading";
  login: (payload: LoginPayload) => Promise<AuthActionResult>;
  register: (payload: RegisterPayload) => Promise<AuthActionResult>;
  logout: () => void;
}

const AUTH_STORAGE_KEY = "finpilot_auth_session";
const AUTH_CHANGE_EVENT = "finpilot-auth-change";

let fetchInstalled = false;
let originalFetchRef: typeof fetch | null = null;

function dispatchAuthChange() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

function getBaseFetch(): typeof fetch {
  return originalFetchRef ?? globalThis.fetch.bind(globalThis);
}

function normalizeUser(rawUser: unknown): AuthUser {
  const user = typeof rawUser === "object" && rawUser !== null ? (rawUser as Record<string, unknown>) : {};
  const username = String(user.username ?? user.display_name ?? user.email ?? "user");
  return {
    id: String(user.id ?? ""),
    email: String(user.email ?? ""),
    username,
    display_name: String(user.display_name ?? username),
    avatar_url: typeof user.avatar_url === "string" ? user.avatar_url : null,
    role: String(user.role ?? "user"),
    is_active: typeof user.is_active === "boolean" ? user.is_active : true,
    is_verified: typeof user.is_verified === "boolean" ? user.is_verified : false,
  };
}

function normalizeSession(rawPayload: unknown): StoredAuthSession | null {
  if (typeof rawPayload !== "object" || rawPayload === null) return null;
  const payload = rawPayload as Record<string, unknown>;
  if (typeof payload.access_token !== "string" || typeof payload.refresh_token !== "string") {
    return null;
  }

  return {
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    expiresAt: typeof payload.expires_at === "string" ? payload.expires_at : null,
    user: normalizeUser(payload.user),
  };
}

export function readStoredSession(): StoredAuthSession | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown> | null;
    if (!parsed || typeof parsed !== "object") return null;
    // Accept both stored camelCase (StoredAuthSession) and raw API snake_case payloads.
    if (typeof parsed.accessToken === "string" && typeof parsed.refreshToken === "string") {
      return {
        accessToken: parsed.accessToken,
        refreshToken: parsed.refreshToken,
        expiresAt: typeof parsed.expiresAt === "string" ? parsed.expiresAt : null,
        user: normalizeUser(parsed.user),
      };
    }
    return normalizeSession(parsed);
  } catch {
    return null;
  }
}

export function writeStoredSession(session: StoredAuthSession) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  dispatchAuthChange();
}

export function clearStoredSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  dispatchAuthChange();
}

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  if (typeof Request !== "undefined" && input instanceof Request) return input.url;
  return String(input);
}

function isPyApiRequest(url: string): boolean {
  return url.startsWith("/py-api/") || url.includes("/py-api/");
}

function isAuthSessionRoute(url: string): boolean {
  return /\/py-api\/auth\/(login|register|refresh)\b/.test(url);
}

function mergeHeaders(
  input: RequestInfo | URL,
  initHeaders?: HeadersInit,
  accessToken?: string,
): Headers {
  const headers = new Headers(
    typeof Request !== "undefined" && input instanceof Request ? input.headers : undefined,
  );

  if (initHeaders) {
    new Headers(initHeaders).forEach((value, key) => {
      headers.set(key, value);
    });
  }

  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return headers;
}

async function performAuthorizedRequest(
  baseFetch: typeof fetch,
  input: RequestInfo | URL,
  init?: RequestInit,
  accessToken?: string,
): Promise<Response> {
  const headers = mergeHeaders(input, init?.headers, accessToken);

  if (typeof Request !== "undefined" && input instanceof Request) {
    return baseFetch(new Request(input, { ...init, headers }));
  }

  return baseFetch(input, { ...init, headers });
}

async function refreshStoredSession(session: StoredAuthSession): Promise<StoredAuthSession | null> {
  let response: Response;
  try {
    response = await getBaseFetch()("/py-api/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: session.refreshToken }),
    });
  } catch {
    // Ağ hatası (container henüz hazır değil, bilgisayar uyku'dan döndü vs.)
    // localStorage'ı SİLME — token hâlâ geçerli olabilir, bir sonraki istekte tekrar dener.
    return null;
  }

  if (response.status === 401 || response.status === 403) {
    // Refresh token gerçekten geçersiz/süresi dolmuş → oturumu kapat
    clearStoredSession();
    return null;
  }

  if (!response.ok) {
    // 5xx, 502, 503 vb. — sunucu/container geçici hatası.
    // localStorage'ı SİLME — bir sonraki istekte tekrar refresh denenecek.
    return null;
  }

  const payload = await response.json();
  const nextSession = normalizeSession({ ...payload, expires_at: session.expiresAt });
  if (!nextSession) {
    clearStoredSession();
    return null;
  }

  writeStoredSession(nextSession);
  return nextSession;
}

export function installAuthAwareFetch() {
  if (typeof window === "undefined" || fetchInstalled) return;

  originalFetchRef = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = getRequestUrl(input);

    if (!isPyApiRequest(url) || isAuthSessionRoute(url)) {
      return getBaseFetch()(input, init);
    }

    const session = readStoredSession();
    const response = await performAuthorizedRequest(getBaseFetch(), input, init, session?.accessToken);

    if (response.status !== 401 || !session?.refreshToken) {
      return response;
    }

    const refreshedSession = await refreshStoredSession(session);
    if (!refreshedSession) {
      return response;
    }

    return performAuthorizedRequest(getBaseFetch(), input, init, refreshedSession.accessToken);
  };

  fetchInstalled = true;
}

const defaultContext: AuthContextValue = {
  session: null,
  user: null,
  isAuthenticated: false,
  isAdmin: false,
  status: "guest",
  login: async () => ({ ok: false, error: "Auth provider not available." }),
  register: async () => ({ ok: false, error: "Auth provider not available." }),
  logout: () => {},
};

const AuthContext = createContext<AuthContextValue>(defaultContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  installAuthAwareFetch();

  const [session, setSession] = useState<StoredAuthSession | null>(() => readStoredSession());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sync = () => {
      setSession(readStoredSession());
    };

    window.addEventListener("storage", sync);
    window.addEventListener(AUTH_CHANGE_EVENT, sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener(AUTH_CHANGE_EVENT, sync);
    };
  }, []);

  const login = useCallback(async (payload: LoginPayload): Promise<AuthActionResult> => {
    setBusy(true);
    try {
      const response = await getBaseFetch()("/py-api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: payload.email,
          password: payload.password,
          remember_me: payload.rememberMe ?? false,
        }),
      });

      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        return {
          ok: false,
          error: typeof body.detail === "string" ? body.detail : "Sign in failed.",
        };
      }

      const nextSession = normalizeSession(body);
      if (!nextSession) {
        return { ok: false, error: "Session payload is invalid." };
      }

      writeStoredSession(nextSession);
      setSession(nextSession);
      return { ok: true };
    } finally {
      setBusy(false);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload): Promise<AuthActionResult> => {
    setBusy(true);
    try {
      const response = await getBaseFetch()("/py-api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: payload.email,
          username: payload.username,
          password: payload.password,
          display_name: payload.displayName || payload.username,
        }),
      });

      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        return {
          ok: false,
          error: typeof body.detail === "string" ? body.detail : "Registration failed.",
        };
      }

      const nextSession = normalizeSession(body);
      if (!nextSession) {
        return { ok: false, error: "Session payload is invalid." };
      }

      writeStoredSession(nextSession);
      setSession(nextSession);
      return { ok: true };
    } finally {
      setBusy(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearStoredSession();
    setSession(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      isAuthenticated: Boolean(session?.accessToken),
      isAdmin: (session?.user?.role ?? "").toLowerCase() === "admin",
      status: busy ? "loading" : session?.accessToken ? "authenticated" : "guest",
      login,
      register,
      logout,
    }),
    [busy, login, logout, register, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
