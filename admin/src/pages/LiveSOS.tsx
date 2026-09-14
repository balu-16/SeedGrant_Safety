/* Live SOS monitor: realtime WS feed with sound, inline Ack/Resolve. */

import { useState } from "react";
import {
  IoCheckmarkDone,
  IoHandLeft,
  IoNotificationsOff,
  IoNotificationsOutline,
  IoPulse,
} from "react-icons/io5";
import { Btn, Card, Chip, EmptyState, Toast } from "../components/ui";
import * as api from "../api/services";
import { useSosFeed } from "../hooks/useSosFeed";
import { STATUS_LABELS, TRIGGER_LABELS, fmtTime, fmtDateTime, shortId } from "../lib/format";

function tone(status: string): "red" | "amber" | "green" | "gray" {
  if (status === "active") return "red";
  if (status === "acknowledged") return "amber";
  if (status === "resolved") return "green";
  return "gray";
}

export default function LiveSOS() {
  const { open, feed, connected, soundOn, setSoundOn, refresh } = useSosFeed();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null);

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      setToast({ text: ok, error: false });
      await refresh();
    } catch (err) {
      setToast({ text: err instanceof Error ? err.message : "Action failed", error: true });
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <div className="spread">
        <div className="row">
          <Chip tone={connected ? "green" : "amber"}>
            {connected ? "Realtime connected" : "Connecting…"}
          </Chip>
          <Chip tone={soundOn ? "blue" : "gray"}>
            {soundOn ? "Sound on" : "Sound off"}
          </Chip>
        </div>
        <Btn
          small
          secondary
          title={soundOn ? "Mute alert sound" : "Enable alert sound"}
          icon={soundOn ? IoNotificationsOutline : IoNotificationsOff}
          onClick={() => setSoundOn(!soundOn)}
        />
      </div>

      {open.length > 0 && (
        <div className="sos-banner" role="alert">
          <IoPulse size={26} aria-hidden />
          <span style={{ flex: 1 }}>
            {open.length} open {open.length === 1 ? "emergency" : "emergencies"}
          </span>
        </div>
      )}

      <Card>
        <div className="card-title" style={{ marginBottom: 12 }}>
          Open incidents
        </div>
        {open.length === 0 ? (
          <EmptyState
            icon={IoPulse}
            title="All quiet"
            hint="New emergencies appear here instantly via WebSocket"
          />
        ) : (
          <div className="stack">
            {open.map((e) => (
              <div key={e.id} className="card" style={{ boxShadow: "none", border: "1px solid var(--border)" }}>
                <div className="spread">
                  <div className="row">
                    <Chip tone={tone(e.status)}>{STATUS_LABELS[e.status] ?? e.status}</Chip>
                    <div>
                      <div className="bold">
                        {e.protected_email ?? shortId(e.protected_user_id)} ·{" "}
                        {TRIGGER_LABELS[e.trigger_type] ?? e.trigger_type}
                      </div>
                      <div className="muted" style={{ fontSize: 13 }}>
                        {fmtDateTime(e.created_at)}
                        {e.latitude !== null
                          ? ` · ${e.latitude.toFixed(4)}, ${e.longitude?.toFixed(4)}`
                          : ""}
                      </div>
                    </div>
                  </div>
                  <div className="row">
                    {e.status === "active" && (
                      <Btn
                        small
                        secondary
                        title="Acknowledge"
                        icon={IoHandLeft}
                        loading={busyId === e.id}
                        onClick={async () => {
                          setBusyId(e.id);
                          await act(() => api.ackEmergency(e.id), "Acknowledged");
                        }}
                      />
                    )}
                    <Btn
                      small
                      title="Resolve"
                      icon={IoCheckmarkDone}
                      loading={busyId === e.id}
                      onClick={async () => {
                        setBusyId(e.id);
                        await act(() => api.resolveEmergency(e.id), "Resolved");
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <div className="card-title" style={{ marginBottom: 12 }}>
          Event stream
        </div>
        {feed.length === 0 ? (
          <div className="muted">
            Live events (created / status changes) stream in here as they happen.
          </div>
        ) : (
          <div className="stack">
            {feed.map((ev, i) => (
              <div key={`${ev.emergency.id}-${ev.type}-${i}`} className="spread">
                <span className="row" style={{ gap: 9 }}>
                  <Chip tone={ev.type === "emergency-created" ? "red" : "blue"}>
                    {ev.type === "emergency-created" ? "NEW SOS" : "UPDATE"}
                  </Chip>
                  <span className="bold">{shortId(ev.emergency.id)}</span>
                  <span className="muted">
                    {TRIGGER_LABELS[ev.emergency.trigger_type] ?? ev.emergency.trigger_type} ·{" "}
                    {STATUS_LABELS[ev.emergency.status] ?? ev.emergency.status}
                  </span>
                </span>
                <span className="muted">{fmtTime(ev.at)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Toast message={toast} onDone={() => setToast(null)} />
    </>
  );
}
