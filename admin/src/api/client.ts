/* API client: bearer auth, 15s timeout, single-flight 401 -> refresh -> retry.
   Ported from client/src/services/api.ts (web storage instead of SecureStore). */

const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
const REFRESH_KEY = "sst-admin.refresh-token";

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function wsUrl(): string {
  const base = API_URL
    ? API_URL.replace(/^http/, "ws")
    : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
  return `${base}/api/ws`;
}

let accessToken: string | null = null;
let refreshToken: string | null = localStorage.getItem(REFRESH_KEY);
let refreshInFlight: Promise<boolean> | null = null;
const sessionLostListeners = new Set<() => void>();

export function getAccessToken(): string | null {
  return accessToken;
}

export function hasSession(): boolean {
  return refreshToken !== null;
}

export function clearSession(): void {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem(REFRESH_KEY);
}

export function onSessionLost(cb: () => void): () => void {
  sessionLostListeners.add(cb);
  return () => sessionLostListeners.delete(cb);
}

function storePair(access: string, refresh: string): void {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem(REFRESH_KEY, refresh);
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function rawFetch(
  path: string,
  init: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    return await fetch(apiUrl(path), { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const data = await res.json();
    const err = data?.error ?? {};
    return new ApiError(res.status, err.code ?? "error", err.message ?? res.statusText);
  } catch {
    return new ApiError(res.status, "error", res.statusText);
  }
}

interface FetchOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  retry?: boolean;
}

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, retry = true } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  const res = await rawFetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (res.status === 401 && auth && retry) {
    const ok = await refreshSession();
    if (ok) return apiFetch<T>(path, { ...options, retry: false });
    throw new ApiError(401, "unauthorized", "Session expired");
  }
  if (res.status === 204) return undefined as T;
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

/** Single-flight refresh-token rotation; false when the session is gone. */
export async function refreshSession(): Promise<boolean> {
  if (!refreshToken) return false;
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const res = await rawFetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        clearSession();
        sessionLostListeners.forEach((cb) => cb());
        return false;
      }
      const data = (await res.json()) as { access_token: string; refresh_token: string };
      storePair(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

/** Called after a fresh login/restore; keeps tokens for the WS connection. */
export function adoptTokens(access: string, refresh: string): void {
  storePair(access, refresh);
}

export async function revokeRefreshToken(): Promise<void> {
  if (!refreshToken) return;
  try {
    await rawFetch("/api/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // Best effort — clear locally regardless.
  }
}
