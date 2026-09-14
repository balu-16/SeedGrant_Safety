/* Guardians: every safety-circle link, with force consent transitions. */

import { useCallback, useEffect, useState } from "react";
import { IoHeartCircle, IoTrash } from "react-icons/io5";
import { DataTable, type Column } from "../components/DataTable";
import { Btn, Card, Chip, Modal, Toast } from "../components/ui";
import * as api from "../api/services";
import type { GuardianLink } from "../api/types";
import { fmtDateTime } from "../lib/format";

function tone(status: string): "green" | "amber" | "gray" | "red" {
  if (status === "accepted") return "green";
  if (status === "pending") return "amber";
  if (status === "rejected") return "red";
  return "gray";
}

const STATUSES = ["pending", "accepted", "rejected", "removed"];

export default function Guardians() {
  const [rows, setRows] = useState<GuardianLink[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);
  const [deleting, setDeleting] = useState<GuardianLink | null>(null);
  const limit = 50;

  const load = useCallback(
    async (o: number) => {
      setLoading(true);
      try {
        const res = await api.listGuardians({ status: status || undefined, limit, offset: o });
        setRows(res.items);
        setTotal(res.total);
      } catch (err) {
        setToast({ text: err instanceof Error ? err.message : "Load failed", error: true });
      } finally {
        setLoading(false);
      }
    },
    [status],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      setToast({ text: ok, error: false });
      await load(offset);
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Action failed", error: true });
    }
  };

  const columns: Column<GuardianLink>[] = [
    {
      key: "guardian",
      label: "Guardian",
      render: (g) => (
        <span>
          <span className="bold">{g.guardian_name || g.guardian_email}</span>
          <br />
          <span className="muted" style={{ fontSize: 13 }}>
            {g.guardian_account_email ?? "not registered"}
          </span>
        </span>
      ),
    },
    {
      key: "protected",
      label: "Protects",
      render: (g) => g.protected_email ?? shortId(g.protected_user_id),
    },
    { key: "relation", label: "Relation", render: (g) => g.relation || "—" },
    {
      key: "primary",
      label: "Primary",
      render: (g) => (g.is_primary ? <Chip tone="blue">Primary</Chip> : <span className="muted">—</span>),
    },
    {
      key: "status",
      label: "Consent",
      render: (g) => <Chip tone={tone(g.status)}>{g.status}</Chip>,
    },
    {
      key: "force",
      label: "Force status",
      render: (g) => (
        <select
          className="field"
          style={{ minHeight: 38, width: 130 }}
          value={g.status}
          aria-label={`Force status for ${g.guardian_email}`}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) =>
            act(
              () => api.forceGuardianStatus(g.id, e.target.value),
              `Link forced to ${e.target.value}`,
            )
          }
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      ),
    },
    {
      key: "actions",
      label: "",
      width: "60px",
      render: (g) => (
        <button
          type="button"
          className="icon-btn"
          aria-label={`Delete link ${g.guardian_email}`}
          title="Delete link"
          onClick={(e) => {
            e.stopPropagation();
            setDeleting(g);
          }}
        >
          <IoTrash size={18} color="var(--red)" />
        </button>
      ),
    },
    {
      key: "created",
      label: "Added",
      render: (g) => <span className="muted">{fmtDateTime(g.created_at)}</span>,
    },
  ];

  return (
    <>
      <Card>
        <div className="spread" style={{ marginBottom: 12 }}>
          <select
            className="field"
            style={{ width: 170 }}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <span className="muted">{total} links</span>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyIcon={IoHeartCircle}
          emptyTitle="No guardian links"
          pager={{ offset, limit, total }}
          onPage={(o) => {
            setOffset(o);
            void load(o);
          }}
        />
      </Card>

      {deleting && (
        <Modal title="Delete guardian link?" onClose={() => setDeleting(null)} width={440}>
          <p className="muted" style={{ marginTop: 0 }}>
            Remove <b>{deleting.guardian_email}</b> from protecting{" "}
            <b>{deleting.protected_email ?? shortId(deleting.protected_user_id)}</b>? This
            cannot be undone.
          </p>
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <Btn secondary title="Cancel" onClick={() => setDeleting(null)} />
            <Btn
              danger
              title="Delete"
              onClick={async () => {
                await act(() => api.deleteGuardian(deleting.id), "Link deleted");
                setDeleting(null);
              }}
            />
          </div>
        </Modal>
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}

function shortId(id: string): string {
  return id.slice(0, 8);
}
