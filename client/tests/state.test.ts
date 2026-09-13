import { test } from "node:test";
import assert from "node:assert/strict";
import { initialState, parseStored, reducer } from "../src/store/reducer";
import { authService, demoUser } from "../src/services/mock";
import { validateLogin, validateSignup } from "../src/utils/validation";
test("mock auth rejects malformed input and returns no credentials", async () => {
  assert.ok(validateLogin("bad", "tiny").email);
  assert.ok(validateLogin("a@b.com", "short").password);
  await assert.rejects(authService.login("bad", "valid-password"));
  const user = await authService.login(" TEST@EXAMPLE.COM ", "valid-password");
  assert.equal(user.email, "test@example.com");
  assert.equal("password" in user, false);
});
test("signup validates all required fields, confirmation and consent", () => {
  const fields = {
    name: " ",
    email: "bad",
    phone: "12",
    password: "short",
    confirm: "different",
    terms: false,
  };
  assert.deepEqual(Object.keys(validateSignup(fields)).sort(), [
    "confirm",
    "email",
    "name",
    "password",
    "phone",
    "terms",
  ]);
  assert.deepEqual(
    validateSignup({
      name: "Naveen",
      email: "naveen@example.com",
      phone: "+91 90000 12345",
      password: "12345678",
      confirm: "12345678",
      terms: true,
    }),
    {},
  );
});
test("logout clears user data and retains onboarding completion", () => {
  const signedIn = reducer(reducer(initialState, { type: "onboard" }), {
    type: "login",
    user: demoUser,
  });
  const changed = reducer(signedIn, { type: "guardians", guardians: [] });
  const loggedOut = reducer(changed, { type: "logout" });
  assert.equal(loggedOut.user, null);
  assert.equal(loggedOut.onboarding, true);
  assert.equal(loggedOut.alerts.length, 0);
  assert.equal(loggedOut.guardians.length, 3);
});
test("storage ignores malformed payloads and restores supported fields", () => {
  assert.deepEqual(parseStored("{broken"), {});
  assert.deepEqual(parseStored("null"), {});
  assert.deepEqual(
    parseStored(JSON.stringify({ version: 2, onboarding: true })),
    {},
  );
  const valid = parseStored(
    JSON.stringify({
      version: 1,
      onboarding: true,
      user: demoUser,
      guardians: [],
      preferences: { notifications: false, voice: "invalid" },
    }),
  );
  assert.equal(valid.user?.name, "Priya Sharma");
  assert.deepEqual(valid.guardians, []);
  assert.equal(valid.preferences?.notifications, false);
  assert.equal(valid.preferences?.voice, false);
});
test("duplicate emergency completion cannot create duplicate history", () => {
  const alert = {
    id: "one",
    createdAt: new Date().toISOString(),
    recipients: 3,
    status: "simulated" as const,
  };
  const state = reducer(reducer(initialState, { type: "alert", alert }), {
    type: "alert",
    alert,
  });
  assert.equal(state.alerts.length, 1);
});

test("hydration strips unknown profile properties and rejects malformed guardians", () => {
  const state = parseStored(
    JSON.stringify({
      version: 1,
      onboarding: true,
      user: { ...demoUser, password: "must-never-return" },
      guardians: [{ id: 42 }],
      preferences: { constructor: true, notifications: false },
    }),
  );
  assert.equal("password" in (state.user ?? {}), false);
  assert.equal(state.guardians?.length, 3);
  assert.equal(Object.hasOwn(state.preferences ?? {}, "constructor"), false);
});
