import { beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { getServices, isBackendMode } from "../src/services/index";
import {
  mapDeviceStatus,
  mapEmergency,
  mapGuardian,
  mapLocationPoint,
} from "../src/services/remote/services";

describe("service selector", () => {
  beforeEach(() => {
    delete process.env.EXPO_PUBLIC_API_URL;
  });

  it("uses mocks without API URL or user", () => {
    assert.equal(isBackendMode(null), false);
    assert.equal(isBackendMode("u1"), false);
    assert.equal(getServices(null).guardians, null);
  });

  it("uses remote services when configured and signed in", () => {
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
    assert.equal(isBackendMode("u1"), true);
    assert.notEqual(getServices("u1").guardians, null);
  });
});

describe("response mappers", () => {
  it("maps a location fix to a display point", () => {
    const p = mapLocationPoint({
      id: "1",
      latitude: 19.0544,
      longitude: 72.8406,
      source: "phone_gps",
      accuracy_m: 12.4,
      recorded_at: "2026-09-13T06:00:00Z",
    });
    assert.equal(p.id, "1");
    assert.match(p.name, /19\.0544/);
    assert.match(p.address, /phone_gps/);
  });

  it("maps device status with null battery", () => {
    const d = mapDeviceStatus({
      id: "d",
      name: "Tag",
      connected: true,
      battery_pct: null,
      connection_state: "online",
    });
    assert.deepEqual(d, { connected: true, battery: 0, name: "Tag" });
  });

  it("maps guardian invite response", () => {
    const g = mapGuardian({
      id: "g1",
      guardian_email: "a@example.com",
      guardian_name: "",
      relation: "",
      status: "pending",
      is_primary: false,
    });
    assert.equal(g.name, "a@example.com");
    assert.equal(g.primary, false);
  });

  it("maps emergency create response", () => {
    const e = mapEmergency({ id: "e1", status: "active", created_at: "2026-09-13T06:00:00Z" }, 2);
    assert.equal(e.id, "e1");
    assert.equal(e.status, "active");
    assert.equal(e.recipients, 2);
  });
});
