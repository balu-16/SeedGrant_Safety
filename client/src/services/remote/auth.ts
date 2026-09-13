import { apiFetch, setAccessToken } from "../api";
import { clearSession, loadRefreshToken, saveRefreshToken } from "../session";
import type { SignupInput, User } from "../../types";
import type { AuthService } from "../mock";

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

interface LoginResponse extends TokenPair {
  user: User;
  token_type: string;
  expires_in: number;
}

export const remoteAuth: AuthService = {
  async login(email, password) {
    const res = await apiFetch<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: { email, password },
      retry: false,
    });
    setAccessToken(res.access_token);
    await saveRefreshToken(res.refresh_token);
    return res.user;
  },
  async signup(input: SignupInput) {
    await apiFetch<User>("/api/auth/register", {
      method: "POST",
      body: {
        name: input.name.trim(),
        email: input.email.trim().toLowerCase(),
        phone: input.phone.trim(),
        password: input.password,
      },
      retry: false,
    });
    // Register returns the user only — sign in to establish the session.
    return remoteAuth.login(input.email, input.password);
  },
  async google() {
    throw new Error("Google sign-in is not connected to the server yet.");
  },
  async resetPassword() {
    throw new Error("Password reset is not available on the server yet.");
  },
};

export async function remoteLogout(): Promise<void> {
  try {
    const refreshToken = await loadRefreshToken();
    if (refreshToken) {
      await apiFetch("/api/auth/logout", {
        method: "POST",
        body: { refresh_token: refreshToken },
        retry: false,
      });
    }
  } catch (e) {
    console.warn("Server logout failed", e);
  } finally {
    await clearSession();
  }
}
