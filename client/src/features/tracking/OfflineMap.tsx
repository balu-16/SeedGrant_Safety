import { useState } from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle, Path, Rect, Text as SvgText } from "react-native-svg";
import { C } from "../../constants/theme";
import { Icon, Txt } from "../../components/ui";
export function OfflineMap({
  name,
  onDetails,
}: {
  name: string;
  onDetails: () => void;
}) {
  const [centered, setCentered] = useState(false);
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
      <Svg
        width="100%"
        height="100%"
        viewBox="0 0 400 260"
        preserveAspectRatio="xMidYMid slice"
        accessibilityLabel="Demo map of Bandra West showing a blue location trail"
      >
        <Rect width="400" height="260" fill="#EBEFF3" />
        <Path d="M0 0H70Q40 80 65 140T100 260H0Z" fill="#A8D9FA" />
        <Path
          d="M70 0H99Q65 100 83 146T126 260H100Q58 199 65 140T70 0"
          fill="#CDE8D9"
        />
        <Path
          d="M267 121L343 152L307 244L241 222Z M112 0H175L150 74L106 54Z M349 0H400V51L331 33Z"
          fill="#CDE7D8"
        />
        {[100, 145, 190, 235, 280, 325, 370, 415].map((x) => (
          <Path
            key={x}
            d={`M${x} -20 L${x - 100} 280`}
            stroke="white"
            strokeWidth="7"
          />
        ))}
        {[0, 50, 100, 150, 200].map((y) => (
          <Path
            key={y}
            d={`M75 ${y} L420 ${y + 135}`}
            stroke="white"
            strokeWidth="8"
          />
        ))}
        <Path
          d="M120 236 L164 204 L206 204 L237 146"
          stroke="#2D87FF"
          strokeWidth="4"
          strokeDasharray="5 6"
          fill="none"
          strokeLinecap="round"
        />
        <Circle
          cx="237"
          cy="146"
          r={centered ? 29 : 23}
          fill="#187BFF"
          opacity=".14"
        />
        <Circle
          cx="237"
          cy="146"
          r="10"
          fill="#0875FF"
          stroke="white"
          strokeWidth="3"
        />
        <SvgText x="98" y="142" fontSize="13" fill="#516580" fontWeight="600">
          Bandra West
        </SvgText>
        <SvgText x="24" y="225" fontSize="11" fill="#536B81">
          Bandra
        </SvgText>
        <SvgText x="20" y="240" fontSize="11" fill="#536B81">
          Sea Face
        </SvgText>
        <SvgText x="288" y="214" fontSize="11" fill="#536B81">
          Pali Hill
        </SvgText>
        <SvgText x="282" y="58" fontSize="11" fill="#536B81">
          Linking Road
        </SvgText>
        <Path d="M310 179l-7 12h14Z M310 184l-9 13h18Z" fill="#78B38C" />
        <Path d="M310 195v7" stroke="#78B38C" strokeWidth="3" />
      </Svg>
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
          Smartphone-assisted{"\n"}tracking
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
        <Txt style={{ color: C.blue, fontSize: 12, marginTop: 3 }}>
          Live now ›
        </Txt>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Recenter map"
        onPress={() => setCentered(true)}
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
      {centered && (
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
          <Txt
            accessibilityLiveRegion="polite"
            style={{ fontSize: 11, color: C.muted }}
          >
            Map centered on your demo location
          </Txt>
        </View>
      )}
    </View>
  );
}
