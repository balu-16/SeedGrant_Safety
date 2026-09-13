import React, { useState } from "react";
import {
  ActivityIndicator,
  ColorValue,
  Image,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TextInputProps,
  TextProps,
  View,
  ViewProps,
} from "react-native";
import Ionicons from "@expo/vector-icons/Ionicons";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import Svg, { Path } from "react-native-svg";
import { C, illustrations } from "../constants/theme";
import { useApp } from "../store/AppStore";
export type IconName = React.ComponentProps<typeof Ionicons>["name"];
export function Txt({ style, ...props }: TextProps) {
  const { state } = useApp();
  const flat = StyleSheet.flatten(style);
  return (
    <Text
      {...props}
      style={[
        { color: C.ink, fontSize: 16 },
        style,
        state.preferences.largeText && {
          fontSize: (flat?.fontSize ?? 16) * 1.15,
          ...(flat?.lineHeight ? { lineHeight: flat.lineHeight * 1.15 } : {}),
        },
      ]}
    />
  );
}
export function Icon({
  name,
  size = 24,
  color = C.blue,
}: {
  name: IconName;
  size?: number;
  color?: ColorValue;
}) {
  return (
    <Ionicons
      accessible={false}
      aria-hidden={true}
      name={name}
      size={size}
      color={color}
    />
  );
}
export function Button({
  title,
  onPress,
  secondary = false,
  danger = false,
  loading = false,
  icon,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  danger?: boolean;
  loading?: boolean;
  icon?: IconName;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => ({ opacity: pressed || disabled ? 0.65 : 1 })}
    >
      <LinearGradient
        colors={
          secondary
            ? [C.white, C.white]
            : danger
              ? ["#F66B54", "#D93328"]
              : ["#2387FF", "#066BFF"]
        }
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[
          s.button,
          secondary && { borderWidth: 1, borderColor: C.border },
        ]}
      >
        {loading ? (
          <ActivityIndicator color={secondary ? C.blue : "white"} />
        ) : (
          <>
            <Txt
              style={{
                color: secondary ? C.blue : "white",
                fontSize: 18,
                fontWeight: "600",
              }}
            >
              {title}
            </Txt>
            {!!icon && (
              <Icon name={icon} color={secondary ? C.blue : "white"} />
            )}
          </>
        )}
      </LinearGradient>
    </Pressable>
  );
}
export function LinkText({
  title,
  onPress,
}: {
  title: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      onPress={onPress}
      style={{ minHeight: 44, justifyContent: "center" }}
    >
      <Txt style={{ color: C.blue }}>{title}</Txt>
    </Pressable>
  );
}
export function Card({
  children,
  style,
  onPress,
  label,
}: ViewProps & { onPress?: () => void; label?: string }) {
  return onPress ? (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [s.card, style, { opacity: pressed ? 0.8 : 1 }]}
    >
      {children}
    </Pressable>
  ) : (
    <View style={[s.card, style]}>{children}</View>
  );
}
export function BadgeIcon({
  name,
  color = C.blue,
  bg = C.pale,
}: {
  name: IconName;
  color?: string;
  bg?: string;
}) {
  return (
    <View style={[s.badgeIcon, { backgroundColor: bg }]}>
      <Icon name={name} size={29} color={color} />
    </View>
  );
}
export function Row({
  title,
  subtitle,
  icon,
  onPress,
  color,
  detail,
}: {
  title: string;
  subtitle?: string;
  icon: IconName;
  onPress?: () => void;
  color?: string;
  detail?: string;
}) {
  return (
    <Card onPress={onPress} label={title} style={s.row}>
      <BadgeIcon name={icon} color={color} />
      <View style={{ flex: 1, gap: 5 }}>
        <Txt style={s.bold}>{title}</Txt>
        {!!detail && (
          <Txt
            style={{ color: color ?? C.green, fontSize: 19, fontWeight: "600" }}
          >
            {detail}
          </Txt>
        )}
        {!!subtitle && <Txt style={s.muted}>{subtitle}</Txt>}
      </View>
      {onPress && <Icon name="chevron-forward" color={C.muted} size={19} />}
    </Card>
  );
}
export function Waves() {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Svg
        width="100%"
        height="100%"
        viewBox="0 0 400 250"
        preserveAspectRatio="none"
      >
        <Path d="M0 55 Q75 0 160 65 T300 70 T400 60 V250 H0Z" fill="#EAF3FF" />
        <Path
          d="M0 135 Q75 80 160 135 T300 130 T400 110 V170 Q290 235 200 180 T0 200Z"
          fill="#D8EAFE"
        />
      </Svg>
    </View>
  );
}
export function Brand() {
  return (
    <View style={s.brand}>
      <View>
        <Icon name="shield" size={49} />
        <View style={{ position: "absolute", top: 13, left: 12 }}>
          <Icon name="heart" size={25} color="white" />
        </View>
      </View>
      <View style={{ flexShrink: 1 }}>
        <Txt style={{ fontSize: 24, fontWeight: "700", letterSpacing: -0.8 }}>
          Smart{" "}
          <Txt style={{ color: C.blue, fontSize: 24, fontWeight: "700" }}>
            Safety Tag
          </Txt>
        </Txt>
        <Txt style={{ color: C.muted, fontSize: 12, marginTop: 4 }}>
          People you care about, always closer
        </Txt>
      </View>
    </View>
  );
}
export function Hero({
  index = 0,
  height,
}: {
  index?: number;
  height: number;
}) {
  return (
    <View style={{ height, width: "100%", overflow: "hidden" }}>
      <Image
        source={illustrations[index]}
        accessibilityLabel={`Safety illustration ${index + 1}: girl with open eyes and plain backpack`}
        style={{ width: "100%", height: "100%" }}
        resizeMode="cover"
      />
      <Svg
        pointerEvents="none"
        height={55}
        width="100%"
        viewBox="0 0 400 55"
        preserveAspectRatio="none"
        style={{ position: "absolute", bottom: -1 }}
      >
        <Path d="M0 0 Q200 106 400 0 V55 H0Z" fill={C.bg} />
      </Svg>
    </View>
  );
}
export function Field({
  icon,
  error,
  password,
  ...props
}: TextInputProps & { icon: IconName; error?: string; password?: boolean }) {
  const [visible, setVisible] = useState(false);
  return (
    <View style={{ gap: 4 }}>
      <View style={[s.field, error && { borderColor: C.red }]}>
        <Icon name={icon} color={C.muted} size={22} />
        <TextInput
          {...props}
          accessibilityLabel={props.accessibilityLabel ?? props.placeholder}
          placeholderTextColor="#8391AA"
          secureTextEntry={password && !visible}
          autoCapitalize={props.autoCapitalize ?? "none"}
          style={{
            flex: 1,
            minWidth: 0,
            color: C.ink,
            fontSize: 16,
            paddingVertical: 15,
          }}
        />
        {password && (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`${visible ? "Hide" : "Show"} ${props.placeholder?.toLowerCase()}`}
            onPress={() => setVisible(!visible)}
            style={{ padding: 7 }}
          >
            <Icon
              name={visible ? "eye-outline" : "eye-off-outline"}
              color={C.muted}
              size={22}
            />
          </Pressable>
        )}
      </View>
      {!!error && (
        <Txt accessibilityRole="alert" style={s.error}>
          {error}
        </Txt>
      )}
    </View>
  );
}
export function Sheet({
  title,
  visible,
  onClose,
  children,
}: React.PropsWithChildren<{
  title: string;
  visible: boolean;
  onClose: () => void;
}>) {
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={s.scrim}
      >
        <View style={s.sheet}>
          <View style={[s.row, { marginBottom: 16 }]}>
            <Txt style={[s.heading, { flex: 1 }]}>{title}</Txt>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close dialog"
              onPress={onClose}
              style={{ padding: 10 }}
            >
              <Icon name="close" color={C.muted} />
            </Pressable>
          </View>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={{ gap: 16, paddingBottom: 24 }}
          >
            {children}
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}
export function Toggle({
  title,
  value,
  onChange,
  subtitle,
}: {
  title: string;
  value: boolean;
  onChange: (value: boolean) => void;
  subtitle?: string;
}) {
  return (
    <View style={[s.row, { paddingVertical: 10 }]}>
      <View style={{ flex: 1 }}>
        <Txt style={s.bold}>{title}</Txt>
        {!!subtitle && <Txt style={s.muted}>{subtitle}</Txt>}
      </View>
      <Switch
        accessibilityLabel={title}
        value={value}
        onValueChange={onChange}
        trackColor={{ true: C.blue, false: "#CCD6E5" }}
      />
    </View>
  );
}
export function Avatar({
  name,
  size = 43,
  photo = false,
}: {
  name: string;
  size?: number;
  photo?: boolean;
}) {
  if (photo)
    return (
      <Image
        source={require("../../assets/avatars/demo-profile.png")}
        accessibilityLabel={`${name} profile photo`}
        style={{ width: size, height: size, borderRadius: size / 2 }}
      />
    );
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: "#DCEAFF",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Txt style={{ color: "#2864AB", fontWeight: "700", fontSize: size / 3 }}>
        {name
          .split(" ")
          .map((x) => x[0])
          .slice(0, 2)
          .join("")}
      </Txt>
    </View>
  );
}
export function Page({ children }: React.PropsWithChildren) {
  const { storageError } = useApp();
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={s.page}>
      <ScrollView
        contentContainerStyle={s.content}
        keyboardShouldPersistTaps="handled"
      >
        {!!storageError && <Txt style={s.error}>{storageError}</Txt>}
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}
export const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: C.bg },
  content: {
    padding: 18,
    paddingBottom: 28,
    gap: 14,
    width: "100%",
    maxWidth: 600,
    alignSelf: "center",
  },
  heading: { fontSize: 25, fontWeight: "700", letterSpacing: -0.6 },
  bold: { fontSize: 16, fontWeight: "600" },
  muted: { color: C.muted, fontSize: 14, lineHeight: 21 },
  error: { color: C.red, fontSize: 13 },
  row: { flexDirection: "row", alignItems: "center", gap: 13 },
  card: {
    backgroundColor: "white",
    borderRadius: 18,
    padding: 17,
    boxShadow: "0px 3px 15px rgba(36, 62, 100, 0.065)",
  },
  badgeIcon: {
    width: 51,
    height: 51,
    borderRadius: 25,
    alignItems: "center",
    justifyContent: "center",
  },
  button: {
    minHeight: 52,
    borderRadius: 30,
    paddingHorizontal: 22,
    paddingVertical: 13,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  field: {
    backgroundColor: "#FFFFFFBA",
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 13,
    minHeight: 51,
  },
  brand: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 11,
    paddingHorizontal: 22,
    paddingVertical: 20,
  },
  scrim: {
    flex: 1,
    backgroundColor: "#08163866",
    justifyContent: "flex-end",
    alignItems: "center",
  },
  sheet: {
    backgroundColor: C.bg,
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    padding: 22,
    maxHeight: "88%",
    width: "100%",
    maxWidth: 600,
  },
});
