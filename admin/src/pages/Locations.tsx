/* Locations: pick a user, see latest + history on a real map, purge history. */

import { useCallback, useEffect, useState } from "react";
import { IoLocation, IoSearch, IoSearchCircle, IoTrash } from "react-icons/io5";
import { MiniMap } from "../components/MiniMap";
import { Btn, Card, Chip, Field, Toast } from "../components/ui";
import * as api from "../api/services";
import type { AdminUser, LocationPoint } from "../api/types";
import { fmtDateTime, fmtRelative } from "../lib/format";

export default function Locations() {
  const [q, setQ] = useState("");
  const [matches, setMatches] = useState<AdminUser[]>([]);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [latest, setLatest] = useState<LocationPoint | null>(null);
  const [history, setHistory] = useState<LocationPoint[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);
  const [confirmPurge, setConfirmPurge] = useState(false);

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

  const loadUser = useCallback(async (u: AdminUser) => {
    setUser(u);
    setLoading(true);
    setSelectedIdx(0);
    setMatches([]);
    setQ("");
    try {
      const [lat, hist] = await Promise.all([
        api.latestLocation(u.id),
        api.locationHistory(u.id, 200),
      ]);
      setLatest(lat);
      setHistory(hist.items);
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
    } finally {
      setLoading(false);
    }
  }, []);

  const points = [...history]
    .reverse()
    .filter((p) => p.latitude !== null)
    .map((p) => ({ lat: p.latitude, lng: p.longitude }));

  return (
    <>
      <Card>
        <div style={{ position: "relative" }}>
          <Field
            icon={IoSearch}
            placeholder="Find a user by name or email…"
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
                  onClick={() => void loadUser(m)}
                >
                  <span>
                    <span className="bold">{m.name}</span>{" "}
                    <span className="muted" style={{ fontSize: 13 }}>{m.email}</span>
                  </span>
                  <span className="row" style={{ gap: 6 }}>
                    {m.role === "admin" && <Chip tone="blue">Admin</Chip>}
                    {m.disabled_at && <Chip tone="red">Disabled</Chip>}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
        {user && (
          <div className="spread" style={{ marginTop: 12 }}>
            <div className="row">
              <Chip tone="blue">{user.name}</Chip>
              <span className="muted">{user.email}</span>
            </div>
            <Btn
              small
              ghostDanger
              title="Purge location history"
              icon={IoTrash}
              onClick={() => setConfirmPurge(true)}
            />
          </div>
        )}
      </Card>

      {!user && (
        <Card>
          <div className="empty" style={{ padding: "60px 20px" }}>
            <div className="badge-icon" style={{ width: 64, height: 64 }}>
              <IoSearchCircle size={34} color="var(--blue)" />
            </div>
            <div className="bold">Search for a user to inspect their location trail</div>
            <div className="muted">
              Access is audited. Purging history is permanent and affects the user's app.
            </div>
          </div>
        </Card>
      )}

      {user && loading && <Card>Loading location data…</Card>}

      {user && !loading && (
        <>
          {points.length === 0 ? (
            <Card>
              <div className="empty">
                <div className="badge-icon">
                  <IoLocation size={28} color="var(--blue)" />
                </div>
                <div className="bold">No location history</div>
                <div className="muted">This user has not shared any locations yet.</div>
              </div>
            </Card>
          ) : (
            <>
              <Card style={{ padding: 0, overflow: "hidden" }}>
                <MiniMap
                  points={[...points].reverse().map((p, i) => ({
                    ...p,
                    label: i === 0 ? "Latest" : undefined,
                  }))}
                  trail
                  height={380}
                />
              </Card>
              {latest && (
                <Card>
                  <div className="spread">
                    <div className="row">
                      <Chip tone="red">Latest fix</Chip>
                      <span className="bold">
                        {latest.latitude.toFixed(5)}, {latest.longitude.toFixed(5)}
                      </span>
                    </div>
                    <span className="muted">
                      {latest.source} · {fmtRelative(latest.recorded_at)}
                      {latest.accuracy_m !== null ? ` · ±${Math.round(latest.accuracy_m)}m` : ""}
                    </span>
                  </div>
                </Card>
              )}
              <Card>
                <div className="card-title" style={{ marginBottom: 10 }}>
                  History ({history.length})
                </div>
                <div className="table-wrap" style={{ maxHeight: 320, overflowY: "auto" }}>
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Recorded</th>
                        <th>Coordinates</th>
                        <th>Source</th>
                        <th>Accuracy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((p, i) => (
                        <tr
                          key={p.id}
                          className="clickable"
                          onClick={() => setSelectedIdx(i)}
                          style={{ background: i === selectedIdx ? "var(--pale)" : undefined }}
                        >
                          <td className="muted">{fmtDateTime(p.recorded_at)}</td>
                          <td className="bold">
                            {p.latitude.toFixed(5)}, {p.longitude.toFixed(5)}
                          </td>
                          <td>
                            <Chip tone="gray">{p.source}</Chip>
                          </td>
                          <td className="muted">
                            {p.accuracy_m !== null ? `±${Math.round(p.accuracy_m)}m` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}
        </>
      )}

      {confirmPurge && user && (
        <div className="scrim" onClick={(e) => e.target === e.currentTarget && setConfirmPurge(false)}>
          <div className="modal-card" style={{ maxWidth: 440 }} role="dialog" aria-modal="true">
            <h2 className="heading">Purge location history?</h2>
            <p className="muted" style={{ marginTop: 0 }}>
              Permanently delete all {history.length} location records for{" "}
              <b>{user.email}</b>. Their Track history will be empty afterwards.
            </p>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <Btn secondary title="Cancel" onClick={() => setConfirmPurge(false)} />
              <Btn
                danger
                title="Purge history"
                onClick={async () => {
                  try {
                    const { deleted } = await api.purgeLocations(user.id);
                    setToast({ text: `Deleted ${deleted} location records`, error: false });
                    setConfirmPurge(false);
                    await loadUser(user);
                  } catch (err) {
                    setToast({ text: err instanceof Error ? err.message : "Failed", error: true });
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}
