// Confirm step: the server's planned path is on the map; nothing moves until Confirm.
import { useState } from "react";
import { Icon, nodeLabel } from "../hud/ui";
import { useWorld } from "../store/world";
import { actionVerb, useControl } from "./state";

function pathLength(fromX: number, fromZ: number, path: string[]): number {
  const nodes = useWorld.getState().layout?.nodes ?? [];
  let d = 0, x = fromX, z = fromZ;
  for (const id of path) {
    const n = nodes.find((q) => q.id === id);
    if (!n) continue;
    d += Math.hypot(n.x - x, n.z - z);
    x = n.x; z = n.z;
  }
  return d;
}

export function ProposalSheet() {
  const p = useControl((s) => s.proposal);
  const notice = useControl((s) => s.notice);
  const unit = useWorld((s) => (p ? s.units[p.unit_id] : undefined));
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);
  const { propose, run, setNotice } = useControl.getState();

  if (notice) {
    return (
      <div className="card flex items-center gap-3 border-warn/40 px-4 py-3" role="alert">
        <span className="h-2 w-2 shrink-0 rounded-full bg-warn" />
        <span className="flex-1 text-ink">{notice.text}</span>
        <button type="button" aria-label="Dismiss" onClick={() => setNotice(null)} className="grid h-8 w-8 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="close" size={14} /></button>
      </div>
    );
  }
  if (result && !p) {
    return (
      <div className="card flex items-center gap-3 px-4 py-3" role="status">
        <span className={`h-2 w-2 shrink-0 rounded-full ${result.ok ? "bg-ok" : "bg-crit"}`} />
        <span className="flex-1">{result.text}</span>
        <button type="button" aria-label="Dismiss" onClick={() => setResult(null)} className="grid h-8 w-8 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="close" size={14} /></button>
      </div>
    );
  }
  if (!p || !unit) return null;

  const where = nodeLabel(p.target);
  const what = p.pallet_id ? `Pick ${p.pallet_id} at ${where}` : `${actionVerb[p.action]} ${where}`;
  const metres = p.path ? Math.round(pathLength(unit.x, unit.z, p.path)) : 0;
  const confirm = async () => {
    setBusy(true);
    const a = await run({ type: "move_unit", unit_id: p.unit_id, target_node: p.target, action: p.action, ...(p.pallet_id ? { pallet_id: p.pallet_id } : {}) }, `${p.unit_id}: ${what}`);
    setBusy(false);
    propose(null);
    setResult(a.type === "local_failure" ? { ok: false, text: `Not delivered: ${a.reason}` }
      : { ok: a.ok, text: a.ok ? `${p.unit_id} accepted: ${what}` : `Rejected: ${a.reason ?? "no reason given"}` });
  };

  return (
    <div className="card px-4 py-3" role="dialog" aria-label="Confirm move">
      <div className="text-[12px] text-ink-2">Planned by the server · {p.path ? Math.max(0, p.path.length - 1) : 0} waypoints · {metres} m</div>
      <div className="mt-0.5 text-[15px] font-semibold">{p.unit_id} · {what}</div>
      <div className="mt-3 flex gap-2">
        <button type="button" onClick={() => propose(null)} disabled={busy}
          className="h-11 flex-1 rounded-xl border border-[var(--card-border)] bg-white font-medium text-ink hover:bg-idle-bg">Cancel</button>
        <button type="button" onClick={confirm} disabled={busy}
          className="h-11 flex-[2] rounded-xl bg-accent font-semibold text-white hover:bg-[var(--structure-dark)] disabled:opacity-60">{busy ? "Sending…" : "Confirm move"}</button>
      </div>
    </div>
  );
}
