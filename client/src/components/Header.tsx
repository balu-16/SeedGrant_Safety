import { useState } from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { useApp } from "../store/AppStore";
import { Avatar, Icon, Sheet, Txt, s } from "./ui";
export function Header({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  const { state } = useApp();
  const [open, setOpen] = useState(false);
  return (
    <>
      <View style={[s.row, { paddingVertical: 10 }]}>
        <View style={{ flex: 1 }}>
          <Txt style={s.heading}>{title}</Txt>
          <Txt style={[s.muted, { marginTop: 4 }]}>{subtitle}</Txt>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Notifications"
          onPress={() => setOpen(true)}
          style={{ padding: 8 }}
        >
          <Icon name="notifications-outline" color="#11213D" size={27} />
          <View
            style={{
              position: "absolute",
              top: 7,
              right: 9,
              width: 8,
              height: 8,
              borderRadius: 5,
              backgroundColor: "#F04444",
            }}
          />
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open profile"
          onPress={() => router.push("/profile")}
        >
          <Avatar photo name={state.user?.name ?? "Priya Sharma"} />
        </Pressable>
      </View>
      <Sheet
        title="Notifications"
        visible={open}
        onClose={() => setOpen(false)}
      >
        <Txt>Your safety tag is connected.</Txt>
        <Txt style={s.muted}>
          You have {state.guardians.length} trusted guardians in your safety
          circle.
        </Txt>
        {state.alerts.map((a) => (
          <Txt key={a.id}>
            Demo SOS recorded · {new Date(a.createdAt).toLocaleTimeString()}
          </Txt>
        ))}
      </Sheet>
    </>
  );
}
