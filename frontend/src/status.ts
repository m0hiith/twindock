import type { Unit } from "./contract";

export type Tone = "ok" | "info" | "warn" | "crit" | "idle" | "live";

const TONES: Record<string, Record<string, Tone>> = {
  forklift: { idle: "idle", driving: "info", carrying: "info", picking: "warn", loading: "info", charging: "ok" },
  truck: { arriving: "info", docked: "ok", loading: "warn", departing: "info", gone: "idle" },
  dock: { available: "ok", occupied: "info", maintenance: "warn" },
  charger: { available: "ok", occupied: "info" },
  rack: { available: "ok", full: "warn" },
  pallet: { stored: "idle", staged: "info", carried: "info", loaded: "ok" },
  gateway: { online: "live", offline: "crit", waiting: "idle" },
  machine: { running: "ok", idle: "idle", starved: "warn", blocked: "warn", setup: "info", planned_stop: "idle", fault: "crit", maintenance: "warn", no_data: "idle" },
  worker: { walking: "info", working: "ok", idle: "idle" },
};

/** Device health tone. The real board's online state is violet (live data); a sim device's is green. */
export function deviceTone(d: { status: string; source: string }): Tone {
  if (d.status === "online") return d.source === "device" ? "live" : "ok";
  return d.status === "stale" ? "warn" : d.status === "fault" ? "crit" : "idle";
}

export function toneOf(u: Pick<Unit, "kind" | "state">): Tone {
  return TONES[u.kind]?.[u.state] ?? "idle";
}

export const toneColor: Record<Tone, { fg: string; bg: string }> = {
  ok: { fg: "var(--ok)", bg: "var(--ok-bg)" },
  info: { fg: "var(--info)", bg: "var(--info-bg)" },
  warn: { fg: "var(--warn)", bg: "var(--warn-bg)" },
  crit: { fg: "var(--crit)", bg: "var(--crit-bg)" },
  idle: { fg: "var(--idle)", bg: "var(--idle-bg)" },
  live: { fg: "var(--live)", bg: "#F3EDFF" },
};

/** Sentence-case state for pills: "charging" -> "Charging". */
export const stateLabel = (s: string) => (s.charAt(0).toUpperCase() + s.slice(1)).replace(/_/g, " ");
