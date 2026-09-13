import { Redirect } from "expo-router";
import { useApp } from "../store/AppStore";
export default function Index() {
  const { state } = useApp();
  return (
    <Redirect
      href={state.user ? "/home" : state.onboarding ? "/login" : "/onboarding"}
    />
  );
}
