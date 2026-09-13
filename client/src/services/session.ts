/**
 * Refresh-token persistence. SecureStore on device, in-memory fallback
 * (web/test) when the native module is unavailable.
 */
const REFRESH_KEY = "smart-safety.refresh-token";

let memoryToken: string | null = null;
let secureStore: typeof import("expo-secure-store") | null | undefined;

async function store(): Promise<typeof import("expo-secure-store") | null> {
  if (secureStore !== undefined) return secureStore;
  try {
    secureStore = await import("expo-secure-store");
  } catch {
    secureStore = null;
  }
  return secureStore;
}

export async function saveRefreshToken(token: string): Promise<void> {
  memoryToken = token;
  const s = await store();
  if (s) {
    try {
      await s.setItemAsync(REFRESH_KEY, token);
    } catch (e) {
      console.warn("SecureStore save failed", e);
    }
  }
}

export async function loadRefreshToken(): Promise<string | null> {
  if (memoryToken) return memoryToken;
  const s = await store();
  if (!s) return null;
  try {
    const value = await s.getItemAsync(REFRESH_KEY);
    if (value) memoryToken = value;
    return value;
  } catch (e) {
    console.warn("SecureStore load failed", e);
    return memoryToken;
  }
}

export async function clearSession(): Promise<void> {
  const { setAccessToken } = await import("./api");
  memoryToken = null;
  setAccessToken(null);
  const s = await store();
  if (s) {
    try {
      await s.deleteItemAsync(REFRESH_KEY);
    } catch (e) {
      console.warn("SecureStore clear failed", e);
    }
  }
}
