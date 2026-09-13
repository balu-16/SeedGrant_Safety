import { describe, it } from "node:test";
import assert from "node:assert/strict";

/**
 * Auth-selector regression: remote auth must be selectable BEFORE any user
 * exists (the login screen renders with no signed-in user).
 */
describe("auth service selection", () => {
  it("selects remote auth when the API is configured, even with no user", async () => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
    const { getAuthServices } = await import("../src/services/index");
    const { remoteAuth } = await import("../src/services/remote/auth");
    assert.equal(getAuthServices().auth, remoteAuth);
  });

  it("falls back to mock auth when no API URL is set", async () => {
    delete process.env.EXPO_PUBLIC_API_URL;
    const { getAuthServices } = await import("../src/services/index");
    const { authService: mockAuth } = await import("../src/services/mock");
    assert.equal(getAuthServices().auth, mockAuth);
  });
});
