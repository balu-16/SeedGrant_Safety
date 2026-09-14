/**
 * Background location task. Registered once from the root layout so updates
 * keep uploading while sharing is on, even when the app is backgrounded.
 * Phone GPS only: source is always phone_gps, device_id is never set.
 */
import type { LiveFix } from "../types";

export const BG_LOCATION_TASK = "bg-location-updates";

export function registerBackgroundLocationTask() {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const TaskManager = require("expo-task-manager") as typeof import("expo-task-manager");
    if (TaskManager.isTaskDefined(BG_LOCATION_TASK)) return;
    TaskManager.defineTask<{ locations?: { coords: { latitude: number; longitude: number; accuracy: number | null }; timestamp: number }[] }>(
      BG_LOCATION_TASK,
      async ({ data, error }) => {
        try {
          if (error || !data?.locations?.length) return;
          const raw = data.locations[0];
          const fix: LiveFix = {
            latitude: raw.coords.latitude,
            longitude: raw.coords.longitude,
            accuracy_m: raw.coords.accuracy ?? null,
            recorded_at: new Date(raw.timestamp).toISOString(),
          };
          const { setLastFix, uploadFix } = await import("../services/location");
          const { getAccessToken } = await import("../services/api");
          setLastFix(fix);
          if (getAccessToken()) {
            try {
              await uploadFix(fix);
            } catch {
              // best-effort
            }
          }
        } catch {
          // never crash the task
        }
      },
    );
  } catch {
    // web / missing native module: safe no-op
  }
}
