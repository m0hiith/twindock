// Open alerts from the rules engine, critical first. Shared by every screen: acknowledging here
// shows "acknowledged by …" everywhere. Clicking an alert flies the camera to its source.
import { useState } from "react";
import type { AlertsUpdate } from "../contract";
import { siteAt } from "../sites";
import { send, request } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { navigate } from "./PageTabs";
import { ago, Icon, Pill, useTick } from "./ui";

export type Alert = AlertsUpdate["alerts"][number];
// One shared empty list: a selector returning a fresh [] each call would re-render forever.
const NO_ALERTS: Alert[] = [];
const TONE = { critical: "crit", warning: "warn", info: "info" } as const;

/** Who is acknowledging, as everyone will see it (there is no sign-in on this demo). */
export function screenName(): string {
  const page = location.pathname.startsWith("/monitor") ? "Monitoring centre" : location.pathname.startsWith("/control") ? "Control Room" : location.pathname.startsWith("/rules") ? "Rules page" : "Twin";
  return innerWidth < 640 ? `${page} (phone)` : page;
}

/** Switch to the alert's site, select its unit or device and fly the camera there. */
export function flyTo(a: Alert, stay = false): void {
  const t = a.target;
  if (t.x === undefined || t.z === undefined) return;
  const v = useView.getState();
  const site = t.site_id ?? siteAt(useWorld.getState().sites, t.x, t.z);
  if (site && site !== v.site && !stay) v.setSite(site);
  const id = t.unit_id ?? t.device_id;
  if (id) send({ type: "select_unit", unit_id: id });
  if (t.device_id && !t.unit_id) v.setShowDevices(true);
  v.focusOn(t.x, t.z);
  if (!stay && !location.pathname.startsWith("/twin")) navigate("/twin");
}

export function AlertRow({ a, compact = false, stay = false }: { a: Alert; compact?: boolean; stay?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const ack = async () => {
    setBusy(true);
    setErr(null);
    const r = await request({ type: "ack_alert", alert_id: a.id, by: screenName() }).ack;
    setBusy(false);
    if (r.type === "local_failure") setErr(r.reason);
    else if (!r.ok) setErr(r.reason ?? "Rejected");
  };
  return (
    <div className="flex items-start gap-2.5 py-2">
      <button type="button" onClick={() => flyTo(a, stay)} className="min-w-0 flex-1 text-left" title="Show in the twin">
        <div className="flex items-center gap-2">
          <Pill tone={a.state === "resolved" ? "idle" : TONE[a.severity]}>{a.state === "resolved" ? "Resolved" : a.severity === "critical" ? "Critical" : a.severity === "warning" ? "Warning" : "Info"}</Pill>
          <span className="truncate text-[12px] text-ink-2">{a.title} · {ago(a.raised_ms)}</span>
        </div>
        <div className={`mt-0.5 ${compact ? "line-clamp-2" : ""} text-[13px] text-ink`}>{a.message}</div>
        {a.acknowledged_by && <div className="text-[12px] text-ink-2">Acknowledged by {a.acknowledged_by}{a.acknowledged_ms ? ` · ${ago(a.acknowledged_ms)}` : ""}</div>}
        {err && <div className="text-[12px] text-crit">{err}</div>}
      </button>
      {a.state === "raised" && (
        <button type="button" disabled={busy} onClick={() => void ack()}
          className="h-8 shrink-0 rounded-lg border border-[var(--card-border)] px-2.5 text-[12px] font-medium hover:bg-idle-bg disabled:opacity-50">
          {busy ? "…" : "Acknowledge"}
        </button>
      )}
    </div>
  );
}

/** Compact floating card for /twin. Collapses to a pill when nothing is open. */
/** `collapsed`: start folded (an inspect card is open above); a click still opens it. */
export function AlertsCard({ collapsed = false }: { collapsed?: boolean }) {
  const alerts = useWorld((s) => s.alerts?.alerts ?? NO_ALERTS);
  const [choice, setChoice] = useState<{ open: boolean; when: boolean } | null>(null);
  // The person's last click wins until `collapsed` changes (a new inspect card opens or closes).
  const open = choice && choice.when === collapsed ? choice.open : !collapsed;
  const setOpen = (v: boolean) => setChoice({ open: v, when: collapsed });
  useTick(5000);
  const active = alerts.filter((a) => a.state !== "resolved");
  const crit = active.filter((a) => a.severity === "critical").length;
  if (active.length === 0) {
    return (
      <button type="button" data-tour="alerts" onClick={() => navigate("/rules")} className="card pointer-events-auto flex items-center gap-2 px-3 py-2 text-[13px] text-ink-2">
        <Icon name="check" className="text-ok" /> No open alerts
      </button>
    );
  }
  return (
    <div className="card pointer-events-auto w-[340px] overflow-hidden" aria-label="Open alerts" data-tour="alerts">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
        className="flex w-full items-center gap-2 border-b border-[var(--card-border)] px-4 py-2.5 text-left">
        <Icon name="alert" size={16} className={crit ? "text-crit" : "text-warn"} />
        <span className="font-semibold">{active.length} open alert{active.length > 1 ? "s" : ""}</span>
        {crit > 0 && <span className="text-[12px] font-medium text-crit">{crit} critical</span>}
        <Icon name={open ? "chevronDown" : "chevronRight"} size={14} className="ml-auto text-ink-2" />
      </button>
      {open && (
        <div className="max-h-[260px] divide-y divide-[var(--card-border)] overflow-y-auto px-4">
          {active.map((a) => <AlertRow key={a.id} a={a} compact />)}
        </div>
      )}
    </div>
  );
}

/** Full list for /control (phone): open first, then recently resolved. */
export function AlertsList() {
  const alerts = useWorld((s) => s.alerts?.alerts ?? NO_ALERTS);
  useTick(5000);
  const active = alerts.filter((a) => a.state !== "resolved");
  const done = alerts.filter((a) => a.state === "resolved").slice(0, 10);
  return (
    <div className="flex flex-col gap-3">
      <div className="card px-4">
        {active.length === 0 && <div className="py-4 text-center text-ink-2">No open alerts</div>}
        <div className="divide-y divide-[var(--card-border)]">{active.map((a) => <AlertRow key={a.id} a={a} />)}</div>
      </div>
      {done.length > 0 && (
        <>
          <div className="px-1 text-[12px] font-medium text-ink-2">Recently resolved</div>
          <div className="card divide-y divide-[var(--card-border)] px-4">{done.map((a) => <AlertRow key={a.id} a={a} compact />)}</div>
        </>
      )}
      <button type="button" onClick={() => navigate("/rules")} className="text-[13px] text-ink-2 underline">All rules in plain language</button>
    </div>
  );
}
