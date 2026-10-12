// Maintenance and automatic actions (R5): decisions waiting for a person, work orders, and every automatic action
// as cause → action → result. Stopping a machine or calling emergency services happens only after someone approves.
import { useState } from "react";
import type { ControlUpdate } from "../contract";
import { ago, Pill, SimBadge, useTick } from "../hud/ui";
import type { Tone } from "../status";
import { useWorld } from "../store/world";
import { useControl } from "./state";

const WO_TONE: Record<string, Tone> = {
  awaiting_approval: "warn", waiting: "warn", dispatched: "info", in_progress: "info", done: "ok", dismissed: "idle", broke_down: "crit", open: "info",
};
const WO_STATE: Record<string, string> = {
  awaiting_approval: "Needs approval", waiting: "Waiting", dispatched: "Technician on the way", in_progress: "In progress",
  done: "Done", dismissed: "Dismissed", broke_down: "Broke down first", open: "Open",
};
const KIND: Record<string, string> = { bearing: "Bearing change", leak_fix: "Leak fix", compressor_service: "Compressor service" };

function Decision({ r }: { r: ControlUpdate["recommendations"][number] }) {
  const run = useControl((s) => s.run);
  const [busy, setBusy] = useState<"approve" | "dismiss" | null>(null);
  const decide = async (decision: "approve" | "dismiss") => {
    setBusy(decision);
    await run({ type: "control_decision", rec_id: r.id, decision, by: "Control room" }, `${decision === "approve" ? "Approve" : "Dismiss"} ${r.id}`);
    setBusy(null);
  };
  return (
    <div className="rounded-xl border border-warn bg-warn-bg p-3">
      <div className="text-[13px] text-ink">{r.text}</div>
      <div className="mt-2 flex items-center gap-2">
        <button type="button" disabled={busy !== null} onClick={() => void decide("approve")}
          className="h-8 rounded-lg bg-accent px-3 text-[13px] font-medium text-white disabled:opacity-50">
          {busy === "approve" ? "Sending…" : r.kind === "emergency_call" ? "Called" : "Approve"}
        </button>
        <button type="button" disabled={busy !== null} onClick={() => void decide("dismiss")}
          className="h-8 rounded-lg border border-[var(--card-border)] bg-white px-3 text-[13px] font-medium disabled:opacity-50">
          {busy === "dismiss" ? "Sending…" : r.kind === "emergency_call" ? "Not needed" : "Dismiss"}
        </button>
        <span className="ml-auto text-[12px] text-ink-2">{ago(r.created_ms)}</span>
      </div>
    </div>
  );
}

export function MaintenancePanel() {
  const c = useWorld((s) => s.control);
  useTick(5000);
  if (!c) return <div className="p-4 text-ink-2">Waiting for the server…</div>;
  const open = c.work_orders.filter((w) => !["done", "dismissed"].includes(w.state));
  const closed = c.work_orders.filter((w) => ["done", "dismissed"].includes(w.state)).slice(0, 8);
  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        <span className="text-ink-2">Shift report (PDF, from the historian):</span>
        <a className="underline" href="/api/report/shift.pdf?which=current" download>this shift</a>
        <a className="underline" href="/api/report/shift.pdf?which=previous" download>previous shift</a>
      </div>
      <section aria-label="Decisions">
        <div className="flex items-center gap-2"><h2 className="text-[15px] font-semibold">Decisions for a person</h2><SimBadge /></div>
        <p className="mt-0.5 text-[12px] text-ink-2">Anything that stops production or calls emergency services waits here.</p>
        <div className="mt-2 flex flex-col gap-2">
          {c.recommendations.length === 0 && <div className="text-[13px] text-ink-2">Nothing waiting</div>}
          {c.recommendations.map((r) => <Decision key={r.id} r={r} />)}
        </div>
      </section>
      <section aria-label="Work orders">
        <h2 className="text-[15px] font-semibold">Work orders</h2>
        <div className="mt-1 flex flex-wrap gap-3 text-[12px] text-ink-2">
          <span>Leaks at the last break: {c.leak_estimate_nm3_min === null ? "not measured yet" : `${c.leak_estimate_nm3_min.toFixed(2)} Nm³/min`}</span>
          {c.shed && <Pill tone="warn">Non-critical loads shed for peak demand</Pill>}
        </div>
        <div className="mt-2 divide-y divide-[var(--card-border)]">
          {[...open, ...closed].map((w) => (
            <div key={w.id} className="py-2 text-[13px]">
              <div className="flex items-center gap-2">
                <span className="tabular font-semibold">{w.id}</span>
                <span>{KIND[w.kind]} · {w.asset_label}</span>
                <span className="ml-auto"><Pill tone={WO_TONE[w.state] ?? "idle"}>{WO_STATE[w.state] ?? w.state}</Pill></span>
              </div>
              <div className="mt-0.5 text-ink-2">Cause: {w.cause}</div>
              {w.technician && <div className="text-ink-2">Technician {w.technician}{w.started_ms ? ` · started ${ago(w.started_ms)} · job ${Math.round(w.job_s / 60)} min` : ""}</div>}
              {w.result && <div className="text-ink">Result: {w.result}</div>}
            </div>
          ))}
          {c.work_orders.length === 0 && <div className="py-2 text-[13px] text-ink-2">No work orders yet</div>}
        </div>
      </section>
      <section aria-label="Automatic actions">
        <h2 className="text-[15px] font-semibold">Automatic actions</h2>
        <div className="mt-2 divide-y divide-[var(--card-border)]">
          {c.actions.length === 0 && <div className="py-2 text-[13px] text-ink-2">None yet</div>}
          {c.actions.map((a) => (
            <div key={`${a.ts_ms}-${a.action}`} className="py-2 text-[13px]">
              <div className="text-[12px] text-ink-2">{ago(a.ts_ms)}</div>
              <div><span className="text-ink-2">Cause</span> {a.cause}</div>
              <div><span className="text-ink-2">Action</span> {a.action}</div>
              {a.result && <div><span className="text-ink-2">Result</span> {a.result}</div>}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
