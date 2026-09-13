import {
  Device,
  Emergency,
  Guardian,
  LocationPoint,
  SignupInput,
  User,
} from "../types";
import { validateLogin, validateSignup } from "../utils/validation";
export interface AuthService {
  login(email: string, password: string): Promise<User>;
  signup(input: SignupInput): Promise<User>;
  google(): Promise<User>;
  resetPassword(email: string): Promise<void>;
}
export interface LocationService {
  history(): Promise<LocationPoint[]>;
  current(): Promise<LocationPoint>;
}
export interface DeviceService {
  status(): Promise<Device>;
}
export interface EmergencyService {
  trigger(recipients: number): Promise<Emergency>;
}
const pause = () => new Promise<void>((resolve) => setTimeout(resolve, 250));
export const demoUser: User = {
  id: "demo",
  name: "Priya Sharma",
  email: "priya@example.com",
  phone: "+91 90000 00000",
};
export const seedGuardians: Guardian[] = [
  {
    id: "1",
    name: "Ananya Mehta",
    relation: "Mother",
    phone: "+91 90000 00001",
    primary: true,
  },
  {
    id: "2",
    name: "Rohit Mehta",
    relation: "Brother",
    phone: "+91 90000 00002",
    primary: false,
  },
  {
    id: "3",
    name: "Sneha Kapoor",
    relation: "Best Friend",
    phone: "+91 90000 00003",
    primary: false,
  },
];
const history: LocationPoint[] = [
  {
    id: "1",
    name: "At Home",
    address: "Bandra West, Mumbai",
    time: "Today, 8:12 AM",
    current: true,
  },
  {
    id: "2",
    name: "Starbucks",
    address: "Linking Road, Mumbai",
    time: "Today, 7:28 AM",
  },
  {
    id: "3",
    name: "St. Andrew’s College",
    address: "Bandra West, Mumbai",
    time: "Yesterday, 4:15 PM",
  },
  {
    id: "4",
    name: "Evening walk",
    address: "Bandra Sea Face, Mumbai",
    time: "Yesterday, 6:30 PM",
  },
];
export const authService: AuthService = {
  async login(email, password) {
    if (Object.keys(validateLogin(email, password)).length)
      throw new Error("Check your email and password.");
    await pause();
    return { ...demoUser, email: email.trim().toLowerCase() };
  },
  async signup(input) {
    if (Object.keys(validateSignup(input)).length)
      throw new Error("Check your account details.");
    await pause();
    return {
      id: "local",
      name: input.name.trim(),
      email: input.email.trim().toLowerCase(),
      phone: input.phone.trim(),
    };
  },
  async google() {
    await pause();
    return { ...demoUser };
  },
  async resetPassword() {
    await pause();
  },
};
export const locationService: LocationService = {
  async history() {
    return history;
  },
  async current() {
    return history[0];
  },
};
export const deviceService: DeviceService = {
  async status() {
    return { connected: true, battery: 78, name: "Smart Safety Tag" };
  },
};
export const emergencyService: EmergencyService = {
  async trigger(recipients) {
    await pause();
    return {
      id: `alert-${Date.now()}`,
      createdAt: new Date().toISOString(),
      recipients,
      status: "simulated",
    };
  },
};
