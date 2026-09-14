/* Audit log: every admin mutation with filters. */

import { useCallback, useEffect, useState } from "react";
import { IoShieldCheckmark } from "react-icons/io5";
import { DataTable, type Column } from "../components/DataTable";
import { Card, Chip } from "../components/ui";
import { listAudit } from "../api/services";
import type { AuditEntry } from "../api/types";
import { fmtDateTime } from "../lib/format";

function actionTone(action: string): "red" | "blue" | "amber" | "gray" {
  if (action.includes("delete") || action.includes("disable") || action.includes("purge"))
    return "red";
  if (action.includes("promote") || action.includes("send")) return "amber";
  if (action.startsWith("user")) return "blue";
  return "gray";
}

export default function Audit() {
  const [rows, setRows] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [action, setAction] = useState("");
  const [targetType, setTargetType] = useState("");
  const [loading, setLoading] = useState(true);
  const limit = 50;

  const load = useCallback(
    async (o: number) => {
      setLoading(true);
      try {
        const res = await listAudit({
          action: action || undefined,
          target_type: targetType || undefined,
          limit,
          offset: o,
        });
        setRows(res.items);
        setTotal(res.total);
      } finally {
        setLoading(false);
      }
    },
    [action, targetType],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  const columns: Column<AuditEntry>[] = [
    {
      key: "when",
      label: "When",
      width: "170px",
      render: (a) => <span className="muted">{fmtDateTime(a.created_at)}</span>,
    },
    {
      key: "actor",
      label: "Admin",
      render: (a) => a.actor_email ?? short(a.actor_user_id),
    },
    {
      key: "action",
      label: "Action",
      render: (a) => <Chip tone={actionTone(a.action)}>{a.action}</Chip>,
    },
    {
      key: "target",
      label: "Target",
      render: (a) => (
        <span className="muted">
          {a.target_type}
          {a.target_id ? ` · ${a.target_id.slice(0, 8)}` : ""}
        </span>
      ),
    },
    {
      key: "details",
      label: "Details",
      render: (a) =>
        a.details ? (
          <code style={{ fontSize: 12.5, color: "var(--muted)" }}>
            {JSON.stringify(a.details)}
          </code>
        ) : (
          <span className="muted">—</span>
        ),
    },
  ];

  return (
    <>
      <Card>
        <div className="spread" style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <input
              className="field"
              style={{ width: 210, paddingLeft: 14 }}
              placeholder="Filter action (e.g. user.disable)"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              aria-label="Filter by action"
            />
            <select
              className="field"
              style={{ width: 160 }}
              value={targetType}
              onChange={(e) => setTargetType(e.target.value)}
              aria-label="Filter by target type"
            >
              <option value="">All targets</option>
              <option value="user">user</option>
              <option value="device">device</option>
              <option value="guardian">guardian</option>
              <option value="emergency">emergency</option>
              <option value="push_token">push_token</option>
            </select>
          </div>
          <span className="muted">{total} entries</span>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyIcon={IoShieldCheckmark}
          emptyTitle="No audit entries"
          emptyHint="Admin actions will appear here"
          pager={{ offset, limit, total }}
          onPage={(o) => {
            setOffset(o);
            void load(o);
          }}
        />
      </Card>
    </>
  );
}

function short(id: string | null): string {
  return id ? `admin ${id.slice(0, 8)}` : "system";
}
