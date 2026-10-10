// Worker safety on /twin (FAC-01): workers per zone, warnings today, closest approach today, and
// who is near a moving forklift right now. Badges show role and zone only.
import { zoneName } from "../fleet/format";
import { useWorld } from "../store/world";
import { ago, Icon, Pill, SimBadge, useTick } from "./ui";

export const PRIVACY_NOTE = "Badges show role and zone only. Names are visible to authorised users, and this demo has no sign-in, so nobody sees them. Nothing is recorded beyond the event log.";

export function SafetyPanel() {
  const s = useWorld((x) => x.safety);
  const sites = useWorld((x) => x.sites);
  useTick(1000);
  if (!s) return null;
  const counts = Object.entries(s.zone_counts).filter((e): e is [string, number] => e[1] !== undefined).sort((a, b) => b[1] - a[1]);
  const active = s.workers.filter((w) => w.near || w.restricted_zone);
  const t = s.today;
  return (
    <div className="card pointer-events-auto flex w-[420px] flex-col gap-3 p-4" aria-label="Worker safety">
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
      {active.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {active.map((w) => (
            <div key={w.id} className="flex items-center gap-2 text-[13px]">
              <Pill tone={w.restricted_zone || w.near?.level === "critical" ? "crit" : "warn"}>
                {w.restricted_zone ? "Restricted" : w.near?.level === "critical" ? "Critical" : "Warning"}
              </Pill>
              <span className="min-w-0 truncate">
                {w.id} ({w.role.replace(/_/g, " ")}) {w.near ? `${w.near.distance_m.toFixed(1)} m from moving ${w.near.forklift}` : `in ${zoneName(sites, w.restricted_zone ?? "")}`}
              </span>
            </div>
          ))}
        </div>
      )}
      <div className="text-[11px] leading-snug text-ink-2">
        Warning within {s.config.warn_m} m of a moving forklift, critical within {s.config.crit_m} m. {PRIVACY_NOTE}
      </div>
    </div>
  );
}
