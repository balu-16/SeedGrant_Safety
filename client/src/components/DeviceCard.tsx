import { useState } from "react";
import { View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useDevice } from "../hooks/useServices";
import { C } from "../constants/theme";
import { Card, Icon, Sheet, Txt, s } from "./ui";
export function DeviceCard() {
  const device = useDevice();
  const [open, setOpen] = useState(false);
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
            {device?.connected ? "Connected" : "Checking device…"}
          </Txt>
          <View style={s.row}>
            <Icon name="battery-half" color={C.green} size={22} />
            <Txt style={s.muted}>{device?.battery ?? "—"}%</Txt>
          </View>
        </View>
        <Icon name="chevron-forward" color={C.muted} size={19} />
      </Card>
      <Sheet
        title="Smart Safety Tag"
        visible={open}
        onClose={() => setOpen(false)}
      >
        <Txt>Connected · Battery {device?.battery}%</Txt>
        <Txt style={s.muted}>
          Demo device connection. Your phone assists with location tracking. BLE
          pairing and hardware controls will be available when a real device is
          connected.
        </Txt>
      </Sheet>
    </>
  );
}
