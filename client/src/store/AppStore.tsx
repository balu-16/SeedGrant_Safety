import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {
  createContext,
  useContext,
  useEffect,
  useReducer,
  useRef,
  useState,
} from "react";
import { AppState } from "../types";
import { onSessionEvent } from "../services/api";
import { Action, initialState, parseStored, reducer } from "./reducer";
const KEY = "smart-safety:v1";
const Context = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
  storageError: string;
}>({ state: initialState, dispatch: () => {}, storageError: "" });
export function AppProvider({ children }: React.PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [storageError, setStorageError] = useState("");
  const queue = useRef(Promise.resolve());
  useEffect(() => {
    AsyncStorage.getItem(KEY)
      .then((raw) => dispatch({ type: "hydrate", payload: parseStored(raw) }))
      .catch(() => {
        setStorageError(
          "Storage unavailable. Changes will last for this session.",
        );
        dispatch({ type: "hydrate", payload: {} });
      });
  }, []);
  useEffect(() => {
    // A rejected background refresh cleared the tokens — drop the signed-in
    // UI state too, so navigation guards send the user back to login.
    return onSessionEvent((event) => {
      if (event === "lost") dispatch({ type: "logout" });
    });
  }, []);
  useEffect(() => {
    if (!state.hydrated) return;
    const payload = JSON.stringify({
      version: 1,
      onboarding: state.onboarding,
      user: state.user,
      guardians: state.guardians,
      preferences: state.preferences,
    });
    queue.current = queue.current
      .then(() => AsyncStorage.setItem(KEY, payload))
      .catch(() => setStorageError("Unable to save changes on this device."));
  }, [
    state.hydrated,
    state.onboarding,
    state.user,
    state.guardians,
    state.preferences,
  ]);
  return (
    <Context.Provider value={{ state, dispatch, storageError }}>
      {children}
    </Context.Provider>
  );
}
export const useApp = () => useContext(Context);
