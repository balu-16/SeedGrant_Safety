/* Reusable data table with pager, matching the app's card-and-row rhythm. */

import { type ReactNode } from "react";
import { IoChevronBack, IoChevronForward } from "react-icons/io5";
import { EmptyState, Spinner } from "./ui";
import type { IconType } from "react-icons";

export interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => ReactNode;
  width?: string;
}

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  loading,
  emptyIcon,
  emptyTitle,
  emptyHint,
  onRowClick,
  pager,
  onPage,
}: {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  emptyIcon: IconType;
  emptyTitle: string;
  emptyHint?: string;
  onRowClick?: (row: T) => void;
  pager?: { offset: number; limit: number; total: number };
  onPage?: (offset: number) => void;
}) {
  if (loading && rows.length === 0) return <Spinner />;
  if (rows.length === 0)
    return <EmptyState icon={emptyIcon} title={emptyTitle} hint={emptyHint} />;

  const page = pager ? Math.floor(pager.offset / pager.limit) + 1 : 1;
  const pages = pager ? Math.max(1, Math.ceil(pager.total / pager.limit)) : 1;

  return (
    <div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} style={c.width ? { width: c.width } : undefined}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className={onRowClick ? "clickable" : ""}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? "—")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pager && pager.total > pager.limit && onPage && (
        <div className="pager">
          <span className="info">
            Page {page} of {pages} · {pager.total} total
          </span>
          <button
            type="button"
            className="icon-btn"
            aria-label="Previous page"
            disabled={pager.offset === 0}
            onClick={() => onPage(Math.max(0, pager.offset - pager.limit))}
            style={{ opacity: pager.offset === 0 ? 0.4 : 1 }}
          >
            <IoChevronBack />
          </button>
          <button
            type="button"
            className="icon-btn"
            aria-label="Next page"
            disabled={pager.offset + pager.limit >= pager.total}
            onClick={() => onPage(pager.offset + pager.limit)}
            style={{ opacity: pager.offset + pager.limit >= pager.total ? 0.4 : 1 }}
          >
            <IoChevronForward />
          </button>
        </div>
      )}
    </div>
  );
}
