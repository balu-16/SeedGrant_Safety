import { useRef, useState } from "react";
import { Image, Pressable, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { Header } from "../../components/Header";
import { DeviceCard } from "../../components/DeviceCard";
import {
  Button,
  Card,
  Icon,
  IconName,
  LinkText,
  Page,
  Row,
  Sheet,
  Toggle,
  Txt,
  s,
} from "../../components/ui";
import { C, illustrations } from "../../constants/theme";
import { useApp } from "../../store/AppStore";
import { useEmergency } from "../../hooks/useServices";
const actions: { title: string; icon: IconName; color: string; bg: string }[] =
  [
    {
      title: "Alert Contacts",
      icon: "people",
      color: "#D93749",
      bg: "#FCE8EC",
    },
    { title: "Voice Help", icon: "mic", color: C.blue, bg: "#E6EFFF" },
    {
      title: "Recent Alerts",
      icon: "time-outline",
      color: "#8A5025",
      bg: "#FAF0E3",
    },
    {
      title: "Emergency Services",
      icon: "call",
      color: "#7446CB",
      bg: "#EDE8FC",
    },
  ];
export default function HomeScreen() {
  const { state, dispatch } = useApp();
  const { pending, trigger } = useEmergency();
  const [dialog, setDialog] = useState("");
  const [success, setSuccess] = useState(false);
  const [holding, setHolding] = useState(false);
  const longPressed = useRef(false);
  function openSOS() {
    setSuccess(false);
    setDialog("Send an SOS alert?");
  }
  return (
    <Page>
      <Header
        title={`Hi, ${state.user?.name.split(" ")[0] ?? "Priya"}`}
        subtitle="Stay safe, always ☀"
      />
      <View style={{ alignItems: "center", paddingVertical: 5 }}>
        <View
          style={{ backgroundColor: "#FDEEEF", padding: 12, borderRadius: 150 }}
        >
          <View
            style={{
              backgroundColor: "#F9DCDD",
              padding: 10,
              borderRadius: 130,
            }}
          >
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="SOS — tap or hold for 3 seconds"
              onPressIn={() => {
                longPressed.current = false;
                setHolding(true);
              }}
              onPressOut={() => setHolding(false)}
              delayLongPress={3000}
              onLongPress={() => {
                longPressed.current = true;
                openSOS();
              }}
              onPress={() => {
                if (!longPressed.current) openSOS();
              }}
            >
              <LinearGradient
                colors={["#FF735D", "#D52C20"]}
                style={{
                  width: 158,
                  height: 158,
                  borderRadius: 100,
                  alignItems: "center",
                  justifyContent: "center",
                  borderWidth: 5,
                  borderColor: "#F68171",
                  gap: 4,
                }}
              >
                <Icon name="call" size={34} color="white" />
                <Txt
                  style={{ color: "white", fontSize: 33, fontWeight: "700" }}
                >
                  SOS
                </Txt>
                <Txt
                  style={{
                    color: "white",
                    fontSize: 13,
                    textAlign: "center",
                    lineHeight: 19,
                  }}
                >
                  {holding ? "Keep holding…" : "Tap and hold\nfor 3 seconds"}
                </Txt>
              </LinearGradient>
            </Pressable>
          </View>
        </View>
        <Txt style={{ marginTop: 9, fontSize: 14, fontWeight: "600" }}>
          You’re not alone. Help is always within reach.
        </Txt>
      </View>
      <Row
        title="Safety Status"
        detail={state.alerts.length ? "Demo alert recorded" : "All Good"}
        subtitle={
          state.alerts.length
            ? "Your SOS simulation is complete"
            : "No active alerts"
        }
        icon="shield-checkmark"
        color={C.green}
        onPress={() => setDialog("Safety Status")}
      />
      <View style={[s.row, { gap: 10, alignItems: "stretch" }]}>
        <Card
          label="Current Location"
          onPress={() => router.push("/track")}
          style={{ flex: 1, gap: 7, padding: 14 }}
        >
          <Icon name="location" />
          <Txt style={{ fontSize: 13, fontWeight: "600" }}>
            Current Location
          </Txt>
          <Txt style={{ fontSize: 13 }}>Bandra West, Mumbai</Txt>
          <Txt style={{ fontSize: 12, color: C.muted }}>Accuracy · 6 m</Txt>
        </Card>
        <Card
          label="Live Tracking"
          onPress={() => router.push("/track")}
          style={{ flex: 1, gap: 7, padding: 14 }}
        >
          <Icon name="map" />
          <Txt style={{ fontSize: 13, fontWeight: "600" }}>Live Tracking</Txt>
          <Txt style={{ fontSize: 13 }}>
            Sharing with {state.sharing ? state.guardians.length : 0} contacts
          </Txt>
          <Txt style={{ fontSize: 12, color: C.green }}>
            {state.sharing ? "● Active now" : "Sharing paused"}
          </Txt>
        </Card>
      </View>
      <DeviceCard />
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Txt style={{ fontSize: 21, fontWeight: "700" }}>Quick Actions</Txt>
        <LinkText title="See All" onPress={() => setDialog("Quick Actions")} />
      </View>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {actions.map((a) => (
          <Pressable
            key={a.title}
            accessibilityRole="button"
            accessibilityLabel={a.title}
            onPress={() =>
              a.title === "Alert Contacts"
                ? router.push("/guardians")
                : setDialog(a.title)
            }
            style={{
              flex: 1,
              backgroundColor: a.bg,
              borderRadius: 15,
              alignItems: "center",
              paddingHorizontal: 5,
              paddingVertical: 17,
              gap: 10,
            }}
          >
            <Icon name={a.icon} color={a.color} size={27} />
            <Txt
              style={{
                textAlign: "center",
                fontSize: 12,
                fontWeight: "600",
                lineHeight: 17,
              }}
            >
              {a.title}
            </Txt>
          </Pressable>
        ))}
      </View>
      <Card
        label="Safety Tips"
        onPress={() => setDialog("Safety Tips")}
        style={{
          flexDirection: "row",
          alignItems: "center",
          padding: 0,
          overflow: "hidden",
          backgroundColor: "#E2F0EA",
        }}
      >
        <Image source={illustrations[0]} style={{ width: 100, height: 95 }} />
        <View style={{ flex: 1, padding: 14, gap: 5 }}>
          <Txt style={{ fontSize: 19, fontWeight: "700" }}>Safety Tips</Txt>
          <Txt style={s.muted}>Simple steps for a safer you</Txt>
        </View>
      </Card>
      <Txt style={{ color: C.muted, fontSize: 11, textAlign: "center" }}>
        Demo mode · Alerts and location are simulated
      </Txt>
      <Sheet
        title={success ? "Demo alert complete" : dialog}
        visible={!!dialog}
        onClose={() => {
          if (!pending) setDialog("");
        }}
      >
        {dialog === "Send an SOS alert?" ? (
          success ? (
            <>
              <Icon name="checkmark-circle" color={C.green} size={46} />
              <Txt>
                Your demo SOS was recorded for {state.guardians.length}{" "}
                guardians.
              </Txt>
              <Txt style={s.muted}>No real messages or calls were sent.</Txt>
              <Button title="Done" onPress={() => setDialog("")} />
            </>
          ) : (
            <>
              <Txt>
                This will simulate an emergency alert to{" "}
                {state.guardians.length} trusted guardians.
              </Txt>
              {state.guardians.length === 0 && (
                <Txt style={s.muted}>
                  Your safety circle is empty. You can still try the simulation.
                </Txt>
              )}
              <Button
                title="Send demo SOS"
                danger
                loading={pending}
                onPress={async () => {
                  const result = await trigger();
                  if (result) setSuccess(true);
                }}
              />
              <Button
                title="Cancel"
                secondary
                disabled={pending}
                onPress={() => setDialog("")}
              />
            </>
          )
        ) : dialog === "Recent Alerts" || dialog === "Safety Status" ? (
          <>
            {!state.alerts.length ? (
              <Txt>No alerts. You’re all good.</Txt>
            ) : (
              state.alerts.map((a) => (
                <Card key={a.id}>
                  <Txt style={s.bold}>SOS simulation completed</Txt>
                  <Txt style={s.muted}>
                    {new Date(a.createdAt).toLocaleString()} · {a.recipients}{" "}
                    guardians
                  </Txt>
                </Card>
              ))
            )}
          </>
        ) : dialog === "Voice Help" ? (
          <>
            <Txt style={s.muted}>
              Try the voice assistance demo. Microphone access is not required.
            </Txt>
            <Toggle
              title="Voice help"
              value={state.preferences.voice}
              onChange={(value) =>
                dispatch({ type: "preferences", value: { voice: value } })
              }
            />
            <Button title="Simulate “Hey SafeMe”" onPress={openSOS} />
          </>
        ) : dialog === "Emergency Services" ? (
          <>
            <Txt>Emergency assistance demo</Txt>
            <Txt style={s.muted}>
              This prototype does not place calls. Use your phone’s emergency
              dialer when you need real assistance.
            </Txt>
            <Button title="Try emergency alert" onPress={openSOS} />
          </>
        ) : dialog === "Quick Actions" ? (
          <>
            {actions.map((a) => (
              <Row
                key={a.title}
                title={a.title}
                icon={a.icon}
                onPress={() => {
                  if (a.title === "Alert Contacts") {
                    setDialog("");
                    router.push("/guardians");
                  } else setDialog(a.title);
                }}
              />
            ))}
          </>
        ) : (
          <>
            <Txt>Keep your phone charged before heading out.</Txt>
            <Txt>Share your plans with someone you trust.</Txt>
            <Txt>Check your safety circle and device connection regularly.</Txt>
          </>
        )}
      </Sheet>
    </Page>
  );
}
