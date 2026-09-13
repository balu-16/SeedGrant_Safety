import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  View,
  useWindowDimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import {
  Brand,
  Button,
  Field,
  Hero,
  Icon,
  LinkText,
  Sheet,
  Txt,
  Waves,
  s,
} from "../../components/ui";
import { C } from "../../constants/theme";
import { useAuth } from "../../hooks/useServices";
import {
  validateLogin,
  validateSignup,
  validEmail,
} from "../../utils/validation";
export default function AuthScreen({ signup = false }: { signup?: boolean }) {
  const auth = useAuth();
  const { width, height } = useWindowDimensions();
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
    terms: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(false);
  const [dialog, setDialog] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetSent, setResetSent] = useState(false);
  const [resetError, setResetError] = useState("");
  const change = (key: keyof typeof form, value: string | boolean) => {
    setForm({ ...form, [key]: value });
    setErrors({ ...errors, [key]: "" });
  };
  async function submit(google = false) {
    if (pending) return;
    const result = google
      ? {}
      : signup
        ? validateSignup(form)
        : validateLogin(form.email, form.password);
    setErrors(result);
    if (Object.keys(result).length) return;
    setPending(true);
    try {
      if (google) await auth.google();
      else if (signup) await auth.signup(form);
      else await auth.login(form.email, form.password);
      router.replace("/home");
    } catch {
      setErrors({ general: "Unable to sign in. Please try again." });
    } finally {
      setPending(false);
    }
  }
  const heroHeight = Math.min(
    Math.min(width, 600) * (signup ? 0.5 : 0.6),
    height * (signup ? 0.25 : 0.29),
  );
  return (
    <SafeAreaView style={s.page}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{
            width: "100%",
            maxWidth: 600,
            alignSelf: "center",
            paddingBottom: 20,
            flexGrow: 1,
          }}
        >
          <View style={{ paddingTop: 8 }}>
            <Brand />
          </View>
          <Hero height={heroHeight} />
          <View style={{ paddingHorizontal: 23, gap: 12 }}>
            <Txt
              accessibilityRole="header"
              style={{
                fontSize: 31,
                fontWeight: "700",
                textAlign: "center",
                letterSpacing: -0.7,
              }}
            >
              {signup ? "Create Account" : "Welcome Back"}
            </Txt>
            <Txt
              style={{
                color: C.muted,
                textAlign: "center",
                fontSize: 16,
                lineHeight: 23,
                marginBottom: 9,
              }}
            >
              {signup
                ? "Join Smart Safety Tag and take a step\ntoward a safer tomorrow."
                : "Sign in to continue to a safer you."}
            </Txt>
            {signup && (
              <Field
                placeholder="Full name"
                icon="person-outline"
                value={form.name}
                onChangeText={(v) => change("name", v)}
                error={errors.name}
                autoCapitalize="words"
                autoComplete="name"
              />
            )}
            <Field
              placeholder="Email address"
              icon="mail-outline"
              value={form.email}
              onChangeText={(v) => change("email", v)}
              error={errors.email}
              keyboardType="email-address"
              autoComplete="email"
            />
            {signup && (
              <Field
                placeholder="Phone number (+91)"
                icon="call-outline"
                value={form.phone}
                onChangeText={(v) => change("phone", v)}
                error={errors.phone}
                keyboardType="phone-pad"
                autoComplete="tel"
              />
            )}
            <Field
              placeholder="Password"
              icon="lock-closed-outline"
              password
              value={form.password}
              onChangeText={(v) => change("password", v)}
              error={errors.password}
              autoComplete={signup ? "new-password" : "current-password"}
            />
            {signup && (
              <Field
                placeholder="Confirm password"
                icon="lock-closed-outline"
                password
                value={form.confirm}
                onChangeText={(v) => change("confirm", v)}
                error={errors.confirm}
              />
            )}
            {signup ? (
              <>
                <View style={[s.row, { gap: 7, alignItems: "flex-start" }]}>
                  <Pressable
                    accessibilityRole="checkbox"
                    accessibilityLabel="Accept terms"
                    accessibilityState={{ checked: form.terms }}
                    aria-checked={form.terms}
                    onPress={() => change("terms", !form.terms)}
                    style={{ padding: 8 }}
                  >
                    <Icon
                      name={form.terms ? "checkbox" : "square-outline"}
                      color={form.terms ? C.blue : C.muted}
                    />
                  </Pressable>
                  <Txt
                    style={{
                      flex: 1,
                      fontSize: 13,
                      lineHeight: 23,
                      marginTop: 5,
                    }}
                  >
                    I agree to the{" "}
                    <Txt
                      accessibilityRole="link"
                      onPress={() => setDialog("Terms of Service")}
                      style={{ color: C.blue, fontSize: 13 }}
                    >
                      Terms of Service
                    </Txt>{" "}
                    and{" "}
                    <Txt
                      accessibilityRole="link"
                      onPress={() => setDialog("Privacy Policy")}
                      style={{ color: C.blue, fontSize: 13 }}
                    >
                      Privacy Policy
                    </Txt>
                  </Txt>
                </View>
                {!!errors.terms && <Txt style={s.error}>{errors.terms}</Txt>}
              </>
            ) : (
              <View
                style={{
                  alignItems: "flex-end",
                  marginTop: -8,
                  marginBottom: -5,
                }}
              >
                <LinkText
                  title="Forgot password?"
                  onPress={() => {
                    setDialog("Reset password");
                    setResetEmail(form.email);
                    setResetSent(false);
                    setResetError("");
                  }}
                />
              </View>
            )}
            {!!errors.general && <Txt style={s.error}>{errors.general}</Txt>}
            <Button
              title={signup ? "Create Account" : "Sign In"}
              icon="chevron-forward"
              onPress={() => submit()}
              loading={pending}
            />
            {!signup && (
              <>
                <View style={[s.row, { marginVertical: 5 }]}>
                  <View
                    style={{ flex: 1, height: 1, backgroundColor: C.border }}
                  />
                  <Txt style={s.muted}>Or continue with</Txt>
                  <View
                    style={{ flex: 1, height: 1, backgroundColor: C.border }}
                  />
                </View>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Sign in with Google"
                  disabled={pending}
                  onPress={() => submit(true)}
                  style={[
                    s.button,
                    {
                      backgroundColor: "white",
                      borderColor: "#D2E0F5",
                      borderWidth: 1,
                    },
                  ]}
                >
                  <Txt
                    style={{
                      fontSize: 25,
                      fontWeight: "700",
                      color: "#4285F4",
                    }}
                  >
                    G
                  </Txt>
                  <Txt style={s.bold}>Sign in with Google</Txt>
                </Pressable>
              </>
            )}
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                gap: 5,
              }}
            >
              <Txt style={s.muted}>
                {signup ? "Already have an account?" : "Don’t have an account?"}
              </Txt>
              <LinkText
                title={signup ? "Sign In" : "Sign Up"}
                onPress={() => router.replace(signup ? "/login" : "/signup")}
              />
            </View>
          </View>
          <View
            pointerEvents="none"
            style={{ height: 42, overflow: "hidden", marginTop: "auto" }}
          >
            <Waves />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
      <Sheet title={dialog} visible={!!dialog} onClose={() => setDialog("")}>
        {dialog === "Reset password" ? (
          resetSent ? (
            <>
              <Icon name="checkmark-circle" color={C.green} size={45} />
              <Txt>Reset request simulated</Txt>
              <Txt style={s.muted}>
                This local demo does not send email. You can sign in using any
                valid email and a password with at least 8 characters.
              </Txt>
              <Button title="Back to sign in" onPress={() => setDialog("")} />
            </>
          ) : (
            <>
              <Txt style={s.muted}>
                Enter your email to try the password reset flow.
              </Txt>
              <Field
                icon="mail-outline"
                placeholder="Reset email"
                value={resetEmail}
                onChangeText={setResetEmail}
                error={resetError}
                keyboardType="email-address"
              />
              <Button
                title="Send reset link"
                loading={pending}
                onPress={async () => {
                  if (!validEmail(resetEmail)) {
                    setResetError("Enter a valid email address.");
                    return;
                  }
                  setPending(true);
                  try {
                    await auth.reset(resetEmail);
                    setResetSent(true);
                  } finally {
                    setPending(false);
                  }
                }}
              />
            </>
          )
        ) : (
          <Txt style={s.muted}>
            {dialog === "Privacy Policy"
              ? "This prototype stores your demo profile and preferences on this device. It does not collect real location, access contacts, or transmit your data. Passwords are not saved. Sign out to clear your local profile."
              : "This is a local demonstration of Smart Safety Tag. Alerts, device connections and location sharing are simulated. No emergency call or message is sent by this prototype."}
          </Txt>
        )}
      </Sheet>
    </SafeAreaView>
  );
}
