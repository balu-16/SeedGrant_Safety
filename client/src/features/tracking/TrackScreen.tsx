import { useState } from "react";
import { Platform, Pressable, View } from "react-native";
import { router } from "expo-router";
import { Header } from "../../components/Header";
import {
  BadgeIcon,
  Button,
  Card,
  Icon,
  LinkText,
  Page,
  Row,
  Sheet,
  Toggle,
  Txt,
  s,
} from "../../components/ui";
import { C } from "../../constants/theme";
import { useTracking } from "../../hooks/useServices";
import { useLastFix } from "../../hooks/useLiveLocation";
import { useApp } from "../../store/AppStore";
import { OfflineMap } from "./OfflineMap";
import { LiveMap } from "./LiveMap";
import { isBackendMode } from "../../services";
import { formatCoord, formatRelative } from "../../services/location";
export default function TrackScreen() {
  const { state, dispatch } = useApp();
  const points = useTracking();
  const liveFix = useLastFix();
  const backend = isBackendMode(state.user?.id ?? null);
  const livePoint = points.find((p) => p.latitude !== undefined && p.longitude !== undefined);
  const currentCoord =
    liveFix != null
      ? formatCoord(liveFix.latitude, liveFix.longitude)
      : livePoint?.latitude !== undefined && livePoint?.longitude !== undefined
        ? formatCoord(livePoint.latitude, livePoint.longitude)
        : null;
  const currentStamp = liveFix?.recorded_at ?? livePoint?.recorded_at ?? null;
  const currentAccuracy = liveFix?.accuracy_m ?? livePoint?.accuracy_m ?? null;
  const currentDetail = currentCoord ?? "Bandra West, Mumbai";
  const currentSubtitle = currentStamp
    ? `Last updated: ${formatRelative(currentStamp)}${currentAccuracy ? ` · Accuracy: ${Math.round(currentAccuracy)} m` : ""}`
    : "Last updated: 2 min ago · Accuracy: 6 m";
  const [history, setHistory] = useState(false);
  const [dialog, setDialog] = useState("");
  return (
    <Page>
      <Header title="Track" subtitle="Live location & history" />
      <View
        style={{
          flexDirection: "row",
          backgroundColor: "#EAF0F9",
          borderRadius: 30,
          padding: 4,
        }}
      >
        {["Live", "History"].map((label, i) => (
          <Pressable
            key={label}
            accessibilityRole="tab"
            accessibilityLabel={label}
            accessibilityState={{ selected: history === !!i }}
            aria-selected={history === !!i}
            onPress={() => setHistory(!!i)}
            style={{
              flex: 1,
              borderRadius: 28,
              minHeight: 46,
              alignItems: "center",
              justifyContent: "center",
              flexDirection: "row",
              gap: 10,
              backgroundColor: history === !!i ? C.blue : "transparent",
            }}
          >
            <Icon
              name={i ? "time-outline" : "location"}
              color={history === !!i ? "white" : C.muted}
            />
            <Txt style={{ color: history === !!i ? "white" : C.muted }}>
              {label}
            </Txt>
          </Pressable>
        ))}
      </View>
      {!history && (
        <>
          {Platform.OS === "web" ? (
            <OfflineMap
              name={state.user?.name.split(" ")[0] ?? "Priya"}
              onDetails={() => setDialog("Current Location")}
            />
          ) : (
            <LiveMap
              name={state.user?.name.split(" ")[0] ?? "Priya"}
              fix={liveFix}
              trail={points}
              onDetails={() => setDialog("Current Location")}
            />
          )}
          <Row
            title="Current Location"
            detail={currentDetail}
            subtitle={currentSubtitle}
            icon="location"
            color={C.blue}
            onPress={() => setDialog("Current Location")}
          />
          <Row
            title="Live Sharing"
            detail={state.sharing ? "Active" : "Paused"}
            subtitle={`Sharing with ${state.sharing ? state.guardians.length : 0} guardians`}
            icon="people"
            color={C.green}
            onPress={() => setDialog("Live Sharing")}
          />
        </>
      )}
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Txt style={{ fontSize: 22, fontWeight: "700" }}>
          {history ? "Location History" : "Recent Movement"}
        </Txt>
        {!history && (
          <LinkText title="See All" onPress={() => setHistory(true)} />
        )}
      </View>
      <Card style={{ gap: 20 }}>
        {points.slice(0, history ? points.length : 3).map((point, index) => (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`View ${point.name}`}
            onPress={() => setDialog(point.name)}
            key={point.id}
            style={s.row}
          >
            <View style={{ alignItems: "center", width: 12 }}>
              <View
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 6,
                  backgroundColor: point.current ? C.blue : "#9AA8BB",
                }}
              />
              {index < (history ? points.length : 3) - 1 && (
                <View
                  style={{
                    position: "absolute",
                    top: 17,
                    width: 1,
                    height: 60,
                    backgroundColor: C.border,
                  }}
                />
              )}
            </View>
            <BadgeIcon
              name={index === 0 ? "home" : index === 2 ? "school" : "business"}
              color={point.current ? C.blue : "#78899B"}
            />
            <View style={{ flex: 1, gap: 3 }}>
              <Txt style={s.bold}>{point.name}</Txt>
              <Txt style={{ color: C.muted, fontSize: 13 }}>
                {point.address}
              </Txt>
              <Txt style={{ color: C.muted, fontSize: 12 }}>{point.time}</Txt>
            </View>
            {point.current && (
              <Txt
                style={{
                  color: C.green,
                  fontSize: 11,
                  backgroundColor: "#E6F8ED",
                  padding: 6,
                  borderRadius: 12,
                }}
              >
                Current
              </Txt>
            )}
          </Pressable>
        ))}
      </Card>
      <Txt style={{ color: C.muted, fontSize: 11, textAlign: "center" }}>
        {backend || liveFix
          ? "Live GPS · shared with guardians while sharing is on"
          : "Illustrative map · No real GPS data"}
      </Txt>
      <Sheet title={dialog} visible={!!dialog} onClose={() => setDialog("")}>
        {dialog === "Live Sharing" ? (
          <>
            <Toggle
              title="Share live location"
              value={state.sharing}
              onChange={(value) => dispatch({ type: "sharing", value })}
            />
            <Txt style={s.muted}>
              {state.sharing
                ? `${state.guardians.length} guardians can see your ${backend || liveFix ? "live" : "demo"} location.`
                : "Your location sharing is paused."}
            </Txt>
            <Button
              title="Manage guardians"
              onPress={() => {
                setDialog("");
                router.push("/guardians");
              }}
            />
          </>
        ) : (
          <>
            <Icon name="location" size={42} />
            <Txt style={s.bold}>
              {dialog === "Current Location"
                ? currentDetail
                : (points.find((p) => p.name === dialog)?.address ?? "Bandra West, Mumbai")}
            </Txt>
            <Txt style={s.muted}>
              {dialog === "Current Location"
                ? currentSubtitle
                : (points.find((p) => p.name === dialog)?.time ??
                  "Last updated: 2 min ago · Accuracy: 6 m")}
            </Txt>
            <Txt style={s.muted}>
              {backend || liveFix
                ? "Live phone-GPS fix. Guardians see this while sharing is on."
                : "This location is part of the offline demonstration."}
            </Txt>
          </>
        )}
      </Sheet>
    </Page>
  );
}
