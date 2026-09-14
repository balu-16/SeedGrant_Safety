import { useState } from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { Header } from "../../components/Header";
import { DeviceCard } from "../../components/DeviceCard";
import {
  Avatar,
  Button,
  Card,
  Field,
  IconName,
  LinkText,
  Page,
  Row,
  Sheet,
  Toggle,
  Txt,
  s,
} from "../../components/ui";
import { C } from "../../constants/theme";
import { useApp } from "../../store/AppStore";
import { useAuth } from "../../hooks/useServices";
import { isBackendMode } from "../../services";
import { ApiError } from "../../services/api";
import { validEmail, validPhone } from "../../utils/validation";
const rows: {
  title: string;
  subtitle: string;
  icon: IconName;
  color: string;
}[] = [
  {
    title: "Account Details",
    subtitle: "Update your personal information",
    icon: "person",
    color: C.blue,
  },
  {
    title: "Notification Settings",
    subtitle: "Manage alerts and updates",
    icon: "notifications",
    color: "#F24C5A",
  },
  {
    title: "Permissions",
    subtitle: "Location, contacts and more",
    icon: "shield-checkmark",
    color: C.green,
  },
  {
    title: "Privacy & Security",
    subtitle: "Keep your data safe",
    icon: "lock-closed",
    color: "#7952D9",
  },
  {
    title: "App Preferences",
    subtitle: "Make yourself at home",
    icon: "settings",
    color: "#A87335",
  },
];
export default function ProfileScreen() {
  const { state, dispatch } = useApp();
  const auth = useAuth();
  const [dialog, setDialog] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const [profile, setProfile] = useState({ name: "", email: "", phone: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  function open(title: string) {
    if (title === "Account Details") {
      setProfile({
        name: state.user?.name ?? "",
        email: state.user?.email ?? "",
        phone: state.user?.phone ?? "",
      });
      setErrors({});
    }
    setDialog(title);
  }
  const [savingProfile, setSavingProfile] = useState(false);
  async function saveProfile() {
    const next: Record<string, string> = {};
    if (!profile.name.trim()) next.name = "Enter your name.";
    if (!validEmail(profile.email)) next.email = "Enter a valid email.";
    if (!validPhone(profile.phone)) next.phone = "Enter a valid phone number.";
    setErrors(next);
    if (Object.keys(next).length || !state.user || savingProfile) return;
    const user = {
      ...state.user,
      name: profile.name.trim(),
      email: profile.email.trim().toLowerCase(),
      phone: profile.phone.trim(),
    };
    // Backend stores name+phone (email is identity and immutable server-side).
    if (isBackendMode(state.user.id)) {
      setSavingProfile(true);
      try {
        const { apiFetch } = await import("../../services/api");
        await apiFetch("/api/users/me", {
          method: "PATCH",
          body: { name: user.name, phone: user.phone },
        });
      } catch (e) {
        setErrors({
          general: e instanceof ApiError ? e.message : "Could not save your profile. Please try again.",
        });
        setSavingProfile(false);
        return;
      }
      setSavingProfile(false);
    }
    dispatch({ type: "login", user });
    setDialog("");
  }
  return (
    <Page>
      <Header title="Profile" subtitle="Your safety matters ☀" />
      <Card style={s.row}>
        <Avatar photo name={state.user?.name ?? ""} size={65} />
        <View style={{ flex: 1, gap: 5 }}>
          <Txt style={{ fontSize: 21, fontWeight: "700" }}>
            {state.user?.name}
          </Txt>
          <Txt style={s.muted}>Smart Safety Tag User</Txt>
          <Txt style={{ color: C.muted, fontSize: 12 }}>
            Staying safe, always ♡
          </Txt>
          <LinkText
            title="Edit Profile"
            onPress={() => open("Account Details")}
          />
        </View>
      </Card>
      <DeviceCard />
      <Row
        title="Linked Guardians"
        detail={`${state.guardians.length} Guardians`}
        subtitle="Your safety network"
        icon="people"
        color={C.blue}
        onPress={() => router.push("/guardians")}
      />
      <Txt style={{ fontSize: 23, fontWeight: "700", marginTop: 3 }}>
        Settings
      </Txt>
      <View style={{ gap: 3 }}>
        {rows.map((row) => (
          <Row key={row.title} {...row} onPress={() => open(row.title)} />
        ))}
      </View>
      <Row
        title="Sign Out"
        subtitle="Log out from this device"
        icon="log-out-outline"
        color={C.red}
        onPress={() => open("Sign Out")}
      />
      <Sheet title={dialog} visible={!!dialog} onClose={() => setDialog("")}>
        {dialog === "Account Details" ? (
          <>
            <Field
              placeholder="Full name"
              icon="person-outline"
              value={profile.name}
              autoCapitalize="words"
              onChangeText={(name) => setProfile({ ...profile, name })}
              error={errors.name}
            />
            <Field
              placeholder="Email address"
              icon="mail-outline"
              value={profile.email}
              keyboardType="email-address"
              onChangeText={(email) => setProfile({ ...profile, email })}
              error={errors.email}
            />
            <Field
              placeholder="Phone number"
              icon="call-outline"
              value={profile.phone}
              keyboardType="phone-pad"
              onChangeText={(phone) => setProfile({ ...profile, phone })}
              error={errors.phone}
            />
            {!!errors.general && <Txt style={s.error}>{errors.general}</Txt>}
            <Button title="Save profile" loading={savingProfile} onPress={saveProfile} />
          </>
        ) : dialog === "Notification Settings" ? (
          <>
            <Toggle
              title="Alert notifications"
              value={state.preferences.notifications}
              onChange={(notifications) =>
                dispatch({ type: "preferences", value: { notifications } })
              }
            />
            <Toggle
              title="Vibration"
              value={state.preferences.vibration}
              onChange={(vibration) =>
                dispatch({ type: "preferences", value: { vibration } })
              }
            />
            <Txt style={s.muted}>
              Your choices are saved locally. Push notifications are simulated.
            </Txt>
          </>
        ) : dialog === "Permissions" ? (
          <>
            <Toggle
              title="Location permission"
              subtitle={state.preferences.location ? "Live phone GPS" : "Off — map shows last known"}
              value={state.preferences.location}
              onChange={async (location) => {
                if (location) {
                  const { ensureForegroundPermission } = await import(
                    "../../services/location"
                  );
                  const result = await ensureForegroundPermission();
                  if (result !== "granted") {
                    setErrors({ permission: "Location was not granted. Enable it in system settings to see live GPS." });
                    return;
                  }
                  setErrors({});
                }
                dispatch({ type: "preferences", value: { location } })
              }}
            />
            <Toggle
              title="Contacts permission"
              subtitle="Not used in this phase"
              value={state.preferences.contacts}
              onChange={(contacts) =>
                dispatch({ type: "preferences", value: { contacts } })
              }
            />
            {!!errors.permission && <Txt style={s.error}>{errors.permission}</Txt>}
            <Txt style={s.muted}>
              Location uses your phone GPS for the live map, sharing and SOS.
            </Txt>
          </>
        ) : dialog === "Privacy & Security" ? (
          <>
            <Txt style={s.bold}>How your data is handled</Txt>
            <Txt style={s.muted}>
              Your profile and guardians sync with the safety server when
              signed in; preferences stay on this device. Passwords are never
              saved. Live GPS uploads only while sharing is on.
            </Txt>
            <Txt style={s.muted}>
              Signing out clears your local profile, contacts and preferences.
              Onboarding completion is retained.
            </Txt>
            <Button
              title="View sign-out options"
              secondary
              onPress={() => setDialog("Sign Out")}
            />
          </>
        ) : dialog === "App Preferences" ? (
          <>
            <Toggle
              title="Larger text"
              value={state.preferences.largeText}
              onChange={(largeText) =>
                dispatch({ type: "preferences", value: { largeText } })
              }
            />
            <Toggle
              title="Voice help"
              value={state.preferences.voice}
              onChange={(voice) =>
                dispatch({ type: "preferences", value: { voice } })
              }
            />
            <Txt style={s.muted}>English · Light appearance</Txt>
          </>
        ) : dialog === "Sign Out" ? (
          <>
            <Txt>Sign out of Smart Safety Tag?</Txt>
            <Txt style={s.muted}>
              Your local profile and custom guardians will be cleared. You can
              sign in again to start a new demo.
            </Txt>
            <Button
              title="Confirm sign out"
              danger
              loading={signingOut}
              onPress={async () => {
                setSigningOut(true);
                try {
                  // Await teardown (push unregister, server logout) BEFORE
                  // navigating, so the auth guard never sees a protected route.
                  await auth.logout();
                } finally {
                  setSigningOut(false);
                  router.replace("/login");
                }
              }}
            />
            <Button
              title="Stay signed in"
              secondary
              onPress={() => setDialog("")}
            />
          </>
        ) : null}
      </Sheet>
    </Page>
  );
}
