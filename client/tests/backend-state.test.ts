import { describe, it } from "node:test";
import assert from "node:assert/strict";

/**
 * Backend-mode users must not see the fake demo guardians; the server list
 * replaces the (empty) circle after sign-in.
 */
describe("backend-mode initial state", () => {
  it("starts with an empty guardian circle when the API is configured", async () => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
    const { initialState } = await import("../src/store/reducer");
    assert.deepEqual(initialState.guardians, []);
    delete process.env.EXPO_PUBLIC_API_URL;
  });
});
