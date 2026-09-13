import { beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { ApiError, apiBaseUrl, apiFetch, setAccessToken } from "../src/services/api";

function jsonResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

describe("api client", () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com/";
    setAccessToken(null);
  });

  it("trims trailing slash from base URL", () => {
    assert.equal(apiBaseUrl(), "https://api.example.com");
  });

  it("sends auth header and returns payload", async () => {
    const seen: { url: string; headers: Record<string, string> }[] = [];
    (globalThis as Record<string, unknown>).fetch = async (url: string, init: RequestInit) => {
      seen.push({ url, headers: init.headers as Record<string, string> });
      return jsonResponse(200, { ok: true });
    };
    setAccessToken("abc");
    const out = await apiFetch<{ ok: boolean }>("/api/health");
    assert.deepEqual(out, { ok: true });
    assert.equal(seen[0].url, "https://api.example.com/api/health");
    assert.equal(seen[0].headers.Authorization, "Bearer abc");
  });

  it("maps backend detail strings and validation arrays", async () => {
    (globalThis as Record<string, unknown>).fetch = async () =>
      jsonResponse(422, { detail: [{ msg: "Field required" }] });
    await assert.rejects(apiFetch("/x"), /Field required/);
    (globalThis as Record<string, unknown>).fetch = async () =>
      jsonResponse(401, { detail: "Cross-type tokens rejected" });
    await assert.rejects(apiFetch("/x"), /Cross-type tokens rejected/);
  });

  it("maps network failure to ApiError status 0", async () => {
    (globalThis as Record<string, unknown>).fetch = async () => {
      throw new Error("down");
    };
    const err = await apiFetch("/x").catch((e) => e);
    assert.ok(err instanceof ApiError && err.status === 0);
  });
});
