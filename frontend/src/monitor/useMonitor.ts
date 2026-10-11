// GET /api/monitor polled every few seconds: energy (kW now, today vs yesterday) and the last 24 h of alerts with
// acknowledgement and resolution times. Everything else on the monitoring page comes from the WebSocket.
import { useEffect, useState } from "react";
import type { AlertsUpdate, SafetyUpdate } from "../contract";

export type Incident = AlertsUpdate["alerts"][number] & { response_s: number | null; resolution_s: number | null };
export interface MonitorData {
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
