import { useEffect, useState } from "react";
import { Image, View } from "react-native";
import { Header } from "../../components/Header";
import {
  Avatar,
  Button,
  Card,
  Field,
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
import { useApp } from "../../store/AppStore";
import { Guardian } from "../../types";
import { ApiError } from "../../services/api";
import { getServices, isBackendMode } from "../../services/index";
import { validEmail, validPhone } from "../../utils/validation";
const blank = { id: "", name: "", relation: "", phone: "", primary: false, email: "" };
// The edit form always carries a concrete email string (server identity).
type EditingGuardian = Guardian & { email: string };
export default function GuardiansScreen() {
  const { state, dispatch } = useApp();
  const userId = state.user?.id ?? null;
  const backend = isBackendMode(userId);
  const [editing, setEditing] = useState<EditingGuardian | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [dialog, setDialog] = useState("");
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [saving, setSaving] = useState(false);
  const [invites, setInvites] = useState<Guardian[]>([]);
  useEffect(() => {
    if (!backend) return;
    let active = true;
    const remote = getServices(userId).guardians;
    remote
      ?.protecting(true)
      .then((list) => {
        if (active) setInvites(list.filter((g) => g.status === "pending"));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [backend, userId, state.guardians.length]);
  async function respondInvite(id: string, status: "accepted" | "rejected") {
    if (saving) return;
    setSaving(true);
    try {
      const remote = getServices(userId).guardians;
      if (!remote) return;
      await remote.respond(id, status);
      const list = await remote.protecting(true);
      setInvites(list.filter((g) => g.status === "pending"));
    } catch (e) {
      setErrors({ general: errorMessage(e, "Could not update the invite. Please try again.") });
    } finally {
      setSaving(false);
    }
  }
  function edit(guardian: Guardian) {
    setEditing({ ...guardian, email: guardian.email ?? "" });
    setErrors({});
    setConfirmRemove(false);
  }
  function errorMessage(e: unknown, fallback: string): string {
    return e instanceof ApiError ? e.message : fallback;
  }
  /** Backend mode: replace the local list with the server's truth. */
  async function syncFromServer(): Promise<boolean> {
    const remote = getServices(userId).guardians;
    if (!remote) return false;
    const guardians = await remote.list();
    dispatch({ type: "guardians", guardians });
    return true;
  }
  async function save() {
    if (!editing || saving) return;
    const nextErrors: Record<string, string> = {};
    if (!editing.name.trim()) nextErrors.name = "Enter a name.";
    if (!editing.relation.trim()) nextErrors.relation = "Enter a relationship.";
    if (backend) {
      // The server identifies guardians by email; phone is informational.
      if (!validEmail(editing.email)) nextErrors.email = "Enter the guardian's email.";
      else if (
        state.guardians.some(
          (g) => g.id !== editing.id && (g.email ?? "").toLowerCase() === editing.email.trim().toLowerCase(),
        )
      )
        nextErrors.email = "This guardian is already in your circle.";
    } else {
      if (!validPhone(editing.phone)) nextErrors.phone = "Enter a valid phone number.";
      if (
        state.guardians.some(
          (g) =>
            g.id !== editing.id &&
            g.phone.replace(/\D/g, "") === editing.phone.replace(/\D/g, ""),
        )
      )
        nextErrors.phone = "This guardian is already in your circle.";
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setSaving(true);
    try {
      if (backend) {
        const remote = getServices(userId).guardians;
        if (!remote) return;
        await remote.invite({
          email: editing.email.trim().toLowerCase(),
          name: editing.name.trim(),
          relation: editing.relation.trim(),
          primary: editing.primary,
        });
        await syncFromServer();
      } else {
        const saved = {
          ...editing,
          // eslint-disable-next-line react-hooks/purity -- event handler, not render
          id: editing.id || `guardian-${Date.now()}`,
          name: editing.name.trim(),
          relation: editing.relation.trim(),
          phone: editing.phone.trim(),
        };
        let guardians = editing.id
          ? state.guardians.map((g) => (g.id === editing.id ? saved : g))
          : [...state.guardians, saved];
        if (saved.primary)
          guardians = guardians.map((g) => ({ ...g, primary: g.id === saved.id }));
        dispatch({ type: "guardians", guardians });
      }
      setEditing(null);
    } catch (e) {
      setErrors({ general: errorMessage(e, "Could not save the guardian. Please try again.") });
    } finally {
      setSaving(false);
    }
  }
  async function removeGuardian() {
    if (!editing || saving) return;
    setSaving(true);
    try {
      if (backend) {
        const remote = getServices(userId).guardians;
        if (!remote) return;
        await remote.remove(editing.id);
        await syncFromServer();
      } else {
        dispatch({
          type: "guardians",
          guardians: state.guardians.filter((g) => g.id !== editing.id),
        });
      }
      setEditing(null);
    } catch (e) {
      setErrors({ general: errorMessage(e, "Could not remove the guardian. Please try again.") });
    } finally {
      setSaving(false);
    }
  }
  return (
    <Page>
      <Header title="Guardians" subtitle="People who get your alerts" />
      <View style={{ alignItems: "center", paddingVertical: 17, gap: 12 }}>
        <Image
          source={require("../../../assets/illustrations/guardians.png")}
          accessibilityLabel="Your trusted safety circle"
          style={{ width: "100%", height: 150 }}
          resizeMode="cover"
        />
        <Txt style={{ color: C.muted, fontSize: 14 }}>
          Your safety is a team effort. Safer together ♡
        </Txt>
      </View>
      <Row
        title={`${state.guardians.length} trusted contacts connected`}
        subtitle="Your SOS alerts are shared with all guardians"
        icon="people"
        color={C.green}
        onPress={() => setDialog("Your safety circle")}
      />
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Txt style={{ fontSize: 22, fontWeight: "700" }}>Your Guardians</Txt>
        <LinkText title="Edit" onPress={() => setDialog("Edit guardians")} />
      </View>
      {state.guardians.map((g) => (
        <Card
          key={g.id}
          label={`Edit ${g.name}`}
          onPress={() => edit(g)}
          style={s.row}
        >
          <Avatar name={g.name} size={55} />
          <View style={{ flex: 1, gap: 4 }}>
            <Txt style={s.bold}>{g.name}</Txt>
            <Txt style={s.muted}>{g.relation}</Txt>
            <Txt style={{ color: C.muted, fontSize: 12 }}>
              {g.phone ? `☎ ${g.phone}` : g.email ? `✉ ${g.email}` : ""}
            </Txt>
          </View>
          <View style={{ gap: 10, alignItems: "flex-end" }}>
            <Txt
              style={{
                color: g.primary ? "#E66546" : C.green,
                backgroundColor: g.primary ? "#FFF0EB" : "#EBF8EF",
                paddingHorizontal: 8,
                paddingVertical: 5,
                borderRadius: 20,
                fontSize: 11,
              }}
            >
              {g.primary ? "♛ Primary" : g.status === "pending" ? "◌ Pending" : "● Active"}
            </Txt>
            <Icon name="chevron-forward" color={C.muted} size={18} />
          </View>
        </Card>
      ))}
      {!state.guardians.length && (
        <Card>
          <Txt style={s.bold}>Start your safety circle</Txt>
          <Txt style={s.muted}>
            Add someone you trust to try sharing and alerts.
          </Txt>
        </Card>
      )}
      <Row
        title="Add Guardian"
        subtitle="Invite someone to be part of your safety circle"
        icon="person-add"
        onPress={() => edit(blank)}
      />
      <Row
        title="Emergency Alert Preferences"
        subtitle="SOS alerts sent to all guardians"
        icon="shield-checkmark"
        color="#ED6178"
        onPress={() => setDialog("Emergency Alert Preferences")}
      />
      {backend && invites.length > 0 && (
        <Row
          title={`${invites.length} guardian ${invites.length === 1 ? "invite" : "invites"} waiting`}
          subtitle="People asking you to be their guardian"
          icon="mail"
          color={C.blue}
          onPress={() => setDialog("Guardian Invites")}
        />
      )}
      <Sheet
        title={editing?.id ? "Edit Guardian" : "Add Guardian"}
        visible={!!editing}
        onClose={() => setEditing(null)}
      >
        {editing &&
          (confirmRemove ? (
            <>
              <Txt>Remove {editing.name} from your safety circle?</Txt>
              <Txt style={s.muted}>
                They will no longer be included in {backend ? "sharing and alerts" : "simulated sharing and alerts"}.
              </Txt>
              <Button
                title="Remove guardian"
                danger
                loading={saving}
                onPress={removeGuardian}
              />
              <Button
                title="Keep guardian"
                secondary
                onPress={() => setConfirmRemove(false)}
              />
            </>
          ) : (
            <>
              <Field
                icon="person-outline"
                placeholder="Guardian name"
                value={editing.name}
                autoCapitalize="words"
                onChangeText={(name) => setEditing({ ...editing, name })}
                error={errors.name}
              />
              <Field
                icon="people-outline"
                placeholder="Relationship"
                value={editing.relation}
                autoCapitalize="words"
                onChangeText={(relation) =>
                  setEditing({ ...editing, relation })
                }
                error={errors.relation}
              />
              {backend && (
                <Field
                  icon="mail-outline"
                  placeholder="Guardian email"
                  value={editing.email ?? ""}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  onChangeText={(email) => setEditing({ ...editing, email })}
                  error={errors.email}
                />
              )}
              <Field
                icon="call-outline"
                placeholder={
                  backend ? "Guardian phone (optional)" : "Guardian phone"
                }
                value={editing.phone}
                keyboardType="phone-pad"
                onChangeText={(phone) => setEditing({ ...editing, phone })}
                error={errors.phone}
              />
              <Toggle
                title="Primary guardian"
                value={editing.primary}
                onChange={(primary) => setEditing({ ...editing, primary })}
              />
              {!!errors.general && <Txt style={s.error}>{errors.general}</Txt>}
              <Txt style={s.muted}>
                {backend
                  ? "An invite is recorded on the server — once they join with this email, they accept it from their Guardian tab."
                  : "Saved locally for this demo. No invitation is sent."}
              </Txt>
              <Button title="Save guardian" loading={saving} onPress={save} />
              {editing.id && (
                <Button
                  title="Remove guardian"
                  danger
                  secondary
                  onPress={() => setConfirmRemove(true)}
                />
              )}
            </>
          ))}
      </Sheet>
      <Sheet title={dialog} visible={!!dialog} onClose={() => setDialog("")}>
        {dialog === "Emergency Alert Preferences" ? (
          <>
            <Toggle
              title="Alert notifications"
              value={state.preferences.notifications}
              onChange={(notifications) =>
                dispatch({ type: "preferences", value: { notifications } })
              }
            />
            <Toggle
              title="Vibration"
              value={state.preferences.vibration}
              onChange={(vibration) =>
                dispatch({ type: "preferences", value: { vibration } })
              }
            />
            <Txt style={s.muted}>
              Preferences apply to {backend ? "real SOS delivery" : "this demo"}.{" "}
              {backend ? "" : "No calls or push notifications are sent."}
            </Txt>
          </>
        ) : dialog === "Guardian Invites" ? (
          <>
            {invites.length === 0 ? (
              <Txt>No pending invites.</Txt>
            ) : (
              invites.map((g) => (
                <Card key={g.id} style={{ gap: 8 }}>
                  <Txt style={s.bold}>{g.name}</Txt>
                  <Txt style={s.muted}>
                    {g.relation}
                    {g.email ? ` · ${g.email}` : ""}
                  </Txt>
                  {!!errors.general && <Txt style={s.error}>{errors.general}</Txt>}
                  <Button
                    title="Accept"
                    loading={saving}
                    onPress={() => respondInvite(g.id, "accepted")}
                  />
                  <Button
                    title="Decline"
                    secondary
                    disabled={saving}
                    onPress={() => respondInvite(g.id, "rejected")}
                  />
                </Card>
              ))
            )}
          </>
        ) : dialog === "Edit guardians" ? (
          <>
            {state.guardians.map((g) => (
              <Row
                key={g.id}
                title={g.name}
                subtitle={g.relation}
                icon="person"
                onPress={() => {
                  setDialog("");
                  edit(g);
                }}
              />
            ))}
            <Button
              title="Add Guardian"
              onPress={() => {
                setDialog("");
                edit(blank);
              }}
            />
          </>
        ) : (
          <>
            <Txt>{state.guardians.length} trusted guardians are connected.</Txt>
            <Txt style={s.muted}>
              Your circle receives {backend ? "real SOS alerts" : "simulated SOS alerts"}. Manage each contact to
              update their details or choose your primary guardian.
            </Txt>
          </>
        )}
      </Sheet>
    </Page>
  );
}
