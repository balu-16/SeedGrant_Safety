/* Admin login — mirrors the app's login screen (Brand + gradient button + waves). */

import { type FormEvent, useState } from "react";
import { IoCall, IoLockClosed, IoMail, IoShieldCheckmark } from "react-icons/io5";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Brand, Btn, Card, Field, Icon } from "../components/ui";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Enter your email and password");
      return;
    }
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <svg className="waves-svg" viewBox="0 0 1440 500" preserveAspectRatio="none" aria-hidden>
        <path
          d="M0 260 Q220 130 480 240 T960 250 T1440 210 V500 H0Z"
          fill="#EAF3FF"
        />
        <path
          d="M0 360 Q240 250 520 340 T1050 330 T1440 300 V500 H0Z"
          fill="#D8EAFE"
        />
      </svg>
      <Card className="login-card">
        <Brand />
        <div style={{ textAlign: "center", marginBottom: 4 }}>
          <div className="bold" style={{ fontSize: 19 }}>
            Admin sign in
          </div>
          <div className="muted">Admins only — every action is audited</div>
        </div>
        <form onSubmit={submit} className="stack">
          <Field
            icon={IoMail}
            placeholder="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Field
            icon={IoLockClosed}
            placeholder="Password"
            password
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && (
            <span className="error-text" role="alert">
              {error}
            </span>
          )}
          <Btn title="Sign in" type="submit" loading={busy} icon={IoShieldCheckmark} />
        </form>
        <div className="row" style={{ justifyContent: "center", gap: 8 }}>
          <Icon icon={IoCall} size={15} color="var(--muted)" />
          <span className="muted" style={{ fontSize: 13 }}>
            Accounts are promoted by the platform owner.
          </span>
        </div>
      </Card>
    </div>
  );
}
