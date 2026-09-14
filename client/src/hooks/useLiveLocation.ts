import { useEffect, useState } from "react";
import { AppState as RNAppState, Platform } from "react-native";
import { useApp } from "../store/AppStore";
import { getAccessToken } from "../services/api";
import {
  ensureBackgroundPermission,
  ensureForegroundPermission,
  getLastFix,
  setLastFix,
  subscribeLastFix,
  uploadFix,
  type PermissionState,
} from "../services/location";
import type { LiveFix } from "../types";

const BG_TASK = "bg-location-updates";

/**
 * Live phone-GPS lifecycle (Android-first, phone_gps only):
 * - requests foreground permission on mount (native only, sharing on)
 * - foreground watchPosition while the screen tree is mounted
 * - uploads each fix while sharing is on + signed in
 * - background updates while sharing is on (same JS task, foreground service)
 * Web: no-op, demo/mock history remains the source.
 */
export function useLiveLocation(opts?: { enableBackground?: boolean }) {
  const { state } = useApp();
  const [fix, setFix] = useState<LiveFix | null>(() => getLastFix());
  const [permission, setPermission] = useState<PermissionState>("unknown");
  const sharing = state.sharing;
  const locationPref = state.preferences.location;
  const userId = state.user?.id ?? null;

  useEffect(() => subscribeLastFix(setFix), []);

  useEffect(() => {
    if (Platform.OS === "web" || !userId || !sharing || !locationPref) return;
    let watch: { remove(): void } | null = null;
    let cancelled = false;
    (async () => {
      try {
        const Location = await import("expo-location");
        const fg = await ensureForegroundPermission();
        if (cancelled) return;
        setPermission(fg);
        if (fg !== "granted") return;
        if (opts?.enableBackground !== false) {
          try {
            const bg = await ensureBackgroundPermission();
            if (!cancelled && bg === "granted") {
              const started = await Location.hasStartedLocationUpdatesAsync(BG_TASK).catch(
                () => false,
              );
              if (!started) {
                await Location.startLocationUpdatesAsync(BG_TASK, {
                  accuracy: Location.Accuracy.Balanced,
                  timeInterval: 60000,
                  distanceInterval: 25,
                  showsBackgroundLocationIndicator: true,
                  foregroundService: {
                    notificationTitle: "Sharing your location",
                    notificationBody: "Your guardians can see you while sharing is on.",
                  },
                }).catch(() => {});
              }
            }
          } catch {
            // background is best-effort; foreground watch still works
          }
        }
        if (cancelled) return;
        watch = await Location.watchPositionAsync(
          {
            accuracy: Location.Accuracy.Balanced,
            timeInterval: 10000,
            distanceInterval: 10,
          },
          async (pos) => {
            const next: LiveFix = {
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude,
              accuracy_m: pos.coords.accuracy ?? null,
              recorded_at: new Date(pos.timestamp).toISOString(),
            };
            setLastFix(next);
            try {
              if (getAccessToken()) await uploadFix(next);
            } catch {
              // fire-and-forget: a failed upload must not break the watch
            }
          },
        );
      } catch {
        if (!cancelled) setPermission("unavailable");
      }
    })();
    return () => {
      cancelled = true;
      try {
        watch?.remove();
      } catch {
        // ignore
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, sharing, locationPref]);

  // Stop background updates when sharing turns off or on logout.
  useEffect(() => {
    if (Platform.OS === "web") return;
    if (sharing && locationPref && userId) return;
    (async () => {
      try {
        const Location = await import("expo-location");
        const started = await Location.hasStartedLocationUpdatesAsync(BG_TASK).catch(
          () => false,
        );
        if (started) await Location.stopLocationUpdatesAsync(BG_TASK).catch(() => {});
      } catch {
        // ignore
      }
    })();
  }, [sharing, userId, locationPref]);

  // Keep the OS watch alive across foreground/background app state; the
  // subscription itself survives, this just nudges a one-shot refresh.
  useEffect(() => {
    if (Platform.OS === "web") return;
    const sub = RNAppState.addEventListener("change", () => {});
    return () => sub.remove();
  }, []);

  return { fix, permission };
}

/** Subscribe to the shared last-fix singleton (no watch of its own). */
export function useLastFix() {
  const [fix, setFix] = useState<LiveFix | null>(() => getLastFix());
  useEffect(() => subscribeLastFix(setFix), []);
  return fix;
}
