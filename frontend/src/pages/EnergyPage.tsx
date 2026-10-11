// /energy: where the campus's power goes and where it comes from (F3). kW by building from the feeder meters, solar (computed
// from the time of day, not measured), grid import, the generator, energy per unit made and a peak-demand warning.
// Everything here is simulated (SIM) or computed from simulated meters; it says so.
import { Brand } from "../hud/Brand";
import { LivePill } from "../hud/LivePill";
import { PageTabs } from "../hud/PageTabs";
import { Pill, SimBadge } from "../hud/ui";
import { useMonitor } from "../monitor/useMonitor";

const f = (v: number | null | undefined, d = 1) => (v === null || v === undefined ? "—" : v.toFixed(d));

function Card({ title, value, unit, sub, tone }: { title: string; value: string; unit?: string; sub?: string; tone?: "crit" | "warn" | "ok" }) {
  return (
    <div className="card flex min-w-[200px] flex-1 flex-col gap-1 p-4">
      <div className="flex items-center gap-2 text-[13px] text-ink-2">{title}<span className="ml-auto"><SimBadge /></span></div>
      <div className={`tabular text-[28px] font-semibold leading-none ${tone === "crit" ? "text-crit" : tone === "warn" ? "text-warn" : ""}`}>{value}{unit && <span className="ml-1 text-[15px] font-medium text-ink-2">{unit}</span>}</div>
      {sub && <div className="text-[12px] text-ink-2">{sub}</div>}
    </div>
  );
}

export function EnergyPage() {
  const data = useMonitor(3000);
  const p = data?.power;
  const rows = p ? [...p.by_zone.map((z) => ({ name: z.name, kw: z.kw })), { name: "Other loads (offices, lighting, warehouse)", kw: p.other_kw }] : [];
  const max = Math.max(1, ...rows.map((r) => r.kw ?? 0));
  const down = p?.grid_ok === false;
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4"><Brand /><PageTabs className="ml-2" /><div className="ml-auto"><LivePill /></div></header>
        <div className="flex flex-wrap items-baseline gap-3">
          <h1 className="text-[20px] font-semibold">Energy</h1>
          {p?.available && <Pill tone={down ? "crit" : p.grid_ok ? "ok" : "idle"}>{down ? `Grid failure · generator ${p.generator_state}` : p.grid_ok ? "Grid connected" : "No meter data"}</Pill>}
          {p?.peak_exceeded && <Pill tone="warn">Above the {p.peak_kw} kW peak limit</Pill>}
          <span className="text-[12px] text-ink-2">Simulated meters. Solar is computed from the time of day and the design size, not measured.</span>
        </div>
        {!data && <div className="text-ink-2">Loading…</div>}
        {p && !p.available && <div className="text-ink-2">No power meters are configured.</div>}
        {p?.available && (
          <>
            <div className="flex flex-wrap gap-3">
              <Card title="Demand" value={f(p.demand_kw)} unit="kW" sub={`${p.peak_kw} kW peak limit`} tone={p.peak_exceeded ? "warn" : undefined} />
              <Card title="Solar now (computed)" value={f(p.solar_kw, 0)} unit="kW" sub={p.solar_share === null ? "Solar offsets nothing while the grid is down" : `${Math.round(p.solar_share * 100)}% of demand`} />
              <Card title="Grid import" value={f(p.grid_kw)} unit="kW" sub={down ? "No grid" : "From the substation incomer meter"} tone={down ? "crit" : undefined} />
              <Card title="Generator" value={f(p.generator_kw)} unit="kW" sub={`Diesel ${p.diesel_pct === null ? "—" : `${p.diesel_pct.toFixed(0)}%`}`} />
              <Card title="Energy per unit" value={p.kwh_per_unit === null ? "—" : p.kwh_per_unit.toFixed(2)} unit="kWh" sub={`${p.units_today} units today · ${f(p.production_kwh_today, 1)} kWh`} />
            </div>
            <section className="card p-4" aria-label="kW by building">
              <h2 className="text-[15px] font-semibold">kW by building</h2>
              <div className="mt-3 flex flex-col gap-2">
                {rows.map((r) => (
                  <div key={r.name} className="grid grid-cols-[260px_1fr_80px] items-center gap-3 text-[13px]">
                    <span className="truncate">{r.name}</span>
                    <div className="h-3 rounded-full bg-idle-bg"><div className="h-3 rounded-full bg-accent" style={{ width: `${((r.kw ?? 0) / max) * 100}%` }} /></div>
                    <span className="tabular text-right">{f(r.kw)} kW</span>
                  </div>
                ))}
              </div>
            </section>
            <section className="card p-4 text-[13px] text-ink-2">
              <div className="font-semibold text-ink">How these numbers are made</div>
              <ul className="mt-1 list-disc pl-5">
                <li>Each building's kW is its feeder meter; the substation incomer meter reads the whole campus minus solar (grid import). "Other loads" is what the incomer sees beyond the metered feeders.</li>
                <li>{p.solar_note}</li>
                <li>{p.kwh_per_unit_note}</li>
                <li>In a grid failure the generator picks up the critical zones only; solar stops (no islanding) and mains devices elsewhere go quiet.</li>
              </ul>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
