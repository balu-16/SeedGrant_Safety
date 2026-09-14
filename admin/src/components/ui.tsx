/* Web port of the app's hand-rolled design system (client/src/components/ui.tsx):
   same palette, card language, gradient pill buttons, Ionicons glyphs. */

import {
  type ButtonHTMLAttributes,
  type CSSProperties,
  type InputHTMLAttributes,
  type ReactNode,
  useEffect,
  useState,
} from "react";
import {
  IoClose,
  IoEyeOffOutline,
  IoEyeOutline,
  IoHeart,
  IoShield,
} from "react-icons/io5";
import type { IconType } from "react-icons";

export function Icon({
  icon: Glyph,
  size = 22,
  color = "var(--blue)",
}: {
  icon: IconType;
  size?: number;
  color?: string;
}) {
  return <Glyph size={size} color={color} aria-hidden />;
}

export function Btn({
  title,
  onClick,
  secondary = false,
  danger = false,
  ghostDanger = false,
  loading = false,
  icon: Glyph,
  small = false,
  disabled = false,
  type = "button",
}: {
  title: string;
  onClick?: () => void;
  secondary?: boolean;
  danger?: boolean;
  ghostDanger?: boolean;
  loading?: boolean;
  icon?: IconType;
  small?: boolean;
  disabled?: boolean;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
}) {
  const cls = [
    "btn",
    secondary ? "secondary" : "",
    danger ? "danger" : "",
    ghostDanger ? "ghost-danger" : "",
    small ? "small" : "",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type={type}
      className={cls}
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={title}
    >
      {loading ? (
        <Spinner small />
      ) : (
        <span className="row" style={{ gap: 9 }}>
          {Glyph && (
            <Icon icon={Glyph} size={18} color={ghostDanger ? "var(--red)" : "currentColor"} />
          )}
          {title}
        </span>
      )}
    </button>
  );
}

export function Card({
  children,
  className = "",
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div className={`card ${className}`.trim()} style={style}>
      {children}
    </div>
  );
}

export function BadgeIcon({
  icon: Glyph,
  color = "var(--blue)",
  size = 29,
}: {
  icon: IconType;
  color?: string;
  size?: number;
}) {
  return (
    <div className="badge-icon">
      <Icon icon={Glyph} size={size} color={color} />
    </div>
  );
}

export function Field({
  icon: Glyph,
  error,
  password = false,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  icon: IconType;
  error?: string;
  password?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div className={`field${error ? " err" : ""}`}>
        <Icon icon={Glyph} color="var(--muted)" />
        <input
          {...props}
          type={password && !visible ? "password" : (props.type ?? "text")}
          aria-label={props.placeholder}
        />
        {password && (
          <button
            type="button"
            className="icon-btn"
            aria-label={visible ? "Hide password" : "Show password"}
            onClick={() => setVisible((v) => !v)}
          >
            <Icon icon={visible ? IoEyeOutline : IoEyeOffOutline} color="var(--muted)" />
          </button>
        )}
      </div>
      {error && (
        <span className="error-text" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export function Toggle({
  title,
  subtitle,
  checked,
  onChange,
}: {
  title: string;
  subtitle?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="row" style={{ padding: "8px 0" }}>
      <div style={{ flex: 1 }}>
        <div className="bold">{title}</div>
        {subtitle && <div className="muted">{subtitle}</div>}
      </div>
      <label className="switch">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          aria-label={title}
        />
        <span className="slider" />
      </label>
    </div>
  );
}

export function Avatar({ name, size = 43 }: { name: string; size?: number }) {
  return (
    <div
      className="avatar"
      style={{ width: size, height: size, fontSize: size / 3 }}
      aria-hidden
    >
      {name
        .split(" ")
        .map((p) => p[0])
        .filter(Boolean)
        .slice(0, 2)
        .join("")
        .toUpperCase()}
    </div>
  );
}

export function Modal({
  title,
  onClose,
  children,
  width,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  width?: number;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      className="scrim"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="modal-card" style={width ? { maxWidth: width } : undefined}>
        <div className="row">
          <h2 className="heading" style={{ flex: 1 }}>
            {title}
          </h2>
          <button type="button" className="icon-btn" aria-label="Close dialog" onClick={onClose}>
            <Icon icon={IoClose} color="var(--muted)" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Drawer({
  title,
  subtitle,
  onClose,
  children,
}: {
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="drawer" role="dialog" aria-modal="true" aria-label={title}>
      <div className="drawer-head">
        <div style={{ flex: 1 }}>
          <h2 className="heading">{title}</h2>
          {subtitle && <div className="muted">{subtitle}</div>}
        </div>
        <button type="button" className="icon-btn" aria-label="Close panel" onClick={onClose}>
          <Icon icon={IoClose} color="var(--muted)" size={26} />
        </button>
      </div>
      <div className="drawer-body">{children}</div>
    </div>
  );
}

export function Spinner({ small = false }: { small?: boolean }) {
  return (
    <span
      className="spinner"
      style={small ? { width: 18, height: 18, margin: 0, borderWidth: 2.5 } : undefined}
      role="status"
      aria-label="Loading"
    />
  );
}

export function EmptyState({
  icon: Glyph,
  title,
  hint,
}: {
  icon: IconType;
  title: string;
  hint?: string;
}) {
  return (
    <div className="empty">
      <BadgeIcon icon={Glyph} />
      <div className="bold">{title}</div>
      {hint && <div className="muted">{hint}</div>}
    </div>
  );
}

export function Chip({
  tone = "gray",
  children,
}: {
  tone?: "blue" | "green" | "red" | "amber" | "gray";
  children: ReactNode;
}) {
  return <span className={`chip ${tone}`}>{children}</span>;
}

export function Brand({ tagline = true }: { tagline?: boolean }) {
  return (
    <div className="brand">
      <div style={{ position: "relative", width: 44, height: 44 }}>
        <IoShield size={44} color="var(--blue)" aria-hidden />
        <div style={{ position: "absolute", top: 12, left: 11 }}>
          <IoHeart size={22} color="white" aria-hidden />
        </div>
      </div>
      <div>
        <div className="name">
          Smart <span>Safety Tag</span>
        </div>
        {tagline && <div className="tag">Admin portal</div>}
      </div>
    </div>
  );
}

export function Toast({
  message,
  onDone,
}: {
  message: { text: string; error: boolean } | null;
  onDone: () => void;
}) {
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(onDone, 3200);
    return () => clearTimeout(t);
  }, [message, onDone]);
  if (!message) return null;
  return (
    <div className={`toast${message.error ? " error" : ""}`} role="status">
      {message.text}
    </div>
  );
}
