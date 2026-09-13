export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
}
export interface Guardian {
  id: string;
  name: string;
  relation: string;
  phone: string;
  primary: boolean;
}
export interface LocationPoint {
  id: string;
  name: string;
  address: string;
  time: string;
  current?: boolean;
}
export interface Device {
  connected: boolean;
  battery: number;
  name: string;
}
export interface Emergency {
  id: string;
  createdAt: string;
  recipients: number;
  status: string;
}
export interface Preferences {
  notifications: boolean;
  location: boolean;
  contacts: boolean;
  voice: boolean;
  vibration: boolean;
  largeText: boolean;
}
export interface AppState {
  hydrated: boolean;
  onboarding: boolean;
  user: User | null;
  guardians: Guardian[];
  sharing: boolean;
  preferences: Preferences;
  alerts: Emergency[];
}
export type SignupInput = {
  name: string;
  email: string;
  phone: string;
  password: string;
  confirm: string;
  terms: boolean;
};
