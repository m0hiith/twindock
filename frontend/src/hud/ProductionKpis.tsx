// FAC-01 production zone KPIs: units today, machine availability, OEE (formula on hover).
// All from the simulated machine monitors (SIM badge); "—" until there is data to compute from.
import { useState } from "react";
import { useWorld } from "../store/world";
import { Icon, SimBadge } from "./ui";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "—" : `${Math.round(x * 100)}%`);

function Kpi({ icon, label, value, sub, children }: { icon: "box" | "machine" | "check"; label: string; value: string; sub: string; children?: React.ReactNode }) {
  return (
    <div className="card pointer-events-auto relative flex w-[200px] flex-col gap-1 p-4">
      <span className="flex items-center gap-2 text-[13px] text-ink-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-idle-bg text-ink"><Icon name={icon} size={16} /></span>
        {label}
        <span className="ml-auto"><SimBadge /></span>
      </span>
      <span className="tabular text-[28px] font-semibold leading-none">{value}</span>
      <span className="line-clamp-2 text-[12px] leading-snug text-ink-2" title={sub}>{sub}</span>
      {children}
    </div>
  );
}

export function ProductionKpis() {
  const p = useWorld((s) => s.production);
  const [hover, setHover] = useState(false);
  const line = p?.line;
  const machines = p?.machines ?? [];
  const running = machines.filter((m) => m.state === "running").length;
  return (
    <div className="flex items-start gap-3">
      <Kpi icon="box" label="Units today" value={line ? String(line.units_today) : "—"}
        sub={line ? `${line.pallets_made} pallets out · ${line.units_toward_pallet}/${p?.config.units_per_pallet} on the next` : "Waiting for machine monitors"} />
      <Kpi icon="machine" label="Availability" value={pct(line?.availability)}
        sub={`${running} of ${machines.length} machines running`} />
      <div onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} onFocus={() => setHover(true)} onBlur={() => setHover(false)} tabIndex={0}
        className="pointer-events-auto rounded-2xl outline-none" aria-describedby="oee-formula">
        <Kpi icon="check" label="OEE" value={pct(line?.oee)} sub={`A ${pct(line?.availability)} · P ${pct(line?.performance)} · Q ${pct(line?.quality)}`}>
          {hover && (
            <div id="oee-formula" role="tooltip" className="card absolute left-0 top-full z-30 mt-2 w-[300px] p-3 text-[12px] leading-relaxed">
              <div className="mb-1 text-[13px] font-semibold">OEE = Availability × Performance × Quality</div>
              <div><b>Availability</b> = running time ÷ planned time (time with data, excluding maintenance).</div>
              <div><b>Performance</b> = ideal cycle time × units made ÷ running time.</div>
              <div><b>Quality</b> = good units ÷ all units.</div>
              <div className="mt-1 text-ink-2">Zone: mean A × mean P × product of Q over M-01 and M-02. Computed from simulated machine monitors.</div>
            </div>
          )}
        </Kpi>
      </div>
    </div>
  );
}
