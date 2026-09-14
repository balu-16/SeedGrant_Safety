/* Devices: every safety tag on the platform. */

import { useCallback, useEffect, useState } from "react";
import {
  IoBatteryDead,
  IoCreate,
  IoGitNetworkOutline,
  IoRadio,
  IoTrash,
} from "react-icons/io5";
import { DataTable, type Column } from "../components/DataTable";
import { Btn, Card, Chip, Field, Icon, Modal, Toast } from "../components/ui";
import * as api from "../api/services";
import type { Device } from "../api/types";
import { batteryColor, fmtRelative } from "../lib/format";

export default function Devices() {
  const [rows, setRows] = useState<Device[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState("");
  const [lowBattery, setLowBattery] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);
  const [renaming, setRenaming] = useState<Device | null>(null);
  const [name, setName] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<Device | null>(null);
  const limit = 50;

  const load = useCallback(
    async (o: number) => {
      setLoading(true);
      try {
        const res = await api.listDevices({
          connection_state: state || undefined,
          low_battery: lowBattery,
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
    [state, lowBattery],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  const columns: Column<Device>[] = [
    {
      key: "name",
      label: "Tag",
      render: (d) => (
        <span>
          <span className="bold">{d.name}</span>
          <br />
          <span className="muted" style={{ fontSize: 13 }}>{d.id.slice(0, 8)}</span>
        </span>
      ),
    },
    {
      key: "owner",
      label: "Owner",
      render: (d) => d.owner_email ?? shortOwner(d.owner_id),
    },
    {
      key: "battery",
      label: "Battery",
      render: (d) =>
        d.battery_pct === null ? (
          <span className="muted">—</span>
        ) : (
          <span className="row" style={{ gap: 8 }}>
            <span
              style={{
                width: 60,
                height: 9,
                borderRadius: 6,
                background: "#E7F1FF",
                overflow: "hidden",
              }}
            >
              <span
                style={{
                  display: "block",
                  height: "100%",
                  width: `${Math.min(100, d.battery_pct)}%`,
                  background: batteryColor(d.battery_pct),
                }}
              />
            </span>
            <span className="muted" style={{ fontSize: 13 }}>{d.battery_pct}%</span>
          </span>
        ),
    },
    {
      key: "state",
      label: "State",
      render: (d) => (
        <Chip tone={d.connection_state === "online" ? "green" : "gray"}>
          {d.connection_state}
        </Chip>
      ),
    },
    {
      key: "seen",
      label: "Last seen",
      render: (d) => <span className="muted">{fmtRelative(d.last_seen_at)}</span>,
    },
    {
      key: "actions",
      label: "",
      width: "150px",
      render: (d) => (
        <span className="row" style={{ gap: 2 }}>
          <button
            type="button"
            className="icon-btn"
            aria-label={`Rename ${d.name}`}
            title="Rename"
            onClick={(ev) => {
              ev.stopPropagation();
              setRenaming(d);
              setName(d.name);
            }}
          >
            <Icon icon={IoCreate} size={18} color="var(--blue)" />
          </button>
          <button
            type="button"
            className="icon-btn"
            aria-label={`Force offline ${d.name}`}
            title="Force offline"
            onClick={(ev) => {
              ev.stopPropagation();
              void doAct(() => api.forceDeviceOffline(d.id), "Tag marked offline");
            }}
          >
            <Icon icon={IoGitNetworkOutline} size={18} color="var(--muted)" />
          </button>
          <button
            type="button"
            className="icon-btn"
            aria-label={`Delete ${d.name}`}
            title="Delete"
            onClick={(ev) => {
              ev.stopPropagation();
              setConfirmDelete(d);
            }}
          >
            <Icon icon={IoTrash} size={18} color="var(--red)" />
          </button>
        </span>
      ),
    },
  ];

  const doAct = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      setToast({ text: ok, error: false });
      await load(offset);
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Action failed", error: true });
    }
  };

  return (
    <>
      <Card>
        <div className="spread" style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <select
              className="field"
              style={{ width: 150 }}
              value={state}
              onChange={(e) => setState(e.target.value)}
              aria-label="Filter by connection state"
            >
              <option value="">All states</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="unknown">Unknown</option>
            </select>
            <button
              type="button"
              className={`chip ${lowBattery ? "red" : "gray"}`}
              style={{ cursor: "pointer", border: "none" }}
              onClick={() => setLowBattery((v) => !v)}
              aria-pressed={lowBattery}
            >
              <Icon icon={IoBatteryDead} size={14} /> Low battery (&lt;20%)
            </button>
          </div>
          <span className="muted">{total} tags</span>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyIcon={IoRadio}
          emptyTitle="No devices found"
          pager={{ offset, limit, total }}
          onPage={(o) => {
            setOffset(o);
            void load(o);
          }}
        />
      </Card>

      {renaming && (
        <Modal title="Rename tag" onClose={() => setRenaming(null)} width={420}>
          <Field icon={IoCreate} placeholder="Tag name" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <Btn secondary title="Cancel" onClick={() => setRenaming(null)} />
            <Btn
              title="Save"
              disabled={!name.trim()}
              onClick={async () => {
                await doAct(() => api.renameDevice(renaming.id, name.trim()), "Tag renamed");
                setRenaming(null);
              }}
            />
          </div>
        </Modal>
      )}

      {confirmDelete && (
        <Modal title="Delete tag?" onClose={() => setConfirmDelete(null)} width={430}>
          <p className="muted" style={{ marginTop: 0 }}>
            Remove <b>{confirmDelete.name}</b> from {confirmDelete.owner_email ?? "its owner"}?
            The tag disappears from their app. Location history is kept.
          </p>
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <Btn secondary title="Cancel" onClick={() => setConfirmDelete(null)} />
            <Btn
              danger
              title="Delete"
              onClick={async () => {
                await doAct(() => api.deleteDevice(confirmDelete.id), "Tag deleted");
                setConfirmDelete(null);
              }}
            />
          </div>
        </Modal>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}

function shortOwner(id: string): string {
  return `user ${id.slice(0, 8)}`;
}
