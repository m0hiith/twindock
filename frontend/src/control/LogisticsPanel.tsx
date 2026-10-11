// Logistics (R3, simulated): KPIs from the logistics event log, each truck's stage with its weighbridge weights,
// recent weighbridge tickets, finished-goods orders, the raw material reorder position and forklift batteries in Ah.
import { Pill, SimBadge, useTick } from "../hud/ui";
import { useWorld } from "../store/world";

const STAGE: Record<string, string> = {
  offsite: "Off site", gate: "Gate check-in", weighbridge: "On the weighbridge", queue: "Yard queue", dock: "At the dock",
  paperwork: "Paperwork", departing: "Leaving",
};

const pct = (x: number | null | undefined) => (x == null ? "—" : `${Math.round(x * 100)}%`);
const min = (x: number | null | undefined) => (x == null ? "—" : `${x.toFixed(0)} min`);

export function LogisticsPanel() {
  const lg = useWorld((s) => s.logistics);
  useTick(5000);
  if (!lg) return <div className="p-4 text-ink-2">Waiting for the server…</div>;
  const k = lg.kpis;
  return (
    <div className="flex flex-col gap-4 p-4 text-[13px]">
      <section aria-label="Logistics KPIs">
        <div className="flex items-center gap-2"><h2 className="text-[15px] font-semibold">Logistics KPIs</h2><SimBadge /></div>
        <p className="mt-0.5 text-[12px] text-ink-2">From the logistics event log; minutes at real-world scale.</p>
        <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
          <span className="text-ink-2">Dock to stock</span><span className="tabular">{min(k.dock_to_stock_min)}</span>
          <span className="text-ink-2">Truck turnaround</span><span className="tabular">{min(k.turnaround_min)}</span>
          <span className="text-ink-2">On-time dispatch</span><span className="tabular">{pct(k.on_time_dispatch)} ({k.orders_shipped} shipped, {k.orders_open} open)</span>
          <span className="text-ink-2">Arrivals on schedule</span><span className="tabular">{pct(k.arrivals_on_schedule)}</span>
          <span className="text-ink-2">Forklift utilisation</span><span className="tabular">{pct(k.forklift_utilisation)}</span>
          <span className="text-ink-2">Raw material</span>
          <span className="tabular">{lg.raw.position} pallets · reorder at {lg.raw.reorder_point}{lg.raw.on_order ? " · on order" : ""}</span>
        </div>
      </section>
      <section aria-label="Trucks">
        <h2 className="text-[15px] font-semibold">Trucks</h2>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          {lg.trucks.map((t) => (
            <div key={t.id} className="flex items-center gap-2 py-1.5">
              <span className="w-12 font-semibold">{t.id}</span>
              <Pill tone={t.stage === "offsite" ? "idle" : t.stage === "dock" ? "ok" : "info"}>{STAGE[t.stage] ?? t.stage}</Pill>
              <span className="ml-auto tabular text-ink-2">
                {t.stage === "offsite" && t.eta_min != null ? `due in ${t.eta_min.toFixed(0)} min` : `${t.pallets} pallets`}
                {t.gross_in_kg != null && ` · in ${(t.gross_in_kg / 1000).toFixed(1)} t`}
                {t.gross_out_kg != null && ` · out ${(t.gross_out_kg / 1000).toFixed(1)} t`}
              </span>
            </div>
          ))}
        </div>
      </section>
      <section aria-label="Weighbridge">
        <h2 className="text-[15px] font-semibold">Weighbridge tickets</h2>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          {lg.tickets.length === 0 && <div className="py-1.5 text-ink-2">None yet</div>}
          {lg.tickets.map((t) => (
            <div key={`${t.truck}-${t.wall_ms}-${t.direction}`} className="flex gap-2 py-1.5 tabular">
              <span className="w-12 font-semibold">{t.truck}</span><span className="w-8">{t.direction}</span>
              <span>{t.gross_kg.toLocaleString()} kg gross · {t.tare_kg.toLocaleString()} tare · net {(t.gross_kg - t.tare_kg).toLocaleString()} kg · {t.pallets} pallets</span>
            </div>
          ))}
        </div>
      </section>
      <section aria-label="Orders">
        <h2 className="text-[15px] font-semibold">Finished-goods orders</h2>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          {lg.orders.length === 0 && <div className="py-1.5 text-ink-2">None yet</div>}
          {lg.orders.map((o) => (
            <div key={o.id} className="flex items-center gap-2 py-1.5">
              <span className="w-16 font-semibold">{o.id}</span>
              <span className="tabular">{o.shipped}/{o.pallets} pallets</span>
              <span className="ml-auto">
                {o.done ? <Pill tone={o.on_time ? "ok" : "warn"}>{o.on_time ? "On time" : "Late"}</Pill>
                  : <span className="tabular text-ink-2">{o.due_in_min >= 0 ? `due in ${o.due_in_min.toFixed(0)} min` : `${(-o.due_in_min).toFixed(0)} min late`}</span>}
              </span>
            </div>
          ))}
        </div>
      </section>
      <section aria-label="Batteries">
        <h2 className="text-[15px] font-semibold">Forklift batteries</h2>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          {lg.batteries.map((b) => (
            <div key={b.id} className="flex items-center gap-2 py-1.5 tabular">
              <span className="w-12 font-semibold">{b.id}</span><span>{b.pct.toFixed(0)}%</span>
              <span className="text-ink-2">used {b.ah_used.toFixed(1)} Ah · charged {b.ah_charged.toFixed(1)} Ah</span>
              {b.charging && <span className="ml-auto"><Pill tone="ok">{b.reason === "opportunity" ? "Top-up in break" : "Charging"}</Pill></span>}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
