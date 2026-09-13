import { useEffect, useRef, useState } from "react";
import { useApp } from "../store/AppStore";
import { Device, LocationPoint, SignupInput } from "../types";
import { getAccessToken } from "../services/api";
import { getServices, isBackendMode } from "../services/index";
import { remoteLogout } from "../services/remote/auth";
import { mapEmergency } from "../services/remote/services";
import {
  connectRealtime,
  disconnectRealtime,
  subscribeRealtime,
} from "../services/realtime";
import { getLastRawPushToken, unregisterPushToken } from "../services/notifications";

export function useAuth() {
  const { state, dispatch } = useApp();
  const services = getServices(state.user?.id ?? null);
  return {
    async login(email: string, password: string) {
      dispatch({
        type: "login",
        user: await services.auth.login(email, password),
      });
    },
    async signup(input: SignupInput) {
      dispatch({ type: "login", user: await services.auth.signup(input) });
    },
    async google() {
      dispatch({ type: "login", user: await services.auth.google() });
    },
    reset: services.auth.resetPassword,
    async logout() {
      if (isBackendMode(state.user?.id ?? null)) {
        const token = getAccessToken();
        const rawPush = getLastRawPushToken();
        if (token && rawPush) {
          await unregisterPushToken(token, rawPush);
        }
        await remoteLogout();
        disconnectRealtime();
      }
      dispatch({ type: "logout" });
    },
  };
}

function useInvalidation(): number {
  const [generation, setGeneration] = useState(0);
  useEffect(() => subscribeRealtime(() => setGeneration((g) => g + 1)), []);
  return generation;
}

export function useTracking() {
  const { state } = useApp();
  const services = getServices(state.user?.id ?? null);
  const generation = useInvalidation();
  const [points, setPoints] = useState<LocationPoint[]>([]);
  useEffect(() => {
    let active = true;
    services.location
      .history()
      .then((v) => {
        if (active) setPoints(v);
      })
      .catch((e) => console.warn("Location history failed", e));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.user?.id, generation]);
  return points;
}

export function useDevice() {
  const { state } = useApp();
  const services = getServices(state.user?.id ?? null);
  const generation = useInvalidation();
  const [device, setDevice] = useState<Device | null>(null);
  useEffect(() => {
    let active = true;
    services.device
      .status()
      .then((v) => {
        if (active) setDevice(v);
      })
      .catch((e) => console.warn("Device status failed", e));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.user?.id, generation]);
  return device;
}

export function useEmergency() {
  const { state, dispatch } = useApp();
  const services = getServices(state.user?.id ?? null);
  const busy = useRef(false);
  const [pending, setPending] = useState(false);
  return {
    pending,
    async trigger() {
      if (busy.current) return;
      busy.current = true;
      setPending(true);
      try {
        const alert = await services.emergency.trigger(state.guardians.length);
        dispatch({ type: "alert", alert });
        return alert;
      } finally {
        busy.current = false;
        setPending(false);
      }
    },
  };
}

/** Backend mode: replace local guardians with the server list on sign-in. */
export function useGuardiansSync() {
  const { state, dispatch } = useApp();
  const userId = state.user?.id ?? null;
  useEffect(() => {
    if (!isBackendMode(userId)) return;
    let active = true;
    getServices(userId)
      .guardians?.list()
      .then((guardians) => {
        if (active) dispatch({ type: "guardians", guardians });
      })
      .catch((e) => console.warn("Guardian sync failed", e));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);
}

/** Backend mode: live emergency/device/location events over WebSocket. */
export function useRealtime() {
  const { state, dispatch } = useApp();
  const userId = state.user?.id ?? null;
  useEffect(() => {
    const token = getAccessToken();
    if (!isBackendMode(userId) || !token) {
      disconnectRealtime();
      return;
    }
    connectRealtime(token);
    return subscribeRealtime((event) => {
      if (event.type === "emergency-created" || event.type === "emergency-updated") {
        const emergency = (event.emergency ?? {}) as {
          id?: string;
          status?: string;
          created_at?: string;
        };
        if (emergency.id) {
          dispatch({
            type: "alert",
            alert: mapEmergency(
              {
                id: String(emergency.id),
                status: String(emergency.status ?? "active"),
                created_at: String(emergency.created_at ?? new Date().toISOString()),
              },
              state.guardians.length
            ),
          });
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);
}
