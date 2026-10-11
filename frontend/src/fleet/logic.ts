// Pure fleet-table logic (sorting, "needs attention", filters, summary). No React, no store, so
// `npm test` (node --test) can run it directly.
import type { Device } from "../contract";

export const LOW_BATTERY_PCT = 20;

export type AttentionReason = "fault" | "offline" | "stale" | "low battery";

/** Why a device needs attention, worst first; empty when it is fine. */
export function attentionReasons(d: Pick<Device, "status" | "battery_pct">): AttentionReason[] {
  const r: AttentionReason[] = [];
  if (d.status === "fault") r.push("fault");
  if (d.status === "offline") r.push("offline");
  if (d.status === "stale") r.push("stale");
  if (typeof d.battery_pct === "number" && d.battery_pct < LOW_BATTERY_PCT) r.push("low battery");
  return r;
}

export const needsAttention = (d: Pick<Device, "status" | "battery_pct">): boolean => attentionReasons(d).length > 0;

const SEVERITY: Record<AttentionReason, number> = { fault: 0, offline: 1, stale: 2, "low battery": 3 };

function severity(d: Device): number {
  const r = attentionReasons(d);
  return r.length ? Math.min(...r.map((x) => SEVERITY[x])) : 9;
}

/** Real devices always first; then the worst problem first; then by id. */
export function sortDevices(list: Device[]): Device[] {
  return [...list].sort((a, b) => {
    if (a.source !== b.source) return a.source === "device" ? -1 : 1;
    const s = severity(a) - severity(b);
    if (s !== 0) return s;
    return a.id.localeCompare(b.id);
  });
}

export interface FleetFilter {
  attentionOnly: boolean;
  site: string | null;
  zone: string | null;
  type: Device["type"] | null;
  protocol: Device["protocol"] | null;
  source: Device["source"] | null;
}

export const DEFAULT_FILTER: FleetFilter = {
  attentionOnly: true, site: null, zone: null, type: null, protocol: null, source: null,
};

export function applyFilter(list: Device[], f: FleetFilter): Device[] {
  return sortDevices(list.filter((d) =>
    (!f.attentionOnly || needsAttention(d)) &&
    (!f.site || d.site_id === f.site) &&
    (!f.zone || d.zone_id === f.zone) &&
    (!f.type || d.type === f.type) &&
    (!f.protocol || d.protocol === f.protocol) &&
    (!f.source || d.source === f.source)));
}

export interface FleetSummary {
  total: number;
  online: number;
  attention: number;
  real: number;
  byProtocol: Record<Device["protocol"], { total: number; online: number }>;
}

export function summarize(list: Device[]): FleetSummary {
  const byProtocol: FleetSummary["byProtocol"] = {
    wifi: { total: 0, online: 0 }, ble: { total: 0, online: 0 }, thread: { total: 0, online: 0 }, matter: { total: 0, online: 0 },
  };
  let online = 0, attention = 0, real = 0;
  for (const d of list) {
    const p = byProtocol[d.protocol];
    p.total++;
    if (d.status === "online") { online++; p.online++; }
    if (needsAttention(d)) attention++;
    if (d.source === "device") real++;
  }
  return { total: list.length, online, attention, real, byProtocol };
}

/** The reading the side panel charts for each device type (null: nothing numeric to chart). */
export const MAIN_CHANNEL: Record<Device["type"], string | null> = {
  gateway: "wifi_rssi_dbm", machine_monitor: "vibration_rms", env_sensor: "temperature", door_sensor: "open",
  occupancy_sensor: "occupied", badge: null, asset_tag: null, power_meter: "power_kw", light: "level_pct",
  air_quality: "co2_ppm", truck_telematics: "speed_kmh", dock_bay: "occupied", conveyor_monitor: "motor_current_a",
  compressor_monitor: "pressure_bar", helmet_clip: "worn", gas_detector: "co_ppm", leak_sensor: "wet", tank_level: "level_pct",
  fire_panel: "alarm", water_quality: "ph", genset_controller: "load_kw",
};

export const TYPE_LABEL: Record<Device["type"], string> = {
  gateway: "Gateway", machine_monitor: "Machine monitor", env_sensor: "Environment sensor", door_sensor: "Door sensor",
  occupancy_sensor: "Occupancy sensor", badge: "Worker badge", asset_tag: "Asset tag", power_meter: "Power meter",
  light: "Light", air_quality: "Air quality", truck_telematics: "Truck telematics", dock_bay: "Dock bay monitor",
  conveyor_monitor: "Conveyor monitor", compressor_monitor: "Compressor monitor", helmet_clip: "Helmet clip", gas_detector: "Gas detector",
  leak_sensor: "Leak sensor", tank_level: "Tank level", fire_panel: "Fire panel bridge", water_quality: "Water quality",
  genset_controller: "Generator controller bridge",
};

/** "-61 dBm" to 0-4 bars, the usual phone-style buckets. */
export function signalBars(rssi: number | null | undefined): number {
  if (rssi === null || rssi === undefined) return 0;
  return rssi >= -55 ? 4 : rssi >= -67 ? 3 : rssi >= -78 ? 2 : rssi >= -88 ? 1 : 0;
}
