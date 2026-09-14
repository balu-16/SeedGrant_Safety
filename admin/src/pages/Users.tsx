/* Users: search, filter, and full control over every account. */

import { useCallback, useEffect, useState } from "react";
import {
  IoBan,
  IoCall,
  IoCheckmarkCircle,
  IoCreate,
  IoHardwareChip,
  IoHeartCircle,
  IoKey,
  IoLogOut,
  IoPeople,
  IoPerson,
  IoPulse,
  IoSearch,
  IoShieldCheckmark,
  IoTime,
  IoTrash,
} from "react-icons/io5";
import { useNavigate } from "react-router-dom";
import { DataTable, type Column } from "../components/DataTable";
import {
  Avatar,
  Btn,
  Card,
  Chip,
  Drawer,
  Field,
  Icon,
  Modal,
  Toast,
} from "../components/ui";
import * as api from "../api/services";
import type { AdminUser, Emergency, UserDetail } from "../api/types";
import { STATUS_LABELS, fmtDateTime, shortId } from "../lib/format";

export default function Users() {
  const [rows, setRows] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [disabled, setDisabled] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<UserDetail | null>(null);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<AdminUser | null>(null);
  const [deleteText, setDeleteText] = useState("");
  const limit = 20;

  const load = useCallback(
    async (o: number) => {
      setLoading(true);
      try {
        const res = await api.listUsers({
          q: q || undefined,
          role: role || undefined,
          disabled: disabled === "" ? undefined : disabled === "yes",
          limit,
          offset: o,
        });
        setRows(res.items);
        setTotal(res.total);
      } catch (err) {
        setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
      } finally {
        setLoading(false);
      }
    },
    [q, role, disabled],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  const openDetail = async (user: AdminUser) => {
    try {
      setSelected(await api.userDetail(user.id));
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
    }
  };

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    try {
      await fn();
      setToast({ text: okText, error: false });
      await load(offset);
      if (selected) setSelected(await api.userDetail(selected.user.id));
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Action failed", error: true });
    }
  };

  const columns: Column<AdminUser>[] = [
    {
      key: "name",
      label: "User",
      render: (usr) => (
        <span className="row" style={{ gap: 10 }}>
          <Avatar name={usr.name} size={34} />
          <span>
            <span className="bold">{usr.name}</span>
            <br />
            <span className="muted" style={{ fontSize: 13 }}>{usr.email}</span>
          </span>
        </span>
      ),
    },
    {
      key: "role",
      label: "Role",
      render: (usr) =>
        usr.role === "admin" ? <Chip tone="blue">Admin</Chip> : <Chip tone="gray">User</Chip>,
    },
    {
      key: "status",
      label: "Status",
      render: (usr) =>
        usr.disabled_at ? <Chip tone="red">Disabled</Chip> : <Chip tone="green">Active</Chip>,
    },
    {
      key: "created",
      label: "Joined",
      render: (usr) => <span className="muted">{fmtDateTime(usr.created_at)}</span>,
    },
  ];

  const u = selected?.user;

  return (
    <>
      <Card>
        <div className="spread" style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 10, flex: 1, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <Field
                icon={IoSearch}
                placeholder="Search name or email…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <select
              className="field"
              style={{ width: 130 }}
              value={role}
              onChange={(e) => setRole(e.target.value)}
              aria-label="Filter by role"
            >
              <option value="">All roles</option>
              <option value="user">Users</option>
              <option value="admin">Admins</option>
            </select>
            <select
              className="field"
              style={{ width: 150 }}
              value={disabled}
              onChange={(e) => setDisabled(e.target.value)}
              aria-label="Filter by status"
            >
              <option value="">All statuses</option>
              <option value="no">Active only</option>
              <option value="yes">Disabled only</option>
            </select>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyIcon={IoPeople}
          emptyTitle="No users found"
          emptyHint="Try a different search"
          onRowClick={openDetail}
          pager={{ offset, limit, total }}
          onPage={(o) => {
            setOffset(o);
            void load(o);
          }}
        />
      </Card>

      {u && selected && (
        <Drawer
          title={u.name}
          subtitle={`${u.email} · joined ${fmtDateTime(u.created_at)}`}
          onClose={() => setSelected(null)}
        >
          <Card>
            <div className="row" style={{ marginBottom: 12 }}>
              <Avatar name={u.name} size={48} />
              <div style={{ flex: 1 }}>
                <div className="bold">{u.phone}</div>
                <div className="row" style={{ gap: 6, marginTop: 4, flexWrap: "wrap" }}>
                  {u.role === "admin" ? <Chip tone="blue">Admin</Chip> : <Chip tone="gray">User</Chip>}
                  {u.disabled_at ? (
                    <Chip tone="red">Disabled</Chip>
                  ) : (
                    <Chip tone="green">Active</Chip>
                  )}
                </div>
              </div>
            </div>
            <EditProfileRow
              user={u}
              onSave={(name, phone) =>
                act(() => api.updateUser(u.id, { name, phone }), "Profile updated")
              }
            />
          </Card>

          <Card>
            <div className="card-title" style={{ marginBottom: 10 }}>
              <Icon icon={IoPerson} size={19} /> Account actions
            </div>
            <div className="stack">
              <div className="spread">
                <span className="muted">
                  {u.disabled_at ? "Account is suspended" : "Suspend sign-in and kill sessions"}
                </span>
                {u.disabled_at ? (
                  <Btn
                    small
                    title="Enable"
                    icon={IoCheckmarkCircle}
                    onClick={() => act(() => api.enableUser(u.id), "Account enabled")}
                  />
                ) : (
                  <Btn
                    small
                    ghostDanger
                    title="Disable"
                    icon={IoBan}
                    onClick={() => act(() => api.disableUser(u.id), "Account disabled")}
                  />
                )}
              </div>
              <div className="spread">
                <span className="muted">Revoke all refresh tokens</span>
                <Btn
                  small
                  secondary
                  title="Force logout"
                  icon={IoLogOut}
                  onClick={() => act(() => api.forceLogout(u.id), "All sessions revoked")}
                />
              </div>
              <div className="spread">
                <span className="muted">One-time temp password</span>
                <Btn
                  small
                  secondary
                  title="Reset password"
                  icon={IoKey}
                  onClick={async () => {
                    try {
                      const { temp_password } = await api.resetPassword(u.id);
                      setToast({ text: `Temp password: ${temp_password}`, error: false });
                    } catch (err) {
                      setToast({ text: err instanceof Error ? err.message : "Failed", error: true });
                    }
                  }}
                />
              </div>
              <div className="spread">
                <span className="muted">
                  {u.role === "admin" ? "Remove admin role" : "Grant admin role"}
                </span>
                {u.role === "admin" ? (
                  <Btn
                    small
                    secondary
                    title="Demote"
                    icon={IoShieldCheckmark}
                    onClick={() => act(() => api.demoteUser(u.id), "Admin role removed")}
                  />
                ) : (
                  <Btn
                    small
                    secondary
                    title="Promote"
                    icon={IoShieldCheckmark}
                    onClick={() => act(() => api.promoteUser(u.id), "Promoted to admin")}
                  />
                )}
              </div>
              <div className="spread">
                <span className="muted">Delete the account and all its data</span>
                <Btn small ghostDanger title="Delete" icon={IoTrash} onClick={() => setConfirmDelete(u)} />
              </div>
            </div>
          </Card>

          <Card>
            <div className="card-title" style={{ marginBottom: 10 }}>
              <Icon icon={IoHardwareChip} size={19} /> Devices ({selected.devices.length})
            </div>
            {selected.devices.length === 0 ? (
              <div className="muted">No safety tags paired.</div>
            ) : (
              <div className="stack">
                {selected.devices.map((d) => (
                  <div key={d.id} className="spread">
                    <span className="bold">{d.name}</span>
                    <span className="row" style={{ gap: 8 }}>
                      {d.battery_pct !== null && (
                        <Chip tone={d.battery_pct < 20 ? "red" : "green"}>{d.battery_pct}%</Chip>
                      )}
                      <Chip tone={d.connection_state === "online" ? "green" : "gray"}>
                        {d.connection_state}
                      </Chip>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <div className="card-title" style={{ marginBottom: 10 }}>
              <Icon icon={IoHeartCircle} size={19} /> Guardians ({selected.guardians.length})
            </div>
            {selected.guardians.length === 0 ? (
              <div className="muted">No guardians added.</div>
            ) : (
              <div className="stack">
                {selected.guardians.map((g) => (
                  <div key={g.id} className="spread">
                    <span>
                      <span className="bold">{g.guardian_name || g.guardian_email}</span>{" "}
                      <span className="muted" style={{ fontSize: 13 }}>{g.relation}</span>
                    </span>
                    <Chip
                      tone={g.status === "accepted" ? "green" : g.status === "pending" ? "amber" : "gray"}
                    >
                      {g.status}
                    </Chip>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <div className="card-title" style={{ marginBottom: 10 }}>
              <Icon icon={IoPulse} size={19} /> Recent emergencies
            </div>
            <EmergencyMiniList
              emergencies={selected.emergencies}
              onOpen={() => setSelected(null)}
            />
          </Card>

          <Card>
            <div className="card-title" style={{ marginBottom: 10 }}>
              <Icon icon={IoTime} size={19} /> Sessions & tokens
            </div>
            <div className="stack">
              <div className="row">
                <Chip tone="blue">{selected.active_sessions.length} active sessions</Chip>
                <Chip tone="gray">{selected.push_tokens.length} push tokens</Chip>
              </div>
              {selected.push_tokens.map((t) => (
                <div key={t.id} className="spread">
                  <span className="muted">{t.platform} token</span>
                  <span className="muted" style={{ fontSize: 13 }}>
                    seen {fmtDateTime(t.last_seen_at)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </Drawer>
      )}

      {confirmDelete && (
        <Modal title="Delete user?" onClose={() => setConfirmDelete(null)} width={460}>
          <p className="muted" style={{ marginTop: 0 }}>
            This permanently removes <b>{confirmDelete.email}</b> and all of their devices,
            guardians, locations, emergencies and tokens. Type <b>{confirmDelete.email}</b> to confirm.
          </p>
          <Field
            icon={IoTrash}
            placeholder={confirmDelete.email}
            value={deleteText}
            onChange={(e) => setDeleteText(e.target.value)}
          />
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <Btn secondary title="Cancel" onClick={() => setConfirmDelete(null)} />
            <Btn
              danger
              title="Delete forever"
              disabled={deleteText.trim().toLowerCase() !== confirmDelete.email.toLowerCase()}
              onClick={async () => {
                await act(() => api.deleteUser(confirmDelete.id), "User deleted");
                setConfirmDelete(null);
                setSelected(null);
                setDeleteText("");
              }}
            />
          </div>
        </Modal>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}

function EditProfileRow({
  user,
  onSave,
}: {
  user: AdminUser;
  onSave: (name: string, phone: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone);
  if (!editing)
    return (
      <div className="spread">
        <span className="muted">Profile details</span>
        <Btn small secondary title="Edit" icon={IoCreate} onClick={() => setEditing(true)} />
      </div>
    );
  return (
    <div className="stack">
      <Field icon={IoPerson} placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
      <Field icon={IoCall} placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
      <div className="row" style={{ justifyContent: "flex-end" }}>
        <Btn small secondary title="Cancel" onClick={() => setEditing(false)} />
        <Btn
          small
          title="Save"
          onClick={() => {
            onSave(name, phone);
            setEditing(false);
          }}
        />
      </div>
    </div>
  );
}

function EmergencyMiniList({
  emergencies,
  onOpen,
}: {
  emergencies: Emergency[];
  onOpen: () => void;
}) {
  const navigate = useNavigate();
  if (emergencies.length === 0) return <div className="muted">No emergencies.</div>;
  return (
    <div className="stack">
      {emergencies.slice(0, 5).map((e) => (
        <button
          key={e.id}
          type="button"
          className="spread"
          style={{ background: "none", border: "none", padding: 0, cursor: "pointer", textAlign: "left", width: "100%" }}
          onClick={() => {
            onOpen();
            navigate(`/emergencies?open=${e.id}`);
          }}
        >
          <span className="bold">
            {shortId(e.id)} · {e.trigger_type.replaceAll("_", " ").toLowerCase()}
          </span>
          <Chip tone={e.status === "active" ? "red" : e.status === "acknowledged" ? "amber" : "green"}>
            {STATUS_LABELS[e.status] ?? e.status}
          </Chip>
        </button>
      ))}
    </div>
  );
}
