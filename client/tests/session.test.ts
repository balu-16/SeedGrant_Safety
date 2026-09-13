import { beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  ApiError,
  apiFetch,
  getAccessToken,
  setAccessToken,
} from "../src/services/api";
import {
  clearSession,
  loadRefreshToken,
  saveRefreshToken,
} from "../src/services/session";

function jsonResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

describe("session + refresh rotation", () => {
  beforeEach(async () => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
    await clearSession();
  });

  it("retries once after rotating the refresh token", async () => {
    await saveRefreshToken("refresh-1");
    setAccessToken("expired");
    const calls: string[] = [];
    (globalThis as Record<string, unknown>).fetch = async (url: string, init: RequestInit) => {
      calls.push(`${url}|${(init.headers as Record<string, string>).Authorization ?? "none"}`);
      if (url.endsWith("/api/auth/refresh")) {
        return jsonResponse(200, { access_token: "fresh", refresh_token: "refresh-2" });
      }
      if ((init.headers as Record<string, string>).Authorization === "Bearer fresh") {
        return jsonResponse(200, { ok: true });
      }
      return jsonResponse(401, { detail: "expired" });
    };
    const out = await apiFetch<{ ok: boolean }>("/api/data");
    assert.deepEqual(out, { ok: true });
    assert.equal(getAccessToken(), "fresh");
    assert.equal(await loadRefreshToken(), "refresh-2");
    assert.equal(calls.filter((c) => c.includes("/api/auth/refresh")).length, 1);
  });

  it("clears the session when refresh is rejected", async () => {
    await saveRefreshToken("bad-refresh");
    setAccessToken("expired");
    (globalThis as Record<string, unknown>).fetch = async (url: string) => {
      if (url.endsWith("/api/auth/refresh")) return jsonResponse(401, { detail: "revoked" });
      return jsonResponse(401, { detail: "expired" });
    };
    await assert.rejects(apiFetch("/api/data"), /expired/);
    assert.equal(getAccessToken(), null);
    assert.equal(await loadRefreshToken(), null);
  });

  it("surfaces 401 when no refresh token exists", async () => {
    setAccessToken("expired");
    (globalThis as Record<string, unknown>).fetch = async () =>
      jsonResponse(401, { detail: "expired" });
    const err = await apiFetch("/api/data").catch((e) => e);
    assert.ok(err instanceof ApiError && err.status === 401);
  });
});
