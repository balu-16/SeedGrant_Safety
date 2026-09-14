import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { ActivityIndicator, View } from "react-native";
import { AppProvider, useApp } from "../store/AppStore";
import { useNotifications } from "../hooks/useNotifications";
import { useGuardiansSync, useRealtime } from "../hooks/useServices";
import { useLiveLocation } from "../hooks/useLiveLocation";
import { registerBackgroundLocationTask } from "../tasks/locationTask";
import { useSessionRestore } from "../hooks/useSessionRestore";
import { C } from "../constants/theme";
registerBackgroundLocationTask();
function Routes() {
  const { state } = useApp();
  useNotifications();
  useGuardiansSync();
  useRealtime();
  useLiveLocation();
  useSessionRestore();
  if (!state.hydrated)
    return (
      <View
        style={{ flex: 1, backgroundColor: C.bg, justifyContent: "center" }}
      >
        <ActivityIndicator
          color={C.blue}
          accessibilityLabel="Loading your safety app"
        />
      </View>
    );
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: C.bg },
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Protected guard={!state.user}>
          <Stack.Screen name="onboarding" />
          <Stack.Screen name="login" />
          <Stack.Screen name="signup" />
        </Stack.Protected>
        <Stack.Protected guard={!!state.user}>
          <Stack.Screen name="(tabs)" />
        </Stack.Protected>
      </Stack>
    </>
  );
}
export default function Root() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <Routes />
      </AppProvider>
    </SafeAreaProvider>
  );
}
