/* System: platform health + the signed-in admin's own session. */

import { useCallback, useEffect, useState } from "react";
import {
  IoGlobe,
  IoHardwareChip,
  IoLogOut,
  IoPersonCircle,
  IoServer,
} from "react-icons/io5";
import { BadgeIcon, Btn, Card, Chip, Spinner, Toast } from "../components/ui";
import * as api from "../api/services";
import { apiFetch } from "../api/client";
import type { AdminHealth } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { fmtDateTime } from "../lib/format";

export default function System() {
  const { admin, logout } = useAuth();
  const [hp, setHp] = useState<AdminHealth | null>(null);
  const [basic, setBasic] = useState<{ service: string; env: string; time: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [h, b] = await Promise.all([
        api.health(),
        apiFetch<{ status: string; service: string; env: string; time: string }>(
          "/api/health",
          { auth: false },
        ),
      ]);
      setHp(h);
      setBasic(b);
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !hp) return <Spinner />;

  return (
    <>
      <div className="grid-2">
        <Card>
          <div className="card-title" style={{ marginBottom: 14 }}>
            <BadgeIcon icon={IoServer} size={22} color="var(--green)" /> Backend health
          </div>
          {hp ? (
            <div className="stack">
              <div className="spread">
                <span className="muted">Overall</span>
                <Chip tone={hp.status === "ok" ? "green" : "red"}>{hp.status}</Chip>
              </div>
              <div className="spread">
                <span className="muted">Database</span>
                <Chip tone={hp.database === "up" || hp.database === "fake" ? "green" : "red"}>
                  {hp.database}
                </Chip>
              </div>
              <div className="spread">
                <span className="muted">Environment</span>
                <Chip tone="blue">{hp.env}</Chip>
              </div>
              <div className="spread">
                <span className="muted">Push provider</span>
                <Chip tone="gray">{hp.push_provider}</Chip>
              </div>
              <div className="spread">
                <span className="muted">FCM configured</span>
                <Chip tone={hp.fcm_configured ? "green" : "gray"}>
                  {hp.fcm_configured ? "yes" : "no"}
                </Chip>
              </div>
              <div className="spread">
                <span className="muted">ADMIN_EMAILS bootstrap entries</span>
                <Chip tone="gray">{hp.admin_bootstrap_emails}</Chip>
              </div>
            </div>
          ) : (
            <div className="muted">Health endpoint unreachable.</div>
          )}
        </Card>

        <Card>
          <div className="card-title" style={{ marginBottom: 14 }}>
            <BadgeIcon icon={IoGlobe} size={22} /> API service
          </div>
          {basic && (
            <div className="stack">
              <div className="spread">
                <span className="muted">Service</span>
                <span className="bold">{basic.service}</span>
              </div>
              <div className="spread">
                <span className="muted">Server time</span>
                <span className="bold">{fmtDateTime(basic.time)}</span>
              </div>
            </div>
          )}
          <div className="muted" style={{ marginTop: 12 }}>
            The admin portal shares this backend with the mobile app. Health and readiness
            also live at <code>/api/health</code> and <code>/api/ready</code>.
          </div>
        </Card>
      </div>

      <Card>
        <div className="card-title" style={{ marginBottom: 14 }}>
          <BadgeIcon icon={IoPersonCircle} size={22} /> Your admin session
        </div>
        {admin && (
          <div className="stack">
            <div className="spread">
              <span className="muted">Signed in as</span>
              <span className="bold">
                {admin.name} · {admin.email}
              </span>
            </div>
            <div className="spread">
              <span className="muted">Role</span>
              <Chip tone="blue">admin</Chip>
            </div>
            <div className="spread">
              <span className="muted">Sign out of this browser</span>
              <Btn
                small
                secondary
                title="Sign out"
                icon={IoLogOut}
                onClick={async () => {
                  await logout();
                  window.location.href = "/login";
                }}
              />
            </div>
          </div>
        )}
      </Card>

      <Card>
        <div className="card-title" style={{ marginBottom: 8 }}>
          <BadgeIcon icon={IoHardwareChip} size={22} /> Operational notes
        </div>
        <ul className="muted" style={{ margin: 0, paddingLeft: 18, lineHeight: 1.7 }}>
          <li>
            Promote more admins with <code>ADMIN_EMAILS</code> on the server, or one-off via{" "}
            <code>uv run python -m app.bootstrap_admin email@example.com</code>.
          </li>
          <li>Every action taken in this portal is recorded in the Audit Log.</li>
          <li>Disabling a user revokes their sessions immediately — no grace period.</li>
        </ul>
      </Card>

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}
