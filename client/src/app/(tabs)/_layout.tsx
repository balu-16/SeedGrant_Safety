import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Tabs } from "expo-router";
import { Icon, IconName } from "../../components/ui";
import { C } from "../../constants/theme";
const tabs: { name: string; title: string; icon: IconName }[] = [
  { name: "home", title: "Home", icon: "home" },
  { name: "track", title: "Track", icon: "location" },
  { name: "guardians", title: "Guardians", icon: "people" },
  { name: "profile", title: "Profile", icon: "person" },
];
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: C.blue,
        tabBarInactiveTintColor: "#758194",
        tabBarStyle: {
          backgroundColor: "white",
          borderTopWidth: 0,
          height: 70 + insets.bottom,
          paddingTop: 9,
          paddingBottom: Math.max(9, insets.bottom),
        },
        tabBarLabelStyle: { fontSize: 12, marginTop: 4 },
      }}
    >
      {tabs.map((t) => (
        <Tabs.Screen
          key={t.name}
          name={t.name}
          options={{
            title: t.title,
            tabBarAccessibilityLabel: t.title,
            tabBarIcon: ({ color }) => (
              <Icon name={t.icon} color={color} size={26} />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}
