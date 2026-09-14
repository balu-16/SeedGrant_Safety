/* Typed endpoint wrappers for /api/auth + /api/admin. */

import { apiFetch } from "./client";
import type {
  AdminHealth,
  AdminStats,
  AdminUser,
  AuditEntry,
  Device,
  Emergency,
  EmergencyEvent,
  GuardianLink,
  LocationPoint,
  Paged,
  PushSendResult,
  PushToken,
  UserDetail,
} from "./types";

export interface LoginResponse {
  user: { id: string; email: string; name: string; phone: string; role: string };
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
}

export function me(): Promise<AdminUser> {
  return apiFetch<AdminUser>("/api/users/me");
}

export function logout(): Promise<void> {
  return apiFetch<void>("/api/auth/logout", { method: "POST", auth: false, body: {} });
}

export function stats(): Promise<AdminStats> {
  return apiFetch<AdminStats>("/api/admin/stats");
}

export function health(): Promise<AdminHealth> {
  return apiFetch<AdminHealth>("/api/admin/health");
}

// ------------------------------------------------------------------ users ---

export function listUsers(params: {
  q?: string;
  role?: string;
  disabled?: boolean;
  limit?: number;
  offset?: number;
}): Promise<Paged<AdminUser>> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.role) query.set("role", params.role);
  if (params.disabled !== undefined && params.disabled !== null)
    query.set("disabled", String(params.disabled));
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/admin/users?${query}`);
}

export function userDetail(userId: string): Promise<UserDetail> {
  return apiFetch(`/api/admin/users/${userId}`);
}

export function updateUser(
  userId: string,
  body: { name?: string; phone?: string },
): Promise<AdminUser> {
  return apiFetch(`/api/admin/users/${userId}`, { method: "PATCH", body });
}

export const disableUser = (userId: string) =>
  apiFetch<AdminUser>(`/api/admin/users/${userId}/disable`, { method: "POST" });

export const enableUser = (userId: string) =>
  apiFetch<AdminUser>(`/api/admin/users/${userId}/enable`, { method: "POST" });

export const forceLogout = (userId: string) =>
  apiFetch<{ revoked: number }>(`/api/admin/users/${userId}/force-logout`, { method: "POST" });

export const resetPassword = (userId: string) =>
  apiFetch<{ temp_password: string }>(`/api/admin/users/${userId}/reset-password`, {
    method: "POST",
  });

export const promoteUser = (userId: string) =>
  apiFetch<AdminUser>(`/api/admin/users/${userId}/promote`, { method: "POST" });

export const demoteUser = (userId: string) =>
  apiFetch<AdminUser>(`/api/admin/users/${userId}/demote`, { method: "POST" });

export const deleteUser = (userId: string) =>
  apiFetch<void>(`/api/admin/users/${userId}`, { method: "DELETE" });

// ---------------------------------------------------------------- devices ---

export function listDevices(params: {
  connection_state?: string;
  low_battery?: boolean;
  limit?: number;
  offset?: number;
}): Promise<Paged<Device>> {
  const query = new URLSearchParams();
  if (params.connection_state) query.set("connection_state", params.connection_state);
  if (params.low_battery) query.set("low_battery", "true");
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/admin/devices?${query}`);
}

export function renameDevice(deviceId: string, name: string): Promise<Device> {
  return apiFetch(`/api/admin/devices/${deviceId}`, { method: "PATCH", body: { name } });
}

export const forceDeviceOffline = (deviceId: string) =>
  apiFetch<Device>(`/api/admin/devices/${deviceId}/force-offline`, { method: "POST" });

export const deleteDevice = (deviceId: string) =>
  apiFetch<void>(`/api/admin/devices/${deviceId}`, { method: "DELETE" });

// --------------------------------------------------------------- guardians ---

export function listGuardians(params: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<Paged<GuardianLink>> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/admin/guardians?${query}`);
}

export const forceGuardianStatus = (guardianId: string, status: string) =>
  apiFetch<GuardianLink>(`/api/admin/guardians/${guardianId}/status`, {
    method: "PATCH",
    body: { status },
  });

export const deleteGuardian = (guardianId: string) =>
  apiFetch<void>(`/api/admin/guardians/${guardianId}`, { method: "DELETE" });

// ------------------------------------------------------------ emergencies ---

export function listEmergencies(params: {
  status?: string;
  trigger_type?: string;
  limit?: number;
  offset?: number;
}): Promise<Paged<Emergency>> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.trigger_type) query.set("trigger_type", params.trigger_type);
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/admin/emergencies?${query}`);
}

export function emergencyDetail(
  emergencyId: string,
): Promise<{ emergency: Emergency; events: EmergencyEvent[] }> {
  return apiFetch(`/api/admin/emergencies/${emergencyId}`);
}

export const ackEmergency = (id: string) =>
  apiFetch<Emergency>(`/api/admin/emergencies/${id}/ack`, { method: "POST" });

export const resolveEmergency = (id: string) =>
  apiFetch<Emergency>(`/api/admin/emergencies/${id}/resolve`, { method: "POST" });

export const cancelEmergency = (id: string) =>
  apiFetch<Emergency>(`/api/admin/emergencies/${id}/cancel`, { method: "POST" });

// -------------------------------------------------------------- locations ---

export const latestLocation = (userId: string) =>
  apiFetch<LocationPoint | null>(`/api/admin/locations/latest?user_id=${userId}`);

export function locationHistory(
  userId: string,
  limit = 100,
): Promise<Paged<LocationPoint>> {
  return apiFetch(
    `/api/admin/locations/history?user_id=${userId}&limit=${limit}&offset=0`,
  );
}

export const purgeLocations = (userId: string) =>
  apiFetch<{ deleted: number }>(`/api/admin/locations?user_id=${userId}`, { method: "DELETE" });

// -------------------------------------------------------------------- push ---

export const listPushTokens = (userId: string) =>
  apiFetch<PushToken[]>(`/api/admin/push-tokens?user_id=${userId}`);

export const deletePushToken = (tokenId: string) =>
  apiFetch<void>(`/api/admin/push-tokens/${tokenId}`, { method: "DELETE" });

export const sendPush = (body: {
  title: string;
  body: string;
  user_ids?: string[];
  all_users?: boolean;
}): Promise<PushSendResult> =>
  apiFetch("/api/admin/push/send", { method: "POST", body });

// ------------------------------------------------------------------- audit ---

export function listAudit(params: {
  action?: string;
  target_type?: string;
  actor_id?: string;
  limit?: number;
  offset?: number;
}): Promise<Paged<AuditEntry>> {
  const query = new URLSearchParams();
  if (params.action) query.set("action", params.action);
  if (params.target_type) query.set("target_type", params.target_type);
  if (params.actor_id) query.set("actor_id", params.actor_id);
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/admin/audit?${query}`);
}
