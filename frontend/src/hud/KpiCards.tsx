import { useMemo } from "react";
import { useWorld } from "../store/world";
import { kpiCounts } from "./kpis";
import { Icon, type IconName } from "./ui";

function Delta({ value, since }: { value: number; since: string }) {
  const zero = value === 0;
  return (
    <span className="flex items-center gap-1.5 text-[12px] text-ink-2">
      <span className={`tabular inline-flex items-center gap-0.5 rounded-full px-1.5 py-px font-medium ${zero ? "bg-idle-bg text-idle" : "bg-ok-bg text-ok"}`}>
        {!zero && <Icon name={value > 0 ? "arrowUp" : "arrowDown"} size={11} strokeWidth={2.4} />}
        {zero ? "±0" : Math.abs(value)}
      </span>
      since {since}
    </span>
  );
}

function Kpi({ icon, label, value, suffix, delta, since, context }: {
  icon: IconName; label: string; value: number; suffix?: string; delta: number | null; since: string; context: string;
}) {
  return (
    <div className="card pointer-events-auto w-[236px] p-4">
      <div className="flex items-center gap-2.5">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-info-bg text-info"><Icon name={icon} size={17} /></span>
        <span className="text-[13px] text-ink-2">{label}</span>
      </div>
      <div className="mt-3 flex items-baseline justify-between gap-2">
        <span className="tabular text-[28px] font-semibold leading-none tracking-tight">
          {value}{suffix && <span className="ml-1 text-[15px] font-medium text-ink-2">{suffix}</span>}
        </span>
        {delta !== null && <Delta value={delta} since={since} />}
      </div>
      <div className="mt-2 line-clamp-2 text-[12px] leading-snug text-ink-2" title={context}>{context}</div>
    </div>
  );
}

export function KpiCards() {
  const units = useWorld((s) => s.units);
  const logistics = useWorld((s) => s.logistics);
  const baseline = useWorld((s) => s.baseline);
  // Units change at 20 Hz; the counts only depend on states, so this is cheap.
  const c = useMemo(() => kpiCounts(units), [units]);
  const b = baseline?.counts;
  const since = baseline ? new Date(baseline.at_ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";
  const dockPct = c.docksUsable ? Math.round((c.docksInUse / c.docksUsable) * 100) : 0;
  return (
    <div className="flex gap-3">
      <Kpi icon="box" label="Stock on hand" value={c.stock} suffix="pallets" delta={b ? c.stock - b.stock : null} since={since}
        context={`${c.stockInRacks} in racks · ${c.stockStaged} staged · ${c.stock - c.stockInRacks - c.stockStaged} on forklifts`} />
      <Kpi icon="truck" label="Trucks on site" value={c.trucksOnSite} delta={b ? c.trucksOnSite - b.trucksOnSite : null} since={since}
        context={`${c.trucksDocked} docked · ${c.trucksOnSite - c.trucksDocked} in the yard`} />
      {logistics?.kpis.on_time_dispatch != null ? (
        // On-time dispatch from the logistics event log: orders shipped by their due time (simulated orders, R3).
        <Kpi icon="dock" label="On-time dispatch" value={Math.round(logistics.kpis.on_time_dispatch * 100)} suffix="%" delta={null} since={since}
          context={`${logistics.kpis.orders_shipped} orders shipped · ${logistics.kpis.orders_open} open · ${dockPct}% of docks in use`} />
      ) : (
        <Kpi icon="dock" label="Docks in use" value={dockPct} suffix="%" delta={b ? c.docksInUse - b.docksInUse : null} since={since}
          context={`${c.docksInUse} of ${c.docksUsable} bays${c.docksMaintenance ? ` · ${c.docksMaintenance} in maintenance` : ""}`} />
      )}
    </div>
  );
}
