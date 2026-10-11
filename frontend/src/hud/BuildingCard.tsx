// Inspect card for a campus building (F2): purpose, zone hazard level and PPE, the devices in it (each SIM, with its
// reading and age), people in the zone (a count only) and live KPIs derived from those devices.
import { useMemo } from "react";
import type { Device } from "../contract";
import { channelLabel, formatReading, readingEntries, zoneName } from "../fleet/format";
import { sunFactor } from "../scene/campus/shared";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { ago, Icon, Pill, SimBadge, useTick } from "./ui";

const PURPOSE: Record<string, string> = {
  SEC_CABIN: "Visitor check-in and boom barrier control at the main gate, next to the weighbridge.",
  ADMIN: "Offices and reception for the campus. Visitors sign in at the gate first.",
  CANTEEN: "Staff canteen. Kitchen leak probe and air quality are monitored.",
  MEDICAL: "First aid and medical room. First-aiders are the nearest responders for SOS and man-down alerts.",
  RAW_STORE: "Inbound raw material. Trucks dock on the east wall; forklifts feed the manufacturing hall.",
  QC_LAB: "Quality control lab for samples from both production lines.",
  WORKSHOP: "Maintenance workshop and spare-parts store.",
  SUBSTATION: "Electrical substation and transformers feeding every zone. Restricted to utilities staff.",
  GENERATOR: "Diesel generator for critical loads during a grid failure, with its day tank.",
  COMPRESSOR: "Compressed air for the production lines. Pressure and loading are monitored.",
  PUMP_HOUSE: "Water pumps for the day tanks next to it.",
  HAZMAT: "Bunded store for hazardous materials, kept away from occupied buildings. Gas and leak monitored.",
  FIRE_PUMP: "Fire pump house and fire water tank. The panel bridge only reads the certified fire panel.",
  ETP: "Effluent treatment plant: equalisation, aeration and clarifier. Lone-worker zone.",
};
const HAZARD_TONE = { low: "ok", medium: "warn", high: "crit" } as const;
const PPE_LABEL: Record<string, string> = { helmet: "Helmet", vest: "Hi-vis vest", hearing: "Hearing protection", glasses: "Safety glasses", gloves: "Gloves", respirator: "Respirator", safety_shoes: "Safety shoes" };

const num = (d: Device | undefined, ch: string): number | null => {
  const v = d?.readings[ch]?.value;
  return d?.status === "online" && typeof v === "number" ? v : null;
};

/** Headline numbers per zone, all computed from the zone's own devices (never invented). */
function kpis(zoneId: string, ds: Device[], pv: number | null): [string, string][] {
  const by = (type: string) => ds.filter((d) => d.type === type);
  const out: [string, string][] = [];
  const kw = by("power_meter").map((d) => num(d, "power_kw")).filter((v): v is number => v !== null);
  if (kw.length) out.push(["Power now", `${kw.reduce((a, b) => a + b, 0).toFixed(1)} kW`]);
  const docks = by("dock_bay");
  if (docks.length) out.push(["Docks busy", `${docks.filter((d) => d.readings.occupied?.value === true).length} of ${docks.length}`]);
  const tanks = by("tank_level").map((d) => num(d, "level_pct")).filter((v): v is number => v !== null);
  if (tanks.length) out.push(["Tank level", tanks.map((v) => `${v.toFixed(0)}%`).join(" · ")]);
  const gas = by("gas_detector").map((d) => num(d, "co_ppm")).filter((v): v is number => v !== null);
  if (gas.length) out.push(["CO", `${Math.max(...gas).toFixed(0)} ppm`]);
  const comp = ds.find((d) => d.type === "compressor_monitor");
  if (comp) out.push(["Air pressure", num(comp, "pressure_bar") === null ? "—" : `${num(comp, "pressure_bar")!.toFixed(1)} bar`]);
  const env = by("env_sensor");
  const t = env.map((d) => num(d, "temperature")).filter((v): v is number => v !== null);
  const co2 = env.map((d) => num(d, "co2_ppm")).filter((v): v is number => v !== null);
  if (t.length) out.push(["Temperature", `${(t.reduce((a, b) => a + b, 0) / t.length).toFixed(1)} °C`]);
  if (co2.length) out.push(["CO₂", `${Math.round(Math.max(...co2))} ppm`]);
  if (by("leak_sensor").some((d) => d.readings.wet?.value === true)) out.push(["Leak", "Liquid detected"]);
  const fire = by("fire_panel")[0];
  if (fire) out.push(["Fire panel", fire.readings.alarm?.value === true ? "ALARM" : fire.readings.trouble?.value === true ? "Trouble" : "Normal"]);
  if (pv !== null) out.push(["Solar now", `${pv.toFixed(0)} kW`]);
  void zoneId;
  return out;
}

