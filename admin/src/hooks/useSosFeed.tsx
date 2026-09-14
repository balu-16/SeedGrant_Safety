/* Live emergency feed over the admin WebSocket channel.
   One connection for the whole app: the sidebar badge and the Live SOS
   monitor both consume this context. */

import {
  type ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { getAccessToken, refreshSession, wsUrl } from "../api/client";
import { listEmergencies } from "../api/services";
import type { Emergency, WsEmergency } from "../api/types";

interface SosFeed {
  open: Emergency[];
  feed: (WsEmergency & { at: string })[];
  connected: boolean;
  soundOn: boolean;
  setSoundOn: (v: boolean) => void;
  refresh: () => Promise<void>;
}

const FeedCtx = createContext<SosFeed>({
  open: [],
  feed: [],
  connected: false,
  soundOn: false,
  setSoundOn: () => {},
  refresh: async () => {},
});

const OPEN_STATUSES = new Set(["active", "acknowledged"]);

function beep(): void {
  try {
    const Ctx =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.55);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.6);
    osc.onended = () => ctx.close();
  } catch {
    // Audio is best-effort (autoplay policies, etc.).
  }
}

export function SosFeedProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState<Emergency[]>([]);
  const [feed, setFeed] = useState<(WsEmergency & { at: string })[]>([]);
  const [connected, setConnected] = useState(false);
  const [soundOn, setSoundOn] = useState(
    () => localStorage.getItem("sst-admin.sound") === "on",
  );
  const soundRef = useRef(soundOn);
  soundRef.current = soundOn;

  const refresh = useCallback(async () => {
    try {
      const { items } = await listEmergencies({ limit: 100 });
      setOpen(items.filter((e) => OPEN_STATUSES.has(e.status)));
    } catch {
      // Transient errors surface as an empty list until the next event.
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closed = false;
    let retry: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;

    const handleEvent = (event: WsEmergency) => {
      setFeed((prev) => [{ ...event, at: new Date().toISOString() }, ...prev].slice(0, 50));
      setOpen((prev) => {
        const incoming = event.emergency;
        if (!OPEN_STATUSES.has(incoming.status))
          return prev.filter((e) => e.id !== incoming.id);
        // Merge over the previous entry so joined fields (emails) survive —
        // the WS payload carries only the base emergency columns.
        const previous = prev.find((e) => e.id === incoming.id);
        const next = prev.filter((e) => e.id !== incoming.id);
        return [{ ...previous, ...incoming }, ...next];
      });
      if (event.type === "emergency-created" && soundRef.current) beep();
    };

    const connect = () => {
      if (closed) return;
      const token = getAccessToken();
      if (!token) {
        void refreshSession().then((ok) => {
          if (ok && !closed) connect();
        });
        return;
      }
      ws = new WebSocket(`${wsUrl()}?token=${encodeURIComponent(token)}`);
      ws.onopen = () => {
        attempt = 0;
        setConnected(true);
      };
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as WsEmergency | { type: string };
          if (
            (data.type === "emergency-created" || data.type === "emergency-updated") &&
            "emergency" in data
          )
            handleEvent(data);
        } catch {
          // Ignore malformed frames.
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed) {
          attempt += 1;
          retry = setTimeout(connect, Math.min(1000 * attempt, 15000));
        }
      };
      ws.onerror = () => ws?.close();
    };

    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      ws?.close();
    };
  }, []);

  const value = useMemo(
    () => ({
      open,
      feed,
      connected,
      soundOn,
      setSoundOn: (v: boolean) => {
        setSoundOn(v);
        localStorage.setItem("sst-admin.sound", v ? "on" : "off");
      },
      refresh,
    }),
    [open, feed, connected, soundOn, refresh],
  );

  return <FeedCtx.Provider value={value}>{children}</FeedCtx.Provider>;
}

export function useSosFeed(): SosFeed {
  return useContext(FeedCtx);
}
