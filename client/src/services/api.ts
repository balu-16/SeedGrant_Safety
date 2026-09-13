export function apiBaseUrl(): string | null {
  const raw = process.env.EXPO_PUBLIC_API_URL;
  return raw ? raw.replace(/\/$/, "") : null;
}

let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

/** In-memory access token. Phase B persists refresh rotation via SecureStore. */
export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(status: number, payload: unknown): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: string } | undefined;
      if (first?.msg) return first.msg;
    }
  }
  if (status === 401) return "Your session expired. Please sign in again.";
  if (status >= 500) return "The safety service is unavailable. Try again shortly.";
  return "Something went wrong. Please try again.";
}

export async function apiFetch<T>(
  path: string,
  options: { method?: string; body?: unknown; accessToken?: string | null; retry?: boolean } = {}
): Promise<T> {
  const base = apiBaseUrl();
  if (!base) throw new ApiError(0, "The safety service is not configured.");
  const token = options.accessToken ?? accessToken;
  const res = await rawFetch(base, path, options.method ?? "GET", options.body, token);
  if (res.status === 401 && (options.retry ?? true) && path !== "/api/auth/refresh") {
    const renewed = await refreshAccessToken(base);
    if (renewed) {
      const retryRes = await rawFetch(base, path, options.method ?? "GET", options.body, renewed);
      return await parseResponse<T>(retryRes);
    }
  }
  return await parseResponse<T>(res);
}

async function rawFetch(
  base: string,
  path: string,
  method: string,
  body: unknown,
  token: string | null
): Promise<Response> {
  try {
    return await fetch(`${base}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Could not reach the safety service. Check your connection.");
  }
}

/** Single-flight refresh rotation. Returns the new access token or null. */
async function refreshAccessToken(base: string): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const { loadRefreshToken, saveRefreshToken, clearSession } = await import("./session");
        const refreshToken = await loadRefreshToken();
        if (!refreshToken) return null;
        const res = await rawFetch(base, "/api/auth/refresh", "POST", { refresh_token: refreshToken }, null);
        if (!res.ok) {
          await clearSession();
          return null;
        }
        const pair = (await res.json()) as { access_token: string; refresh_token: string };
        setAccessToken(pair.access_token);
        await saveRefreshToken(pair.refresh_token);
        return pair.access_token;
      } catch {
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

async function parseResponse<T>(res: Response): Promise<T> {
  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) throw new ApiError(res.status, errorMessage(res.status, payload));
  return payload as T;
}
