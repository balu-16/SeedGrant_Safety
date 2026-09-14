/* App shell: white sidebar (app nav language) + topbar + routed content. */

import { type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  IoAlertCircle,
  IoAnalytics,
  IoHeartCircle,
  IoLocation,
  IoLogOut,
  IoNotifications,
  IoPeople,
  IoPulse,
  IoRadio,
  IoServer,
  IoShieldCheckmark,
} from "react-icons/io5";
import { Avatar } from "./ui";
import { useAuth } from "../auth/AuthContext";
import { useSosFeed } from "../hooks/useSosFeed";

const NAV: { to: string; label: string; icon: typeof IoPulse; end?: boolean }[] = [
  { to: "/", label: "Dashboard", icon: IoAnalytics, end: true },
  { to: "/live-sos", label: "Live SOS", icon: IoPulse },
  { to: "/users", label: "Users", icon: IoPeople },
  { to: "/devices", label: "Devices", icon: IoRadio },
  { to: "/guardians", label: "Guardians", icon: IoHeartCircle },
  { to: "/emergencies", label: "Emergencies", icon: IoAlertCircle },
  { to: "/locations", label: "Locations", icon: IoLocation },
  { to: "/push", label: "Push & Broadcast", icon: IoNotifications },
  { to: "/audit", label: "Audit Log", icon: IoShieldCheckmark },
  { to: "/system", label: "System", icon: IoServer },
];

const TITLES: Record<string, { title: string; sub: string }> = {
  "/": { title: "Dashboard", sub: "Platform overview at a glance" },
  "/live-sos": { title: "Live SOS Monitor", sub: "Real-time emergency feed" },
  "/users": { title: "Users", sub: "Full control over every account" },
  "/devices": { title: "Devices", sub: "All paired safety tags" },
  "/guardians": { title: "Guardians", sub: "Every safety-circle link" },
  "/emergencies": { title: "Emergencies", sub: "All incidents and their timelines" },
  "/locations": { title: "Locations", sub: "Location history on the map" },
  "/push": { title: "Push & Broadcast", sub: "Send notifications to users" },
  "/audit": { title: "Audit Log", sub: "Every admin action, recorded" },
  "/system": { title: "System", sub: "Platform health and session" },
};

export function Layout({ children }: { children?: ReactNode }) {
  const { admin, logout } = useAuth();
  const { open } = useSosFeed();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const head = TITLES[pathname] ?? { title: "Admin", sub: "" };

  return (
    <div className="shell">
      <nav className="sidebar" aria-label="Admin navigation">
        <NavLink to="/" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="brand">
            <div style={{ position: "relative", width: 40, height: 40 }}>
              <IoHeartCircle size={40} color="var(--blue)" aria-hidden />
            </div>
            <div>
              <div className="name">
                Smart <span>Safety Tag</span>
              </div>
              <div className="tag">Admin portal</div>
            </div>
          </div>
        </NavLink>
        {NAV.map(({ to, label, icon: Glyph, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            <Glyph size={21} aria-hidden />
            {label}
            {to === "/live-sos" && open.length > 0 && (
              <span className="nav-alert" aria-label={`${open.length} open emergencies`}>
                {open.length}
              </span>
            )}
          </NavLink>
        ))}
        <div className="sidebar-footer">
          <div className="row">
            <Avatar name={admin?.name ?? "A"} size={36} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                className="bold"
                style={{ fontSize: 14, overflow: "hidden", textOverflow: "ellipsis" }}
              >
                {admin?.name}
              </div>
              <div className="muted" style={{ fontSize: 12 }}>
                Administrator
              </div>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Sign out"
              title="Sign out"
              onClick={async () => {
                await logout();
                navigate("/login");
              }}
            >
              <IoLogOut size={20} />
            </button>
          </div>
        </div>
      </nav>
      <div className="main">
        <header className="topbar">
          <div style={{ flex: 1 }}>
            <h1>{head.title}</h1>
            <div className="sub">{head.sub}</div>
          </div>
        </header>
        <main className="content">{children ?? <Outlet />}</main>
      </div>
    </div>
  );
}
