// Display helpers for device readings. A value is never shown without its unit and its age
// (the caller shows ago(received_ms) next to it).
import type { Device, Reading } from "../contract";

const CHANNEL_LABEL: Record<string, string> = {
  temperature: "Temperature", humidity: "Humidity", open: "Door", occupied: "Occupancy", co2_ppm: "CO₂",
  pm25_ugm3: "PM2.5", state: "Machine state", cycle_time_s: "Cycle time", current_a: "Motor current",
  vibration_rms: "Vibration (RMS)", units: "Units today", position: "Position", wifi_rssi_dbm: "Wi-Fi RSSI",
  uptime_s: "Uptime", msgs_sent: "Messages sent", power_kw: "Power", level_pct: "Light level",
};

export const channelLabel = (c: string): string =>
  CHANNEL_LABEL[c] ?? c.replace(/_/g, " ").replace(/^./, (x) => x.toUpperCase());

const DEFAULT_UNIT: Record<string, string> = { wifi_rssi_dbm: "dBm", uptime_s: "s" };

export function formatReading(channel: string, r: Reading): string {
  const v = r.value;
  if (typeof v === "boolean") {
    if (channel === "open") return v ? "Open" : "Closed";
    if (channel === "occupied") return v ? "Occupied" : "Empty";
    return v ? "Yes" : "No";
  }
  if (Array.isArray(v)) return `${v[0].toFixed(1)}, ${v[1].toFixed(1)} m`;
  if (typeof v === "string") return v.charAt(0).toUpperCase() + v.slice(1);
  const unit = r.unit ?? DEFAULT_UNIT[channel] ?? "";
  const digits = Math.abs(v) >= 100 || Number.isInteger(v) ? 0 : Math.abs(v) >= 10 ? 1 : 2;
  return `${v.toFixed(digits)}${unit ? (unit.startsWith("°") || unit === "%RH" ? "" : " ") + unit : ""}`;
}

export function zoneName(sites: { zones: { id: string; name: string }[] }[], id: string): string {
  for (const s of sites) for (const z of s.zones) if (z.id === id) return z.name;
  return id;
}

/** Readings as defined [channel, reading] pairs (the index signature allows undefined). */
export function readingEntries(d: Pick<Device, "readings">): [string, Reading][] {
  return Object.entries(d.readings).filter((e): e is [string, Reading] => e[1] !== undefined);
}

export const deviceTitle = (d: Pick<Device, "id" | "label">) => d.label ?? d.id;
