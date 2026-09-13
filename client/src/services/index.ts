import { apiBaseUrl } from "./api";
import {
  authService as mockAuth,
  deviceService as mockDevice,
  emergencyService as mockEmergency,
  locationService as mockLocation,
  type AuthService,
  type DeviceService,
  type EmergencyService,
  type LocationService,
} from "./mock";
import {
  createRemoteLocation,
  remoteDevice,
  remoteEmergency,
  remoteGuardians,
} from "./remote/services";
import { remoteAuth } from "./remote/auth";

export interface ServiceSet {
  auth: AuthService;
  location: LocationService;
  device: DeviceService;
  emergency: EmergencyService;
  guardians: typeof remoteGuardians | null;
}

/** Real backend when configured + signed in; otherwise the local demo mocks. */
export function isBackendMode(userId: string | null): boolean {
  return !!userId && apiBaseUrl() !== null;
}

/**
 * Auth targets the real API whenever one is configured — including the
 * pre-login screens, where no user exists yet. Data services still need a
 * signed-in user.
 */
export function getAuthServices(): Pick<ServiceSet, "auth"> {
  return { auth: apiBaseUrl() !== null ? remoteAuth : mockAuth };
}

export function getServices(userId: string | null): ServiceSet {
  if (!isBackendMode(userId)) {
    return {
      auth: mockAuth,
      location: mockLocation,
      device: mockDevice,
      emergency: mockEmergency,
      guardians: null,
    };
  }
  return {
    auth: remoteAuth,
    location: createRemoteLocation(userId as string),
    device: remoteDevice,
    emergency: remoteEmergency,
    guardians: remoteGuardians,
  };
}
