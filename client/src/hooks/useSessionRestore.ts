import { useEffect, useRef } from "react";
import { useApp } from "../store/AppStore";
import { apiBaseUrl, getAccessToken, setAccessToken } from "../services/api";
import { loadRefreshToken, saveRefreshToken, clearSession } from "../services/session";
import type { User } from "../types";

/**
 * Cold-start session restore (backend mode only):
 * SecureStore refresh token -> POST /auth/refresh -> GET /users/me.
 * Fixes the "looks signed in but API/WS/push silently no-op after restart" gap.
 * Demo mode (no API URL): no-op.
 */
export function useSessionRestore() {
  const { state, dispatch } = useApp();
  const done = useRef(false);
  useEffect(() => {
    if (done.current || !state.hydrated) return;
    done.current = true;
    (async () => {
      try {
        const base = apiBaseUrl();
        if (!base) return;
        if (getAccessToken()) return; // fresh login already set it
        if (!state.user) return; // nothing to restore
        const refresh = await loadRefreshToken();
        if (!refresh) return;
        const res = await fetch(`${base}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) {
          await clearSession();
          dispatch({ type: "logout" });
          return;
        }
        const pair = (await res.json()) as { access_token: string; refresh_token: string };
        setAccessToken(pair.access_token);
        await saveRefreshToken(pair.refresh_token);
        const meRes = await fetch(`${base}/api/users/me`, {
          headers: { Authorization: `Bearer ${pair.access_token}` },
        });
        if (meRes.ok) {
          const me = (await meRes.json()) as User;
          dispatch({ type: "login", user: me });
        }
      } catch {
        // offline at launch: keep cached profile, realtime/push retry later
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.hydrated]);
}
