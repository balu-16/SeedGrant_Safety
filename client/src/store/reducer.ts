import { AppState, Emergency, Guardian, Preferences, User } from "../types";
import { seedGuardians } from "../services/mock";
export const initialState: AppState = {
  hydrated: false,
  onboarding: false,
  user: null,
  guardians: seedGuardians,
  sharing: true,
  preferences: {
    notifications: true,
    location: true,
    contacts: true,
    voice: false,
    vibration: true,
    largeText: false,
  },
  alerts: [],
};
export type Action =
  | { type: "hydrate"; payload: Partial<AppState> }
  | { type: "onboard" }
  | { type: "login"; user: User }
  | { type: "logout" }
  | { type: "guardians"; guardians: Guardian[] }
  | { type: "sharing"; value: boolean }
  | { type: "preferences"; value: Partial<Preferences> }
  | { type: "alert"; alert: Emergency };
export function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "hydrate":
      return {
        ...state,
        ...action.payload,
        preferences: { ...state.preferences, ...action.payload.preferences },
        hydrated: true,
      };
    case "onboard":
      return { ...state, onboarding: true };
    case "login":
      return { ...state, user: action.user, onboarding: true };
    case "logout":
      return { ...initialState, hydrated: true, onboarding: state.onboarding };
    case "guardians":
      return { ...state, guardians: action.guardians };
    case "sharing":
      return { ...state, sharing: action.value };
    case "preferences":
      return {
        ...state,
        preferences: { ...state.preferences, ...action.value },
      };
    case "alert":
      return state.alerts.some((a) => a.id === action.alert.id)
        ? state
        : { ...state, alerts: [action.alert, ...state.alerts] };
  }
}
function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function storedUser(value: unknown): User | null {
  if (
    !record(value) ||
    typeof value.id !== "string" ||
    typeof value.name !== "string" ||
    typeof value.email !== "string" ||
    typeof value.phone !== "string"
  )
    return null;
  return {
    id: value.id,
    name: value.name,
    email: value.email,
    phone: value.phone,
  };
}
function storedGuardian(value: unknown): Guardian | null {
  if (
    !record(value) ||
    typeof value.id !== "string" ||
    typeof value.name !== "string" ||
    typeof value.relation !== "string" ||
    typeof value.phone !== "string" ||
    typeof value.primary !== "boolean"
  )
    return null;
  return {
    id: value.id,
    name: value.name,
    relation: value.relation,
    phone: value.phone,
    primary: value.primary,
  };
}
export function parseStored(raw: string | null): Partial<AppState> {
  if (!raw) return {};
  try {
    const value: unknown = JSON.parse(raw);
    if (
      !record(value) ||
      value.version !== 1 ||
      typeof value.onboarding !== "boolean"
    )
      return {};
    const user = storedUser(value.user);
    const parsed = Array.isArray(value.guardians)
      ? value.guardians.map(storedGuardian)
      : null;
    const guardians =
      parsed &&
      parsed.every((guardian): guardian is Guardian => guardian !== null)
        ? parsed
        : seedGuardians;
    const preferences = record(value.preferences)
      ? Object.fromEntries(
          Object.entries(value.preferences).filter(
            ([key, setting]) =>
              Object.hasOwn(initialState.preferences, key) &&
              typeof setting === "boolean",
          ),
        )
      : {};
    return {
      onboarding: value.onboarding,
      user,
      guardians: user ? guardians : seedGuardians,
      preferences: { ...initialState.preferences, ...preferences },
    };
  } catch {
    return {};
  }
}
