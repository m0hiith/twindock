// Numbers for the daily report and the monitoring page: pure functions, tested in stats.test.ts.
import type { MonitorData } from "./useMonitor";

const SAFETY_RULES = new Set(["proximity_warning", "proximity_critical", "restricted_zone", "fall_prealert", "no_motion_prealert", "man_down", "sos",
  "zone_time_limit", "lone_worker_overdue", "lone_worker_escalated", "evacuate_worker", "gas_alarm", "fire_alarm", "heat_stress"]);

export function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s.length % 2 ? s[(s.length - 1) / 2]! : (s[s.length / 2 - 1]! + s[s.length / 2]!) / 2;
}
export const fmtS = (s: number | null) => (s === null ? "—" : s < 90 ? `${Math.round(s)} s` : `${(s / 60).toFixed(1)} min`);

export function reportStats(d: MonitorData) {
  const inc = d.incidents;
  const bySev = { critical: 0, warning: 0, info: 0 };
  for (const a of inc) bySev[a.severity]++;
  const resp = inc.flatMap((a) => (a.response_s === null ? [] : [a.response_s]));
  const res = inc.flatMap((a) => (a.resolution_s === null ? [] : [a.resolution_s]));
  const open = inc.filter((a) => a.state !== "resolved").length;
  const unacked = inc.filter((a) => a.state === "raised").length;
  const nearMisses = inc.filter((a) => a.rule_id === "proximity_critical").length;
  return { total: inc.length, bySev, medianResponse: median(resp), medianResolution: median(res), open, unacked, nearMisses,
    safetyAlerts: inc.filter((a) => SAFETY_RULES.has(a.rule_id)).length };
}

