/* Dashboard: KPIs, 30-day charts, recent emergencies, health strip. */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  IoAlertCircle,
  IoHeartCircle,
  IoPeople,
  IoPulse,
  IoRadio,
} from "react-icons/io5";
import { BadgeIcon, Card, Chip, Spinner } from "../components/ui";
import { listEmergencies, stats } from "../api/services";
import type { AdminStats, Emergency } from "../api/types";
import { STATUS_LABELS, TRIGGER_LABELS, fmtRelative } from "../lib/format";
import { useSosFeed } from "../hooks/useSosFeed";

function Kpi({
  icon,
  label,
  value,
  color = "var(--blue)",
  tone,
}: {
  icon: typeof IoPeople;
  label: string;
  value: number | string;
  color?: string;
  tone?: "red" | "green";
}) {
  return (
    <Card className="kpi">
      <BadgeIcon icon={icon} color={color} />
      <div>
        <div className="num" style={{ color: tone === "red" ? "var(--red)" : undefined }}>
          {value}
        </div>
        <div className="label">{label}</div>
      </div>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<AdminStats | null>(null);
  const [recent, setRecent] = useState<Emergency[]>([]);
  const [error, setError] = useState("");
  const { open } = useSosFeed();

  const load = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([stats(), listEmergencies({ limit: 6 })]);
      setData(s);
      setRecent(e.items);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (!data) return error ? <Card>{error}</Card> : <Spinner />;

  const t = data.totals;
  const openCount = open.length > 0 ? open.length : t.emergencies_open;

  return (
    <>
      {error && <Card>{error}</Card>}

      {openCount > 0 && (
        <div className="sos-banner" role="alert">
          <IoPulse size={26} aria-hidden />
          <span style={{ flex: 1 }}>
            {openCount} open {openCount === 1 ? "emergency" : "emergencies"} right now
          </span>
          <Link to="/live-sos" style={{ color: "white" }}>
            <button type="button" className="btn small" style={{ background: "rgba(255,255,255,.22)" }}>
              Open Live SOS
            </button>
          </Link>
        </div>
      )}

      <div className="kpi-grid">
        <Kpi icon={IoPeople} label="Total users" value={t.users_total} />
        <Kpi
          icon={IoRadio}
          label="Devices online"
          value={`${t.devices_online}/${t.devices_total}`}
          color="var(--green)"
        />
        <Kpi
          icon={IoAlertCircle}
          label="Open emergencies"
          value={openCount}
          color="var(--red)"
          tone={openCount > 0 ? "red" : undefined}
        />
        <Kpi icon={IoHeartCircle} label="Guardian links" value={t.guardians_accepted} />
      </div>

      <div className="grid-2">
        <Card>
          <div className="card-title" style={{ marginBottom: 12 }}>
            <BadgeIcon icon={IoPeople} size={22} />
            Signups — last 30 days
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.series} margin={{ top: 4, right: 6, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="gSignups" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0875FF" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#0875FF" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#E7F1FF" vertical={false} />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 11, fill: "#667691" }}
                tickFormatter={(d: string) => d.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 11, fill: "#667691" }} allowDecimals={false} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="signups"
                stroke="#0875FF"
                strokeWidth={2.5}
                fill="url(#gSignups)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <div className="card-title" style={{ marginBottom: 12 }}>
            <BadgeIcon icon={IoAlertCircle} size={22} color="var(--red)" />
            Emergencies — last 30 days
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.series} margin={{ top: 4, right: 6, left: -22, bottom: 0 }}>
              <CartesianGrid stroke="#E7F1FF" vertical={false} />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 11, fill: "#667691" }}
                tickFormatter={(d: string) => d.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 11, fill: "#667691" }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="emergencies" fill="#EB493D" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card>
        <div className="spread" style={{ marginBottom: 8 }}>
          <div className="card-title">
            <BadgeIcon icon={IoPulse} size={22} color="var(--red)" />
            Recent emergencies
          </div>
          <Link to="/emergencies">View all</Link>
        </div>
        {recent.length === 0 ? (
          <div className="muted">No emergencies recorded.</div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Trigger</th>
                  <th>Status</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((e) => (
                  <tr key={e.id}>
                    <td className="bold">{e.protected_email ?? e.protected_user_id.slice(0, 8)}</td>
                    <td>{TRIGGER_LABELS[e.trigger_type] ?? e.trigger_type}</td>
                    <td>
                      <Chip
                        tone={
                          e.status === "active"
                            ? "red"
                            : e.status === "acknowledged"
                              ? "amber"
                              : "green"
                        }
                      >
                        {STATUS_LABELS[e.status] ?? e.status}
                      </Chip>
                    </td>
                    <td className="muted">{fmtRelative(e.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