export function BuildingCard() {
  const id = useView((s) => s.building);
  const layout = useWorld((s) => s.layout);
  const sites = useWorld((s) => s.sites);
  const devices = useWorld((s) => s.devices);
  const zoneCounts = useWorld((s) => s.safety?.zone_counts);
  const cutaway = useView((s) => s.cutaway);
  useTick(1000);
  const c = layout?.campus;
  const b = c?.buildings.find((x) => x.id === id) ?? (id === "ETP" && c ? { ...c.etp, name: "Effluent treatment plant", h: 3 } : undefined);
  const zoneId = (b && "zone" in b ? b.zone : undefined) as string | undefined;
  const zone = useMemo(() => sites.flatMap((s) => s.zones).find((z) => z.id === zoneId), [sites, zoneId]);
  if (!id || !b || !zone) return null;
  const ds = Object.values(devices).filter((d) => d.zone_id === zone.id);
  const solar = c!.solar.find((s) => s.building === id);
  const pv = solar ? solar.kwp * sunFactor() * 0.8 : null;
  const people = zoneCounts?.[zone.id] ?? 0;
  const k = kpis(zone.id, ds, pv);
  const btn = "grid h-8 w-8 place-items-center rounded-lg text-ink-2 transition-colors hover:bg-idle-bg hover:text-ink";
  const hazard = (zone as { hazard?: "low" | "medium" | "high" }).hazard ?? "low";
  const ppe = (zone as { ppe?: string[] }).ppe ?? [];
  const roles = zone.restricted_roles ?? [];
  return (
    <div className="card pointer-events-auto max-h-[calc(100vh-250px)] w-[340px] overflow-y-auto p-4" aria-label={`${b.name} details`}>
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-info-bg text-info"><Icon name="dock" size={20} /></span>
        <div className="min-w-0 flex-1">
          <div className="text-[12px] text-ink-2">Building · {zone.site_id}</div>
          <div className="text-[20px] font-semibold leading-tight">{b.name}</div>
        </div>
        <div className="-mr-1 -mt-1 flex">
          <button type="button" className={btn} aria-label="Locate" title="Locate" onClick={() => useView.getState().focusOn(b.x + b.w / 2, b.z + b.d / 2)}><Icon name="locate" /></button>
          <button type="button" className={btn} aria-pressed={cutaway} aria-label="Interiors" title={cutaway ? "Close the roofs" : "Show interiors"} onClick={() => useView.getState().setCutaway(!cutaway)}><Icon name="open" /></button>
          <button type="button" className={btn} aria-label="Close" title="Close" onClick={() => useView.getState().setBuilding(null)}><Icon name="close" /></button>
        </div>
      </div>
      {PURPOSE[id] && <p className="mt-2 text-[13px] text-ink-2">{PURPOSE[id]}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Pill tone={HAZARD_TONE[hazard]}>{hazard[0]!.toUpperCase() + hazard.slice(1)} hazard</Pill>
        {ppe.map((p) => <span key={p} className="rounded-full bg-idle-bg px-2 py-0.5 text-[12px]">{PPE_LABEL[p] ?? p}</span>)}
        {ppe.length === 0 && <span className="text-[12px] text-ink-2">No special PPE</span>}
      </div>
      <div className="mt-2 space-y-0.5 text-[12px] text-ink-2">
        {roles.length > 0 && <div>Restricted to: {roles.map((r) => r.replace(/_/g, " ")).join(", ")}</div>}
        {(zone as { time_limit_min?: number }).time_limit_min && <div>Time limit {(zone as { time_limit_min?: number }).time_limit_min} min</div>}
        {(zone as { lone_worker?: boolean }).lone_worker && <div>Lone-worker zone: check-in every {(zone as { checkin_min?: number }).checkin_min ?? 10} min</div>}
        <div>{people} {people === 1 ? "person" : "people"} here now (count only)</div>
      </div>
      {k.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {k.map(([l, v]) => (
            <div key={l} className="rounded-lg bg-idle-bg px-3 py-2"><div className="text-[12px] text-ink-2">{l}</div><div className="tabular text-[15px] font-semibold">{v}</div></div>
          ))}
        </div>
      )}
      <div className="mt-3 border-t border-[var(--card-border)] pt-2">
        <div className="mb-1 flex items-center justify-between text-[13px] font-semibold">Devices ({ds.length}) <SimBadge /></div>
        <div className="divide-y divide-[var(--card-border)]">
          {ds.length === 0 && <div className="py-1.5 text-[13px] text-ink-2">No devices in this zone</div>}
          {ds.map((d) => {
            const [ch, r] = readingEntries(d)[0] ?? [];
            return (
              <button key={d.id} type="button" className="flex w-full items-center gap-2 py-1.5 text-left text-[13px] hover:bg-idle-bg" onClick={() => { send({ type: "select_unit", unit_id: d.id }); useView.getState().focusOn(d.x, d.z); }}>
                <span className="font-medium">{d.id}</span>
                <span className="min-w-0 flex-1 truncate text-ink-2">{d.label}</span>
                {ch && r ? <span className="tabular shrink-0 text-right"><span title={channelLabel(ch)}>{formatReading(ch, r)}</span> <span className="text-[11px] text-ink-2">{ago(r.received_ms)}</span></span> : <span className="text-ink-2">—</span>}
              </button>
            );
          })}
        </div>
      </div>
      {solar && <p className="mt-2 text-[11px] text-ink-2">Solar: {solar.kwp} kWp design size; output is computed from the time of day (simulation), not measured.</p>}
      <div className="mt-1 text-[11px] text-ink-2">{zoneName(sites, zone.id)}</div>
    </div>
  );
}
