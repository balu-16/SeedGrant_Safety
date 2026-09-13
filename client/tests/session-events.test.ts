import { beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { apiFetch, onSessionEvent, setAccessToken } from "../src/services/api";
import { clearSession, saveRefreshToken } from "../src/services/session";

function jsonResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

describe("session events", () => {
  beforeEach(async () => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
    await clearSession();
  });

  it("emits lost when the refresh token is rejected", async () => {
    const events: string[] = [];
    const unsub = onSessionEvent((e) => events.push(e));
    await saveRefreshToken("bad-refresh");
    setAccessToken("expired");
    (globalThis as Record<string, unknown>).fetch = async (url: string) =>
      url.endsWith("/api/auth/refresh")
        ? jsonResponse(401, { detail: "revoked" })
        : jsonResponse(401, { detail: "expired" });
    await assert.rejects(apiFetch("/api/data"), /expired/);
    assert.deepEqual(events, ["lost"]);
    unsub();
  });

  it("emits restored after a successful refresh rotation", async () => {
    const events: string[] = [];
    const unsub = onSessionEvent((e) => events.push(e));
    await saveRefreshToken("refresh-1");
    setAccessToken("expired");
    (globalThis as Record<string, unknown>).fetch = async (url: string, init?: RequestInit) => {
      if (url.endsWith("/api/auth/refresh")) {
        return jsonResponse(200, { access_token: "fresh", refresh_token: "refresh-2" });
      }
      const auth = ((init?.headers ?? {}) as Record<string, string>).Authorization;
      return auth === "Bearer fresh"
        ? jsonResponse(200, { ok: true })
        : jsonResponse(401, { detail: "expired" });
    };
    await apiFetch("/api/data");
    assert.deepEqual(events, ["restored"]);
    unsub();
  });
});
