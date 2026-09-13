import { useEffect, useRef, useState } from "react";
import { useRouter } from "expo-router";
import { useApp } from "../store/AppStore";
import { apiBaseUrl, getAccessToken, onSessionEvent } from "../services/api";
import {
  addPushReceivedListener,
  addPushResponseListener,
  configureNotifications,
  getDevicePushToken,
  registerPushToken,
} from "../services/notifications";

/**
 * Push lifecycle: configure once, register the native FCM/APNs token after
 * sign-in (when the notifications preference is on), and deep-link taps.
 * Silent no-op in mock mode (no API URL / no session token) and on web.
 */
export function useNotifications() {
  const { state } = useApp();
  const router = useRouter();
  const registeredFor = useRef<string | null>(null);
  // Re-run when a background refresh restores the access token (e.g. right
  // after app restart, when registration was skipped for lack of a token).
  const [sessionTick, setSessionTick] = useState(0);
  useEffect(() => onSessionEvent(() => setSessionTick((t) => t + 1)), []);

  useEffect(() => {
    configureNotifications().catch((e) => console.warn("Notification setup failed", e));
    const received = addPushReceivedListener(() => {});
    const response = addPushResponseListener((res) => {
      const kind = res.notification.request.content.data?.kind;
      if (kind === "emergency-created" || kind === "emergency-updated") {
        router.push("/(tabs)/home");
      }
    });
    return () => {
      received?.remove();
      response?.remove();
    };
  }, [router]);

  useEffect(() => {
    const user = state.user;
    if (!user) {
      registeredFor.current = null;
      return;
    }
    if (!state.preferences.notifications) return;
    if (registeredFor.current === user.id) return;
    const base = apiBaseUrl();
    const session = getAccessToken();
    if (!base || !session) return; // mock mode / token not restored yet
    let cancelled = false;
    (async () => {
      try {
        const deviceToken = await getDevicePushToken();
        if (!deviceToken || cancelled) return;
        await registerPushToken(session, deviceToken);
        registeredFor.current = user.id;
      } catch (e) {
        console.warn("Push token registration failed", e);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [state.user, state.preferences.notifications, sessionTick]);
}
