// FAC-01 line controls on /control (phone-friendly). "Degrade" injects a slowly rising vibration
// on one machine through the simulator so the abnormal-vibration flag can be shown on cue.
// These are simulation controls: they only ever reach tools/site_sim.py, never the real board.
import { useState } from "react";
import type { ProductionUpdate } from "../contract";
import { ago, Pill, SimBadge, useTick } from "../hud/ui";
import { stateLabel, toneOf } from "../status";
import { request } from "../store/ws";
import { useWorld } from "../store/world";

type Machine = ProductionUpdate["machines"][number];
type Action = "degrade" | "restore" | "maintenance";

function MachineCard({ m, z }: { m: Machine; z: number }) {
  const [busy, setBusy] = useState<Action | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const run = async (action: Action) => {
    setBusy(action);
    setNote(null);
    const r = await request({ type: "machine_command", machine_id: m.id, action }).ack;
    setBusy(null);
    if (r.type === "local_failure" || !r.ok) setNote(r.type === "local_failure" ? r.reason : r.reason ?? "Rejected");
    else setNote(action === "degrade" ? "Vibration will rise slowly; watch z climb past the threshold." : action === "restore" ? "Vibration back to normal." : "Maintenance for 30 s.");
  };
  const btn = "h-9 flex-1 rounded-xl border border-[var(--card-border)] text-[13px] font-medium hover:bg-idle-bg disabled:opacity-50";
  return (
    <div className="card flex flex-col gap-2 p-3">
      <div className="flex items-center gap-2">
        <span className="font-semibold">{m.id} {m.label}</span>
        <SimBadge />
        <span className="ml-auto"><Pill tone={toneOf({ kind: "machine", state: m.state })}>{stateLabel(m.state)}</Pill></span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[12px]">
        <div><div className="text-ink-2">Vibration</div><div className={`tabular text-[15px] font-semibold ${m.abnormal ? "text-warn" : ""}`}>{m.vibration_rms?.toFixed(2) ?? "—"}<span className="text-[11px] font-normal text-ink-2"> mm/s</span></div></div>
        <div><div className="text-ink-2">z vs baseline</div><div className={`tabular text-[15px] font-semibold ${m.abnormal ? "text-warn" : ""}`}>{m.z?.toFixed(1) ?? "—"}<span className="text-[11px] font-normal text-ink-2"> / {z}</span></div></div>
        <div><div className="text-ink-2">Units today</div><div className="tabular text-[15px] font-semibold">{m.units_today}</div></div>
      </div>
      <div className="text-[12px] text-ink-2">
        {m.baseline.learned ? `Baseline learned from ${m.baseline.samples} readings` : `Learning baseline (${m.baseline.samples} readings)`}
        {m.data_ms ? ` · data ${ago(m.data_ms)}` : " · no data yet"}
      </div>
      {m.abnormal && <div className="rounded-lg bg-warn-bg px-2.5 py-1.5 text-[12px] text-warn">Abnormal vibration compared with baseline. Not a failure prediction.</div>}
      <div className="flex gap-2">
        <button type="button" className={btn} disabled={busy !== null} onClick={() => void run("degrade")}>{busy === "degrade" ? "Sending…" : "Degrade"}</button>
        <button type="button" className={btn} disabled={busy !== null} onClick={() => void run("restore")}>{busy === "restore" ? "Sending…" : "Restore"}</button>
        <button type="button" className={btn} disabled={busy !== null} onClick={() => void run("maintenance")}>{busy === "maintenance" ? "Sending…" : "Maintenance"}</button>
      </div>
      {note && <div className="text-[12px] text-ink-2">{note}</div>}
    </div>
  );
}

export function ProductionPanel() {
  const p = useWorld((s) => s.production);
  useTick(1000);
  if (!p) return <div className="py-6 text-center text-ink-2">Waiting for the server…</div>;
  return (
    <div className="flex flex-col gap-3">
      <div className="text-[12px] text-ink-2">
        FAC-01 line. Every value comes from simulated machine monitors (tools/site_sim.py). These buttons only
        talk to the simulator, never to the real board.
      </div>
      {p.machines.map((m) => <MachineCard key={m.id} m={m} z={p.config.z_threshold} />)}
      <div className="card grid grid-cols-3 gap-2 p-3 text-[12px]">
        <div><div className="text-ink-2">Line units</div><div className="tabular text-[15px] font-semibold">{p.line.units_today}</div></div>
        <div><div className="text-ink-2">Pallets out</div><div className="tabular text-[15px] font-semibold">{p.line.pallets_made}</div></div>
        <div><div className="text-ink-2">OEE</div><div className="tabular text-[15px] font-semibold">{p.line.oee === null ? "—" : `${Math.round(p.line.oee * 100)}%`}</div></div>
      </div>
    </div>
  );
}
