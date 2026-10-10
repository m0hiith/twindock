// Inspect-card rows for a worker: role, badge, zone, proximity. No name (see PRIVACY_NOTE).
import type { Unit } from "../contract";
import { zoneName } from "../fleet/format";
import { useWorld } from "../store/world";
import { PRIVACY_NOTE } from "./SafetyPanel";
import { ago, SimBadge } from "./ui";

export function WorkerRows({ u }: { u: Unit }) {
  const w = useWorld((s) => s.safety?.workers.find((x) => x.id === u.id));
  const sites = useWorld((s) => s.sites);
  const row = (k: string, v: React.ReactNode) => (
    <div className="flex items-center justify-between gap-3 py-1.5 text-[13px]"><span className="text-ink-2">{k}</span><span className="font-medium">{v}</span></div>
  );
  return (
    <>
      {row("Role", String(u.meta?.role ?? "—").replace(/_/g, " "))}
      {row("Name", <span className="text-ink-2">Hidden (authorised users only)</span>)}
      {row("Badge", <span className="inline-flex items-center gap-1.5">{String(u.meta?.badge ?? "—")} <SimBadge /></span>)}
      {row("Zone", w?.zone_id ? zoneName(sites, w.zone_id) : "—")}
      {row("Nearest moving forklift", w?.near ? `${w.near.forklift}, ${w.near.distance_m.toFixed(1)} m (${w.near.level})` : "None nearby")}
      {row("Position age", w?.data_ms ? ago(w.data_ms) : "never")}
      <div className="py-1.5 text-[11px] leading-snug text-ink-2">{PRIVACY_NOTE}</div>
    </>
  );
}
