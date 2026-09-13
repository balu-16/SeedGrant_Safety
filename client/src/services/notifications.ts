import { Platform } from "react-native";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { apiFetch } from "./api";

/** Must match SOS_CHANNEL_ID in server/app/notifications/fcm.py. */
export const SOS_CHANNEL_ID = "sos";

export type PushPlatform = "android" | "ios" | "web" | "unknown";

export function mapDeviceType(type: string | undefined): PushPlatform {
  if (type === "android") return "android";
  if (type === "ios") return "ios";
  if (type === "web") return "web";
  return "unknown";
}

export function isPushSupported(): boolean {
  return Platform.OS === "android" || Platform.OS === "ios";
}

/** Foreground presentation + SOS channel. Call once at app startup. */
export async function configureNotifications(): Promise<void> {
  if (!isPushSupported()) return;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldPlaySound: true,
      shouldSetBadge: true,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync(SOS_CHANNEL_ID, {
      name: "SOS alerts",
      description: "High-priority emergency alerts from your guardians and tag.",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 500, 250, 500],
      lightColor: "#EB493D",
      lockscreenVisibility: Notifications.AndroidNotificationVisibility.PUBLIC,
    });
  }
}

export interface DevicePushToken {
  token: string;
  platform: PushPlatform;
}

let lastRawToken: string | null = null;

export function getLastRawPushToken(): string | null {
  return lastRawToken;
}

/**
 * Request permission and fetch the native FCM/APNs device token.
 * Returns null on web, emulator-without-Play-services, or denial —
 * callers treat null as "push unavailable", never as an error.
 */
export async function getDevicePushToken(): Promise<DevicePushToken | null> {
  if (!isPushSupported() || !Device.isDevice) return null;
  const { status: existing } = await Notifications.getPermissionsAsync();
  const status =
    existing === "granted" ? existing : (await Notifications.requestPermissionsAsync()).status;
  if (status !== "granted") return null;
  try {
    const deviceToken = await Notifications.getDevicePushTokenAsync();
    if (deviceToken.type === "android" || deviceToken.type === "ios") {
      lastRawToken = deviceToken.data;
      return { token: deviceToken.data, platform: mapDeviceType(deviceToken.type) };
    }
    return null;
  } catch (e) {
    console.warn("Push token fetch failed (google-services.json / Play services?)", e);
    return null;
  }
}

export async function registerPushToken(
  accessToken: string,
  token: DevicePushToken
): Promise<void> {
  await apiFetch("/api/push-tokens", {
    method: "POST",
    accessToken,
    body: { token: token.token, platform: token.platform },
  });
}

export async function unregisterPushToken(accessToken: string, rawToken: string): Promise<void> {
  try {
    await apiFetch(`/api/push-tokens?token=${encodeURIComponent(rawToken)}`, {
      method: "DELETE",
      accessToken,
      retry: false,
    });
    if (lastRawToken === rawToken) lastRawToken = null;
  } catch (e) {
    console.warn("Push token unregister failed", e);
  }
}

export type NotificationSubscription = { remove(): void };

export function addPushReceivedListener(
  listener: (notification: Notifications.Notification) => void
): NotificationSubscription | null {
  if (!isPushSupported()) return null;
  return Notifications.addNotificationReceivedListener(listener);
}

export function addPushResponseListener(
  listener: (response: Notifications.NotificationResponse) => void
): NotificationSubscription | null {
  if (!isPushSupported()) return null;
  return Notifications.addNotificationResponseReceivedListener(listener);
}
