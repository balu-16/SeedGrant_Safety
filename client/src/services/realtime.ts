import { apiBaseUrl, getAccessToken } from "./api";

export interface RealtimeEvent {
  type: string;
  [key: string]: unknown;
}

type Listener = (event: RealtimeEvent) => void;

const listeners = new Set<Listener>();
let socket: WebSocket | null = null;
let wanted = false;
let retryTimer: ReturnType<typeof setTimeout> | null = null;

// Auth rejections are terminal: retrying with the same dead token would loop
// forever. The session-restored flow reconnects with a fresh token instead.
const AUTH_CLOSE_CODES = new Set<number>([1002, 1008, 4401]);

export function subscribeRealtime(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function emit(event: RealtimeEvent) {
  listeners.forEach((fn) => {
    try {
      fn(event);
    } catch (e) {
      console.warn("Realtime listener failed", e);
    }
  });
}

function wsUrl(base: string, token: string): string {
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}/api/ws?token=${encodeURIComponent(token)}`;
}

function scheduleReconnect() {
  if (!wanted || retryTimer) return;
  retryTimer = setTimeout(() => {
    retryTimer = null;
    if (!wanted) return;
    // Re-read the token on every attempt: the access token may have been
    // rotated by a background refresh since the original connect.
    const token = getAccessToken();
    if (token) connectRealtime(token);
  }, 3000);
}

export function connectRealtime(token?: string): void {
  const base = apiBaseUrl();
  if (!base || typeof WebSocket === "undefined") return;
  const authToken = token ?? getAccessToken();
  if (!authToken) return;
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }
  wanted = true;
  try {
    const ws = new WebSocket(wsUrl(base, authToken));
    socket = ws;
    ws.onmessage = (msg) => {
      try {
        emit(JSON.parse(String(msg.data)) as RealtimeEvent);
      } catch {
        // ignore malformed frames
      }
    };
    ws.onclose = (event) => {
      if (socket === ws) socket = null;
      if (AUTH_CLOSE_CODES.has(event.code)) {
        wanted = false;
        return;
      }
      scheduleReconnect();
    };
    ws.onerror = () => {
      try {
        ws.close();
      } catch {
        // already closed
      }
    };
  } catch (e) {
    console.warn("Realtime connect failed", e);
    scheduleReconnect();
  }
}

export function disconnectRealtime(): void {
  wanted = false;
  if (retryTimer) {
    clearTimeout(retryTimer);
    retryTimer = null;
  }
  if (socket) {
    try {
      socket.close();
    } catch {
      // ignore
    }
    socket = null;
  }
}
