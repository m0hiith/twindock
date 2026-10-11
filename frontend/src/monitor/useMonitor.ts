// GET /api/monitor polled every few seconds: energy (kW now, today vs yesterday) and the last 24 h of alerts with
// acknowledgement and resolution times. Everything else on the monitoring page comes from the WebSocket.
import { useEffect, useState } from "react";
import type { AlertsUpdate, SafetyUpdate } from "../contract";

export type Incident = AlertsUpdate["alerts"][number] & { response_s: number | null; resolution_s: number | null };
export interface PowerSummary {
  available: boolean; sim?: true; grid_ok: boolean | null; grid_kw: number | null; generator_kw: number | null; generator_state: string | null;
  solar_kw: number; solar_note: string; demand_kw: number | null; other_kw: number | null; solar_share: number | null; peak_kw: number; peak_exceeded: boolean;
  diesel_pct: number | null; units_today: number; production_kwh_today: number | null; kwh_per_unit: number | null; kwh_per_unit_note: string;
  solar_measured?: boolean; power_factor?: number | null; demand_15min_kw?: number | null; demand_15min_peak_kw?: number | null;
  tariff?: { label: string; rate: number; currency: string } | null; import_kwh_today?: number; cost_today?: number;
  genset?: { engine_state: string | null; rpm: number | null; coolant_c: number | null; fuel_lph: number | null; load_kw: number | null; transfer: string | null; mains_ok: boolean | null } | null;
  by_zone: { meter: string; zone_id: string; name: string; kw: number | null }[];
}
export interface MonitorData {
  power: PowerSummary;
  energy: { kw_now: number | null; today_kwh: number | null; yesterday_kwh: number | null; counting_since_ms: number | null; source: "sim"; meters: string[] };
  incidents: Incident[];
  evacuation_last: { started_ms: number; ended_ms: number | null; reason: string; by: string; on_site: number } | null;
  safety_today: SafetyUpdate["today"];
}

export function useMonitor(everyMs = 4000): MonitorData | null {
  const [d, setD] = useState<MonitorData | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () => fetch("/api/monitor").then((r) => (r.ok ? r.json() : null)).then((j: MonitorData | null) => { if (alive && j) setD(j); }).catch(() => undefined);
    load();
    const t = setInterval(load, everyMs);
    return () => { alive = false; clearInterval(t); };
  }, [everyMs]);
  return d;
}
