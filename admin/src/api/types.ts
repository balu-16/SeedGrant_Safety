/* Shapes returned by the shared FastAPI backend (server/app/*). */

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  phone: string;
  role: "user" | "admin";
  disabled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  owner_id: string;
  name: string;
  battery_pct: number | null;
  connection_state: "online" | "offline" | "unknown";
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
  owner_email?: string | null;
  owner_name?: string | null;
}

export interface GuardianLink {
  id: string;
  protected_user_id: string;
  guardian_user_id: string | null;
  guardian_email: string;
  guardian_name: string;
  relation: string;
  status: "pending" | "accepted" | "rejected" | "removed";
  is_primary: boolean;
  created_at: string;
  updated_at: string;
  protected_email?: string | null;
  protected_name?: string | null;
  guardian_account_email?: string | null;
}

export interface Emergency {
  id: string;
  protected_user_id: string;
  device_id: string | null;
  trigger_type:
    | "TAG_BUTTON"
    | "TAG_VOICE"
    | "APP_BUTTON"
    | "APP_VOICE"
    | "FALL_DETECTION";
  status: "active" | "acknowledged" | "resolved" | "cancelled";
  latitude: number | null;
  longitude: number | null;
  note: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  protected_email?: string | null;
  protected_name?: string | null;
  protected_phone?: string | null;
}

export interface EmergencyEvent {
  id: string;
  emergency_id: string;
  actor_user_id: string | null;
  actor_email?: string | null;
  from_status: string | null;
  to_status: string;
  created_at: string;
}

export interface LocationPoint {
  id: string;
  user_id: string;
  device_id: string | null;
  latitude: number;
  longitude: number;
  accuracy_m: number | null;
  source: string;
  recorded_at: string;
  created_at: string;
}

export interface PushToken {
  id: string;
  user_id: string;
  platform: string;
  created_at: string;
  last_seen_at: string;
}

export interface RefreshSession {
  id: string;
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
}

export interface UserDetail {
  user: AdminUser;
  devices: Device[];
  guardians: GuardianLink[];
  emergencies: Emergency[];
  push_tokens: PushToken[];
  active_sessions: RefreshSession[];
}

export interface Paged<T> {
  items: T[];
  total: number;
}

export interface AdminStats {
  totals: {
    users_total: number;
    users_new_7d: number;
    users_new_30d: number;
    devices_total: number;
    devices_online: number;
    guardians_accepted: number;
    guardians_pending: number;
    emergencies_open: number;
    emergencies_30d: number;
    push_tokens_total: number;
  };
  series: { day: string; signups: number; emergencies: number }[];
}

export interface AdminHealth {
  status: string;
  env: string;
  database: string;
  push_provider: string;
  fcm_configured: boolean;
  admin_bootstrap_emails: number;
}

export interface AuditEntry {
  id: string;
  actor_user_id: string | null;
  actor_email?: string | null;
  actor_name?: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface PushSendResult {
  provider: string;
  message_id: string;
  delivered_to: string[];
  audience_size: number;
}

export interface WsEmergency {
  type: "emergency-created" | "emergency-updated";
  emergency: Emergency;
}
