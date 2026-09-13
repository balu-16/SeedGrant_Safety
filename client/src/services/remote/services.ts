import { apiFetch } from "../api";
import type { Device, Emergency, Guardian, LocationPoint } from "../../types";
import type { DeviceService, EmergencyService, LocationService } from "../mock";

export function mapLocationPoint(item: {
  id: string;
  latitude: number;
  longitude: number;
  source: string;
  accuracy_m: number | null;
  recorded_at: string;
}): LocationPoint {
  const when = new Date(item.recorded_at);
  return {
    id: String(item.id),
    name: `${item.latitude.toFixed(4)}, ${item.longitude.toFixed(4)}`,
    address: `${item.source}${item.accuracy_m ? ` · ±${Math.round(item.accuracy_m)}m` : ""}`,
    time: Number.isNaN(when.getTime()) ? item.recorded_at : when.toLocaleString(),
  };
}

export function createRemoteLocation(userId: string): LocationService {
  async function history(): Promise<LocationPoint[]> {
    const res = await apiFetch<{ items: unknown[] }>(
      `/api/locations/history?user_id=${encodeURIComponent(userId)}&limit=50&offset=0`
    );
    return (res.items as Parameters<typeof mapLocationPoint>[0][]).map(mapLocationPoint);
  }
  async function current(): Promise<LocationPoint> {
    const item = await apiFetch<Parameters<typeof mapLocationPoint>[0] | null>(
      `/api/locations/latest?user_id=${encodeURIComponent(userId)}`
    );
    if (!item) throw new Error("No location shared yet.");
    return mapLocationPoint(item);
  }
  return { history, current };
}

interface DeviceStatusResponse {
  id: string;
  name: string;
  connected: boolean;
  battery_pct: number | null;
  connection_state: string;
}

export function mapDeviceStatus(res: DeviceStatusResponse): Device {
  return {
    connected: res.connected,
    battery: res.battery_pct ?? 0,
    name: res.name,
  };
}

export const remoteDevice: DeviceService = {
  async status(): Promise<Device> {
    const devices = await apiFetch<{ id: string }[]>("/api/devices");
    if (!devices.length) {
      return { connected: false, battery: 0, name: "No tag paired" };
    }
    const res = await apiFetch<DeviceStatusResponse>(`/api/devices/${devices[0].id}/status`);
    return mapDeviceStatus(res);
  },
};

interface EmergencyResponse {
  id: string;
  status: string;
  created_at: string;
}

export function mapEmergency(res: EmergencyResponse, recipients: number): Emergency {
  return {
    id: String(res.id),
    createdAt: res.created_at,
    recipients,
    status: res.status,
  };
}

export const remoteEmergency: EmergencyService = {
  async trigger(recipients: number): Promise<Emergency> {
    const res = await apiFetch<EmergencyResponse>("/api/emergencies", {
      method: "POST",
      body: { trigger_type: "APP_BUTTON" },
    });
    return mapEmergency(res, recipients);
  },
};

interface GuardianResponse {
  id: string;
  guardian_email: string;
  guardian_name: string;
  relation: string;
  status: string;
  is_primary: boolean;
}

export function mapGuardian(g: GuardianResponse): Guardian {
  return {
    id: String(g.id),
    name: g.guardian_name || g.guardian_email,
    relation: g.relation || g.status,
    phone: "",
    primary: g.is_primary,
  };
}

export const remoteGuardians = {
  async list(): Promise<Guardian[]> {
    const items = await apiFetch<GuardianResponse[]>("/api/guardians");
    return items.filter((g) => g.status !== "removed").map(mapGuardian);
  },
  async invite(input: { email: string; name: string; relation: string; primary: boolean }): Promise<Guardian> {
    const res = await apiFetch<GuardianResponse>("/api/guardians/invite", {
      method: "POST",
      body: {
        guardian_email: input.email,
        guardian_name: input.name,
        relation: input.relation,
        is_primary: input.primary,
      },
    });
    return mapGuardian(res);
  },
  async remove(id: string): Promise<void> {
    await apiFetch(`/api/guardians/${encodeURIComponent(id)}`, { method: "DELETE" });
  },
};
