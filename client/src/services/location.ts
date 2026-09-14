import { Platform } from "react-native";
import { apiFetch, getAccessToken } from "./api";
import type { LiveFix } from "../types";

/**
 * Phone-GPS location helpers. Web-safe: expo-location is loaded lazily so
 * the web bundle (Playwright/E2E + browser preview) never touches native code.
 */

let lastFix: LiveFix | null = null;
const fixListeners = new Set<(fix: LiveFix | null) => void>();

export function getLastFix(): LiveFix | null {
  return lastFix;
}

export function setLastFix(fix: LiveFix | null) {
  lastFix = fix;
  fixListeners.forEach((fn) => {
    try {
      fn(fix);
    } catch {
      // ignore broken listeners
    }
  });
}

export function subscribeLastFix(fn: (fix: LiveFix | null) => void): () => void {
  fixListeners.add(fn);
  return () => fixListeners.delete(fn);
}

export function isNative(): boolean {
  return Platform.OS === "android" || Platform.OS === "ios";
}

async function loadLocation(): Promise<typeof import("expo-location") | null> {
  if (!isNative()) return null;
  try {
    return await import("expo-location");
  } catch {
    return null;
  }
}

export type PermissionState = "unknown" | "granted" | "denied" | "unavailable";

export async function ensureForegroundPermission(): Promise<PermissionState> {
  const Location = await loadLocation();
  if (!Location) return "unavailable";
  try {
    const current = await Location.getForegroundPermissionsAsync();
    if (current.status === "granted") return "granted";
    const req = await Location.requestForegroundPermissionsAsync();
    return req.status === "granted" ? "granted" : "denied";
  } catch {
    return "unavailable";
  }
}

export async function ensureBackgroundPermission(): Promise<PermissionState> {
  const Location = await loadLocation();
  if (!Location) return "unavailable";
  try {
    const fg = await ensureForegroundPermission();
    if (fg !== "granted") return fg;
    const current = await Location.getBackgroundPermissionsAsync();
    if (current.status === "granted") return "granted";
    const req = await Location.requestBackgroundPermissionsAsync();
    return req.status === "granted" ? "granted" : "denied";
  } catch {
    return "unavailable";
  }
}

export async function getOneShotFix(timeoutMs = 10000): Promise<LiveFix | null> {
  if (getLastFix()) return getLastFix();
  const Location = await loadLocation();
  if (!Location) return null;
  try {
    const pos = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    const fix: LiveFix = {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      accuracy_m: pos.coords.accuracy ?? null,
      recorded_at: new Date(pos.timestamp).toISOString(),
    };
    setLastFix(fix);
    return fix;
  } catch {
    return null;
  }
}

/** Upload one fix. Silent no-op without backend session; throws only for callers that care. */
export async function uploadFix(fix: LiveFix): Promise<void> {
  const token = getAccessToken();
  if (!token) return;
  await apiFetch("/api/locations", {
    method: "POST",
    accessToken: token,
    retry: false,
    body: {
      latitude: fix.latitude,
      longitude: fix.longitude,
      accuracy_m: fix.accuracy_m ?? undefined,
      source: "phone_gps",
      recorded_at: fix.recorded_at,
    },
  });
}

export function formatCoord(lat: number, lon: number): string {
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}

export function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const mins = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (mins < 1) return "just now";
  if (mins === 1) return "1 min ago";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(iso).toLocaleString();
}
