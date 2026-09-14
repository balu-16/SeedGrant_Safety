/* Admin session state: login, role check, restore-on-reload, logout. */

import {
  type ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  adoptTokens,
  clearSession,
  hasSession,
  onSessionLost,
  refreshSession,
  revokeRefreshToken,
} from "../api/client";
import * as api from "../api/services";
import type { AdminUser } from "../api/types";

interface AuthState {
  admin: AdminUser | null;
  booting: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthCtx = createContext<AuthState>({
  admin: null,
  booting: true,
  login: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Restore: rotate the stored refresh token, then confirm the account
      // still exists, is enabled, and holds the admin role.
      if (hasSession() && (await refreshSession())) {
        try {
          const user = await api.me();
          if (!cancelled) {
            if (user.role === "admin") setAdmin(user);
            else await revokeAndClear();
          }
        } catch {
          if (!cancelled) clearSession();
        }
      }
      if (!cancelled) setBooting(false);
    })();
    const off = onSessionLost(() => setAdmin(null));
    return () => {
      cancelled = true;
      off();
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password);
    if (res.user.role !== "admin") {
      // Revoke the pair we just issued — this account has no portal access.
      adoptTokens(res.access_token, res.refresh_token);
      await revokeRefreshToken();
      clearSession();
      throw new Error("This account doesn't have admin access");
    }
    adoptTokens(res.access_token, res.refresh_token);
    setAdmin({
      id: res.user.id,
      email: res.user.email,
      name: res.user.name,
      phone: res.user.phone,
      role: "admin",
      disabled_at: null,
      created_at: "",
      updated_at: "",
    });
  }, []);

  const logout = useCallback(async () => {
    await revokeRefreshToken();
    clearSession();
    setAdmin(null);
  }, []);

  const value = useMemo(
    () => ({ admin, booting, login, logout }),
    [admin, booting, login, logout],
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

async function revokeAndClear() {
  await revokeRefreshToken();
  clearSession();
}

export function useAuth(): AuthState {
  return useContext(AuthCtx);
}
