/* Emergencies: all incidents, filters, detail with map + timeline + actions. */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  IoAlertCircle,
  IoCheckmarkDone,
  IoCloseCircle,
  IoHandLeft,
} from "react-icons/io5";
import { DataTable, type Column } from "../components/DataTable";
import { MiniMap } from "../components/MiniMap";
import { Btn, Card, Chip, Modal, Toast } from "../components/ui";
import * as api from "../api/services";
import type { Emergency, EmergencyEvent } from "../api/types";
import { STATUS_LABELS, TRIGGER_LABELS, fmtDateTime, fmtRelative, shortId } from "../lib/format";

function statusTone(status: string): "red" | "amber" | "green" | "gray" {
  if (status === "active") return "red";
  if (status === "acknowledged") return "amber";
  if (status === "resolved") return "green";
  return "gray";
}

export default function Emergencies() {
  const [rows, setRows] = useState<Emergency[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [trigger, setTrigger] = useState("");
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<{ emergency: Emergency; events: EmergencyEvent[] } | null>(
    null,
  );
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);
  const [params, setParams] = useSearchParams();
  const limit = 50;

  const load = useCallback(
    async (o: number) => {
      setLoading(true);
      try {
        const res = await api.listEmergencies({
          status: status || undefined,
          trigger_type: trigger || undefined,
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
    [status, trigger],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  // Deep-link from the user drawer / live monitor (?open=<id>).
  useEffect(() => {
    const openId = params.get("open");
    if (!openId) return;
    api
      .emergencyDetail(openId)
      .then(setDetail)
      .catch(() => setToast({ text: "Emergency not found", error: true }))
      .finally(() => setParams({}, { replace: true }));
  }, [params, setParams]);

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    try {
      await fn();
      setToast({ text: okText, error: false });
      await load(offset);
      if (detail) setDetail(await api.emergencyDetail(detail.emergency.id));
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Action failed", error: true });
    }
  };

  const columns: Column<Emergency>[] = [
    { key: "id", label: "ID", render: (e) => <span className="bold">{shortId(e.id)}</span> },
    {
      key: "user",
      label: "User",
      render: (e) => e.protected_email ?? shortId(e.protected_user_id),
    },
    { key: "trigger", label: "Trigger", render: (e) => TRIGGER_LABELS[e.trigger_type] ?? e.trigger_type },
    {
      key: "status",
      label: "Status",
      render: (e) => <Chip tone={statusTone(e.status)}>{STATUS_LABELS[e.status] ?? e.status}</Chip>,
    },
    {
      key: "where",
      label: "Location",
      render: (e) =>
        e.latitude !== null ? (
          <span className="muted">
            {e.latitude.toFixed(4)}, {e.longitude?.toFixed(4)}
          </span>
        ) : (
          <span className="muted">—</span>
        ),
    },
    { key: "when", label: "When", render: (e) => <span className="muted">{fmtRelative(e.created_at)}</span> },
  ];

  const e = detail?.emergency;

  return (
    <>
      <Card>
        <div className="spread" style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <select
              className="field"
              style={{ width: 170 }}
              value={status}
              onChange={(ev) => setStatus(ev.target.value)}
              aria-label="Filter by status"
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <select
              className="field"
              style={{ width: 180 }}
              value={trigger}
              onChange={(ev) => setTrigger(ev.target.value)}
              aria-label="Filter by trigger"
            >
              <option value="">All triggers</option>
              {Object.entries(TRIGGER_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <span className="muted">{total} incidents</span>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyIcon={IoAlertCircle}
          emptyTitle="No emergencies found"
          pager={{ offset, limit, total }}
          onPage={(o) => {
            setOffset(o);
            void load(o);
          }}
          onRowClick={async (row) => {
            try {
              setDetail(await api.emergencyDetail(row.id));
            } catch (err) {
              setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
            }
          }}
        />
      </Card>

      {e && detail && (
        <Modal
          title={`Emergency ${shortId(e.id)}`}
          onClose={() => setDetail(null)}
          width={640}
        >
          <div className="spread">
            <Chip tone={statusTone(e.status)}>{STATUS_LABELS[e.status] ?? e.status}</Chip>
            <span className="muted">{fmtDateTime(e.created_at)}</span>
          </div>
          <Card>
            <div className="stack">
              <div className="spread">
                <span className="muted">User</span>
                <span className="bold">{e.protected_email ?? shortId(e.protected_user_id)}</span>
              </div>
              <div className="spread">
                <span className="muted">Trigger</span>
                <span className="bold">{TRIGGER_LABELS[e.trigger_type] ?? e.trigger_type}</span>
              </div>
              {e.note && (
                <div className="spread">
                  <span className="muted">Note</span>
                  <span className="bold">{e.note}</span>
                </div>
              )}
              {e.resolved_at && (
                <div className="spread">
                  <span className="muted">Closed</span>
                  <span className="bold">{fmtDateTime(e.resolved_at)}</span>
                </div>
              )}
            </div>
          </Card>

          {e.latitude !== null && e.longitude !== null && (
            <MiniMap
              points={[{ lat: e.latitude, lng: e.longitude, label: "Emergency location" }]}
              height={240}
            />
          )}

          <Card>
            <div className="card-title" style={{ marginBottom: 12 }}>
              Status timeline
            </div>
            <div className="timeline">
              {detail.events.map((ev) => (
                <div key={ev.id} className="entry">
                  <div className="node" />
                  <div>
                    <div className="bold">
                      {ev.from_status ? `${ev.from_status} → ${ev.to_status}` : `created (${ev.to_status})`}
                    </div>
                    <div className="muted" style={{ fontSize: 13 }}>
                      {fmtDateTime(ev.created_at)}
                      {ev.actor_email ? ` · by ${ev.actor_email}` : ""}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {(e.status === "active" || e.status === "acknowledged") && (
            <div className="row" style={{ justifyContent: "flex-end", flexWrap: "wrap" }}>
              {e.status === "active" && (
                <Btn
                  secondary
                  title="Acknowledge"
                  icon={IoHandLeft}
                  onClick={() => act(() => api.ackEmergency(e.id), "Emergency acknowledged")}
                />
              )}
              <Btn
                title="Resolve"
                icon={IoCheckmarkDone}
                onClick={() => act(() => api.resolveEmergency(e.id), "Emergency resolved")}
              />
              <Btn
                ghostDanger
                title="Cancel"
                icon={IoCloseCircle}
                onClick={() => act(() => api.cancelEmergency(e.id), "Emergency cancelled")}
              />
            </div>
          )}
        </Modal>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}
