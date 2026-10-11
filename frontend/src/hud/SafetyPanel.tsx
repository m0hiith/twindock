// Worker safety on /twin (FAC-01): workers per zone, warnings today, closest approach today, and
// who is near a moving forklift right now. Badges show role and zone only.
import { zoneName } from "../fleet/format";
import { request } from "../store/ws";
import { useWorld } from "../store/world";
import { ago, Icon, Pill, SimBadge, useTick } from "./ui";

export const PRIVACY_NOTE = "Privacy: screens show zone counts. A worker's position appears only during their own alert or an evacuation. No tracking off site or off shift. Roles only, never names. Incident history is kept for the retention period; workers can see their own data.";

export function SafetyPanel({ className = "w-[420px]", onFocusWorker, compact = false }: { className?: string; onFocusWorker?: (id: string) => void; compact?: boolean }) {
  const s = useWorld((x) => x.safety);
  const sites = useWorld((x) => x.sites);
  useTick(1000);
  if (!s) return null;
  const counts = Object.entries(s.zone_counts).filter((e): e is [string, number] => e[1] !== undefined).sort((a, b) => b[1] - a[1]);
  const active = s.workers.filter((w) => w.near || w.restricted_zone || w.prealert || w.man_down || w.sos_ms || w.lone || w.evacuate || w.zone_overtime_min);
  const evac = s.evacuation;
  const t = s.today;
  return (
    <div className={`card pointer-events-auto flex flex-col gap-3 p-4 ${className}`} aria-label="Worker safety">
      <div className="flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-idle-bg"><Icon name="shield" size={16} /></span>
        <span className="text-[15px] font-semibold">Worker safety</span>
        <SimBadge />
        <span className="ml-auto text-[12px] text-ink-2">{s.workers.filter((w) => w.fresh).length}/{s.workers.length} badges online</span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div><div className="text-[12px] text-ink-2">Warnings today</div><div className="tabular text-[20px] font-semibold">{t.warnings}<span className="text-[13px] text-crit">{t.criticals ? ` +${t.criticals} critical` : ""}</span></div></div>
        <div><div className="text-[12px] text-ink-2">Closest approach</div><div className="tabular text-[20px] font-semibold">{t.closest_m === null ? "—" : `${t.closest_m.toFixed(1)} m`}</div>
          {t.closest && <div className="truncate text-[11px] text-ink-2">{t.closest.worker} · {t.closest.forklift} · {ago(t.closest.at_ms)}</div>}</div>
        <div><div className="text-[12px] text-ink-2">Restricted entries</div><div className="tabular text-[20px] font-semibold">{t.restricted}</div></div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {counts.length === 0 && <span className="text-[12px] text-ink-2">No badge positions yet</span>}
        {counts.map(([z, n]) => (
          <span key={z} className="rounded-full bg-idle-bg px-2 py-0.5 text-[12px]"><b className="tabular">{n}</b> in {zoneName(sites, z)}</span>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="rounded-lg bg-idle-bg py-1"><div className="tabular text-[17px] font-semibold">{s.on_site}</div><div className="text-[11px] text-ink-2">on site</div></div>
        <div className="rounded-lg bg-idle-bg py-1"><div className="tabular text-[17px] font-semibold">{s.in_hazardous}</div><div className="text-[11px] text-ink-2">in hazard zones</div></div>
        <div className="rounded-lg bg-idle-bg py-1"><div className="tabular text-[17px] font-semibold">{t.falls}<span className="text-[11px] text-ink-2"> ({t.falls_cancelled} cancelled)</span></div><div className="text-[11px] text-ink-2">falls today</div></div>
        <div className="rounded-lg bg-idle-bg py-1"><div className="tabular text-[17px] font-semibold">{t.sos}</div><div className="text-[11px] text-ink-2">SOS today</div></div>
      </div>
      {(s.gas_zones.length > 0 || Object.keys(s.heat_zones).length > 0) && (
        <div className="flex flex-wrap gap-1.5 text-[12px]">
          {s.gas_zones.map((z) => <Pill key={z} tone="crit">Gas alarm · {zoneName(sites, z)}</Pill>)}
          {Object.entries(s.heat_zones).map(([z, v]) => <Pill key={z} tone="warn">Heat index {v} °C · {zoneName(sites, z)}</Pill>)}
        </div>
      )}
      {active.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {active.map((w) => {
            const where = w.zone_id ? zoneName(sites, w.zone_id) : "a zone";
            const [tone, label, text] = w.sos_ms ? ["crit", "SOS", `${w.id} in ${where}${w.nearest_first_aider ? ` · first-aider ${w.nearest_first_aider.id} ${w.nearest_first_aider.distance_m} m` : ""}`] as const
              : w.man_down ? ["crit", "Man down", `${w.id} in ${where} (${w.man_down === "fall" ? "fall not cancelled" : "no movement"})`] as const
              : w.prealert ? ["warn", "Pre-alert", `${w.id}: ${w.prealert.kind === "fall" ? "possible fall" : "no movement"}, the worker can cancel on the badge`] as const
              : w.evacuate ? ["crit", "Evacuate", `${w.id}: ${w.evacuate}`] as const
              : w.lone ? [w.lone === "critical" ? "crit" : "warn", "Check-in", `${w.id} alone, check-in ${w.lone === "critical" ? "missed" : "overdue"}`] as const
              : w.zone_overtime_min ? ["warn", "Time limit", `${w.id} is ${w.zone_overtime_min.toFixed(0)} min over the limit in ${where}`] as const
              : w.restricted_zone ? ["crit", "Restricted", `${w.id} in ${zoneName(sites, w.restricted_zone)}`] as const
              : [w.near?.level === "critical" ? "crit" : "warn", w.near?.level === "critical" ? "Critical" : "Warning",
                 `${w.id} ${w.near!.distance_m.toFixed(1)} m from moving ${w.near!.forklift}${w.near!.reversing ? " (reversing)" : ""}`] as const;
            return (
              <div key={w.id} className="flex items-center gap-2 text-[13px]">
                <Pill tone={tone}>{label}</Pill>
                <button type="button" className="min-w-0 flex-1 truncate text-left" title="Show on the map" onClick={() => onFocusWorker?.(w.id)}>{text}</button>
                {(w.sos_ms || w.man_down) && (
                  <button type="button" className="rounded-lg border border-[var(--card-border)] px-2 py-0.5 text-[12px] hover:bg-idle-bg"
                    onClick={() => void request({ type: "safety_command", action: "clear_incident", worker_id: w.id, by: "Twin" })}>Close</button>
                )}
              </div>
            );
          })}
        </div>
      )}
      <div className="rounded-xl border border-[var(--card-border)] p-3">
        {evac ? (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2"><Pill tone="crit">Evacuation</Pill><span className="text-[13px]">{evac.reason}</span>
              <button type="button" className="ml-auto rounded-lg bg-ink px-2.5 py-1 text-[12px] font-medium text-white" onClick={() => void request({ type: "safety_command", action: "end_evacuation", by: "Twin" })}>End</button></div>
            <div className="tabular text-[20px] font-semibold">{evac.accounted} / {evac.on_site} <span className="text-[13px] font-normal text-ink-2">accounted for</span></div>
            {(evac.predicted_s != null || evac.accounted_ms != null) && (
              <div className="tabular text-[12px] text-ink-2">
                {evac.predicted_s != null && `Predicted from walking distances: ${Math.ceil(evac.predicted_s / 60)} min`}
                {evac.accounted_ms != null && ` · everyone mustered in ${Math.round((evac.accounted_ms - evac.started_ms) / 1000)} s`}
              </div>
            )}
            {s.routes.length > 0 && (
              <div className="text-[12px] text-ink-2">
                Routes (advice): {s.routes.slice(0, 4).map((r) => `${zoneName(sites, r.zone_id)} → ${r.muster_id} ${Math.round(r.length_m)} m`).join(" · ")}{s.routes.length > 4 ? ` · +${s.routes.length - 4} more` : ""}
              </div>
            )}
            {evac.unaccounted.length > 0 && <div className="text-[12px]">Unaccounted: {evac.unaccounted.map((u) => `${u.id} (last in ${u.last_zone_id ? zoneName(sites, u.last_zone_id) : "unknown"})`).join(", ")}</div>}
          </div>
        ) : (
          <button type="button" className="rounded-lg bg-accent px-3 py-1.5 text-[13px] font-medium text-white hover:brightness-95"
            onClick={() => void request({ type: "safety_command", action: "start_evacuation", reason: "evacuation drill", by: "Twin" })}>Start evacuation drill</button>
        )}
      </div>
      {!compact && <div className="text-[11px] leading-snug text-ink-2">
        Warning within {s.config.warn_m} m of a moving forklift, critical within {s.config.crit_m} m. {PRIVACY_NOTE}
      </div>}
    </div>
  );
}
