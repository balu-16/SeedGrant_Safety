/* Push & Broadcast: manage tokens, test push to one user, broadcast to many. */

import { useCallback, useEffect, useState } from "react";
import {
  IoBonfire,
  IoMegaphone,
  IoNotifications,
  IoSearch,
  IoSend,
  IoTrash,
} from "react-icons/io5";
import { Btn, Card, Chip, Field, Toast } from "../components/ui";
import * as api from "../api/services";
import type { AdminUser, PushSendResult, PushToken } from "../api/types";
import { fmtDateTime, fmtRelative } from "../lib/format";

export default function Push() {
  // Target user
  const [q, setQ] = useState("");
  const [matches, setMatches] = useState<AdminUser[]>([]);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [tokens, setTokens] = useState<PushToken[]>([]);

  // Compose
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [allUsers, setAllUsers] = useState(false);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<PushSendResult | null>(null);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);

  const loadTokens = useCallback(async (u: AdminUser) => {
    try {
      setTokens(await api.listPushTokens(u.id));
    } catch {
      setTokens([]);
    }
  }, []);

  useEffect(() => {
    if (!q.trim()) {
      setMatches([]);
      return;
    }
    const t = setTimeout(() => {
      api
        .listUsers({ q, limit: 6 })
        .then((r) => setMatches(r.items))
        .catch(() => setMatches([]));
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const pick = (u: AdminUser) => {
    setUser(u);
    setMatches([]);
    setQ("");
    void loadTokens(u);
  };

  const send = async () => {
    setSending(true);
    setResult(null);
    try {
      const res = await api.sendPush({
        title: title.trim(),
        body: body.trim(),
        all_users: allUsers,
        user_ids: allUsers ? undefined : user ? [user.id] : undefined,
      });
      setResult(res);
      setToast({ text: `Sent via ${res.provider}`, error: false });
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Send failed", error: true });
    } finally {
      setSending(false);
    }
  };

  const canSend =
    title.trim().length > 0 && body.trim().length > 0 && (allUsers || user !== null);

  return (
    <>
      <Card>
        <div className="card-title" style={{ marginBottom: 12 }}>
          <span className="badge-icon" style={{ width: 44, height: 44 }}>
            <IoMegaphone size={24} color="var(--blue)" />
          </span>
          Compose
        </div>
        <div className="stack">
          <Field
            icon={IoNotifications}
            placeholder="Title (e.g. Scheduled maintenance)"
            value={title}
            maxLength={120}
            onChange={(e) => setTitle(e.target.value)}
          />
          <div className="field" style={{ alignItems: "flex-start" }}>
            <IoBonfire size={20} color="var(--muted)" style={{ marginTop: 14 }} aria-hidden />
            <textarea
              placeholder="Message body…"
              value={body}
              maxLength={500}
              rows={3}
              onChange={(e) => setBody(e.target.value)}
              aria-label="Message body"
              style={{
                flex: 1,
                border: "none",
                outline: "none",
                background: "transparent",
                color: "var(--ink)",
                font: "inherit",
                fontSize: 15,
                padding: "12px 0",
                resize: "vertical",
              }}
            />
          </div>

          <div className="spread">
            <label className="row" style={{ cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={allUsers}
                onChange={(e) => setAllUsers(e.target.checked)}
                aria-label="Send to all users"
                style={{ width: 18, height: 18, accentColor: "var(--blue)" }}
              />
              <span className="bold">Send to all users</span>
            </label>
          </div>

          {!allUsers && (
            <div style={{ position: "relative" }}>
              <Field
                icon={IoSearch}
                placeholder={user ? `Target: ${user.email}` : "Or pick a single user…"}
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
              {matches.length > 0 && (
                <div
                  className="card"
                  style={{ position: "absolute", top: 54, left: 0, right: 0, zIndex: 20, padding: 8 }}
                >
                  {matches.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      className="spread"
                      style={{
                        display: "flex",
                        width: "100%",
                        background: "none",
                        border: "none",
                        padding: "10px 12px",
                        cursor: "pointer",
                        borderRadius: 10,
                        textAlign: "left",
                      }}
                      onClick={() => pick(m)}
                    >
                      <span>
                        <span className="bold">{m.name}</span>{" "}
                        <span className="muted" style={{ fontSize: 13 }}>{m.email}</span>
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="row" style={{ justifyContent: "flex-end" }}>
            <Btn
              title={allUsers ? "Broadcast to all users" : "Send push"}
              icon={IoSend}
              loading={sending}
              disabled={!canSend}
              onClick={send}
            />
          </div>
          {result && (
            <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
              <Chip tone="green">Provider: {result.provider}</Chip>
              <Chip tone="blue">Audience: {result.audience_size} user(s)</Chip>
            </div>
          )}
        </div>
      </Card>

      {user && (
        <Card>
          <div className="spread" style={{ marginBottom: 10 }}>
            <div className="card-title">Push tokens — {user.email}</div>
            <Chip tone="gray">{tokens.length} total</Chip>
          </div>
          {tokens.length === 0 ? (
            <div className="muted">No push tokens registered for this user.</div>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Platform</th>
                    <th>Created</th>
                    <th>Last seen</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {tokens.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <Chip tone="blue">{t.platform}</Chip>
                      </td>
                      <td className="muted">{fmtDateTime(t.created_at)}</td>
                      <td className="muted">{fmtRelative(t.last_seen_at)}</td>
                      <td style={{ width: 50 }}>
                        <button
                          type="button"
                          className="icon-btn"
                          aria-label="Delete token"
                          title="Delete token"
                          onClick={async () => {
                            try {
                              await api.deletePushToken(t.id);
                              await loadTokens(user);
                              setToast({ text: "Token deleted", error: false });
                            } catch (err) {
                              setToast({
                                text: err instanceof Error ? err.message : "Failed",
                                error: true,
                              });
                            }
                          }}
                        >
                          <IoTrash size={18} color="var(--red)" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}
