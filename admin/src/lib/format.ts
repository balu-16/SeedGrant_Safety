export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function fmtRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}

export function initials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function batteryColor(pct: number | null): string {
  if (pct === null) return "var(--tab-inactive)";
  if (pct < 20) return "var(--red)";
  if (pct < 40) return "var(--amber)";
  return "var(--green)";
}

export const TRIGGER_LABELS: Record<string, string> = {
  TAG_BUTTON: "Tag button",
  TAG_VOICE: "Tag voice",
  APP_BUTTON: "App button",
  APP_VOICE: "App voice",
  FALL_DETECTION: "Fall detection",
};

export const STATUS_LABELS: Record<string, string> = {
  active: "Active",
  acknowledged: "Acknowledged",
  resolved: "Resolved",
  cancelled: "Cancelled",
};
