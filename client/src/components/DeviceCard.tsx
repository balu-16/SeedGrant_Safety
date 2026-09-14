import { useEffect, useState } from "react";
import { Platform, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useDevice } from "../hooks/useServices";
import { useLastFix } from "../hooks/useLiveLocation";
import { useApp } from "../store/AppStore";
import { isBackendMode } from "../services";
import { C } from "../constants/theme";
import { Card, Icon, Sheet, Txt, s } from "./ui";
export function DeviceCard() {
  const device = useDevice();
  const { state } = useApp();
  const liveFix = useLastFix();
  const backend = isBackendMode(state.user?.id ?? null);
  const [phoneBattery, setPhoneBattery] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (Platform.OS === "web") return;
    let active = true;
    (async () => {
      try {
        const Battery = await import("expo-battery");
        const level = await Battery.getBatteryLevelAsync();
        if (active) setPhoneBattery(Math.round(level * 100));
      } catch {
        // battery unavailable — fall back to server/mock device value
      }
    })();
    return () => {
      active = false;
    };
  }, []);
  // No tag hardware in this phase: the phone is the safety device.
  // Backend device (if ever registered) still shows through useDevice;
  // otherwise show live phone-GPS state with the same card design.
  const battery = phoneBattery ?? device?.battery ?? null;
  const live = !!liveFix || state.preferences.location;
  const statusLabel = backend
    ? liveFix
      ? "Phone GPS · Live"
      : state.sharing
        ? "Phone GPS · Waiting for fix"
        : "Phone GPS · Sharing paused"
    : device?.connected
      ? "Connected"
      : "Checking device…";
  return (
    <>
      <Card label="Safety Tag" onPress={() => setOpen(true)} style={s.row}>
        <View style={{ width: 55, alignItems: "center" }}>
          <LinearGradient
            colors={["#444A48", "#111716"]}
            style={{
              width: 33,
              height: 50,
              borderRadius: 17,
              alignItems: "center",
              paddingTop: 6,
              borderWidth: 2,
              borderColor: "#555A58",
            }}
          >
            <View
              style={{
                width: 6,
                height: 6,
                borderRadius: 4,
                backgroundColor: "#D8DDDE",
              }}
            />
            <View
              style={{
                width: 3,
                height: 3,
                borderRadius: 2,
                backgroundColor: "#23DC47",
                marginTop: 8,
              }}
            />
          </LinearGradient>
        </View>
        <View style={{ flex: 1, gap: 4 }}>
          <Txt style={s.bold}>Smart Safety Tag</Txt>
          <Txt style={{ color: C.green, fontWeight: "600" }}>
            {statusLabel}
          </Txt>
          <View style={s.row}>
            <Icon name="battery-half" color={C.green} size={22} />
            <Txt style={s.muted}>{battery ?? "—"}%</Txt>
          </View>
        </View>
        <Icon name="chevron-forward" color={C.muted} size={19} />
      </Card>
      <Sheet
        title="Smart Safety Tag"
        visible={open}
        onClose={() => setOpen(false)}
      >
        <Txt>
          {statusLabel}
          {battery !== null ? ` · Battery ${battery}%` : ""}
        </Txt>
        <Txt style={s.muted}>
          {backend || live
            ? "Your phone is the safety device in this phase — live GPS is shared with guardians while sharing is on. No tag hardware required."
            : "Demo device connection. Your phone assists with location tracking."}
        </Txt>
      </Sheet>
    </>
  );
}
