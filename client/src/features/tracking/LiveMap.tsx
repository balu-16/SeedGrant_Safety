import { Platform, Pressable, View } from "react-native";
import { useEffect, useRef, useState } from "react";
import { C } from "../../constants/theme";
import { Icon, Txt } from "../../components/ui";
import type { LocationPoint, LiveFix } from "../../types";

type MapsModule = typeof import("react-native-maps");

let cachedMaps: MapsModule | null | undefined;

function loadMaps(): MapsModule | null {
  if (Platform.OS === "web") return null;
  if (cachedMaps !== undefined) return cachedMaps;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    cachedMaps = require("react-native-maps") as MapsModule;
  } catch {
    cachedMaps = null;
  }
  return cachedMaps;
}

/**
 * Real map (native only, OSM tiles — no API key).
 * Same frame + overlay chips as OfflineMap so the design is unchanged;
 * only the canvas switches from the SVG illustration to live tiles.
 * Web (or missing native module) renders nothing — TrackScreen shows OfflineMap there.
 */
export function LiveMap({
  name,
  fix,
  trail,
  onDetails,
}: {
  name: string;
  fix: LiveFix | null;
  trail: LocationPoint[];
  onDetails: () => void;
}) {
  const [centerTick, setCenterTick] = useState(0);
  const [centered, setCentered] = useState(false);
  const mapRef = useRef<{ animateToRegion: (r: object, d?: number) => void } | null>(null);

  const Maps = loadMaps();

  const coords = trail
    .filter((p) => p.latitude !== undefined && p.longitude !== undefined)
    .map((p) => ({ latitude: p.latitude as number, longitude: p.longitude as number }));

  const center = fix
    ? { latitude: fix.latitude, longitude: fix.longitude }
    : coords.length
      ? coords[0]
      : { latitude: 19.0596, longitude: 72.8295 }; // Bandra West fallback until first fix

  const region = {
    ...center,
    latitudeDelta: 0.012,
    longitudeDelta: 0.012,
  };

  useEffect(() => {
    if (centerTick > 0 && fix) {
      try {
        mapRef.current?.animateToRegion({ ...region }, 400);
      } catch {
        // ignore
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [centerTick]);

  if (!Maps) return null;
  const MapView = Maps.default;
  const { Marker, Polyline, UrlTile } = Maps;

  return (
    <View
      style={{
        height: 240,
        borderRadius: 18,
        overflow: "hidden",
        borderWidth: 2,
        borderColor: "white",
        backgroundColor: "#EDF0F3",
      }}
    >
      <MapView
        // @ts-expect-error ref type varies across map versions
        ref={mapRef}
        style={{ flex: 1 }}
        initialRegion={region}
        showsUserLocation
        showsMyLocationButton={false}
        toolbarEnabled={false}
        accessibilityLabel="Live map showing your current location"
      >
        <UrlTile
          urlTemplate="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          maximumZ={19}
          tileSize={256}
        />
        {coords.length > 1 && (
          <Polyline coordinates={coords} strokeColor="#2D87FF" strokeWidth={4} lineDashPattern={[5, 6]} />
        )}
        {fix && (
          <Marker coordinate={{ latitude: fix.latitude, longitude: fix.longitude }} title={name}>
            <View
              style={{
                width: 20,
                height: 20,
                borderRadius: 10,
                backgroundColor: "#0875FF",
                borderWidth: 3,
                borderColor: "white",
              }}
            />
          </Marker>
        )}
      </MapView>
      <View
        style={{
          position: "absolute",
          top: 10,
          left: 10,
          flexDirection: "row",
          gap: 8,
          alignItems: "center",
          backgroundColor: "#EEFFF2",
          padding: 10,
          borderRadius: 13,
        }}
      >
        <Icon name="wifi" color={C.green} size={22} />
        <Txt style={{ fontSize: 12, lineHeight: 17, color: C.green }}>
          {"Smartphone-assisted\ntracking"}
        </Txt>
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Show current location"
        onPress={onDetails}
        style={{
          position: "absolute",
          top: 75,
          left: "56%",
          backgroundColor: "white",
          padding: 10,
          borderRadius: 13,
          boxShadow: "0px 3px 12px #25375220",
        }}
      >
        <Txt style={{ fontSize: 13, fontWeight: "600" }}>{name}</Txt>
        <Txt style={{ color: C.blue, fontSize: 12, marginTop: 3 }}>Live now ›</Txt>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Recenter map"
        onPress={() => {
          setCentered(true);
          setCenterTick((t) => t + 1);
        }}
        style={{
          position: "absolute",
          bottom: 10,
          right: 10,
          backgroundColor: "white",
          padding: 11,
          borderRadius: 30,
        }}
      >
        <Icon name="locate-outline" />
      </Pressable>
      {centered && fix && (
        <View
          style={{
            position: "absolute",
            bottom: 12,
            left: 12,
            backgroundColor: "#FFFFFFED",
            padding: 6,
            borderRadius: 6,
          }}
        >
          <Txt accessibilityLiveRegion="polite" style={{ fontSize: 11, color: C.muted }}>
            Map centered on your live location
          </Txt>
        </View>
      )}
      {!fix && (
        <View
          style={{
            position: "absolute",
            bottom: 12,
            left: 12,
            backgroundColor: "#FFFFFFED",
            padding: 6,
            borderRadius: 6,
          }}
        >
          <Txt accessibilityLiveRegion="polite" style={{ fontSize: 11, color: C.muted }}>
            Waiting for GPS…
          </Txt>
        </View>
      )}
    </View>
  );
}
