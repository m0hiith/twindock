// Small HUD building blocks shared by the cards: icons, pills, bars, ages.
import { useEffect, useState, type ReactNode } from "react";
import type { Device, Unit } from "../contract";
import { stateLabel, toneColor, toneOf, type Tone } from "../status";
import { send } from "../store/ws";
import { serverNow, useView, useWorld } from "../store/world";

const PATHS = {
  logo: "M4 15 12 7l8 8M9 15h6v4H9z",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4",
  chevronDown: "m6 9 6 6 6-6",
  chevronRight: "m9 6 6 6-6 6",
  chevronLeft: "m15 6-6 6 6 6",
  bell: "M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20a7.5 7.5 0 0 1 15 0",
  check: "m5 12 5 5 9-10",
  box: "M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5zM3.5 7.5 12 12l8.5-4.5M12 12v9",
  truck: "M2.5 6.5h11v9h-11zM13.5 9.5h4l3 3.2v2.8h-7zM6.5 18.5a1.6 1.6 0 1 0 0-.01M17 18.5a1.6 1.6 0 1 0 0-.01",
  dock: "M3 20V9l9-5 9 5v11M7 20v-7h10v7M7 16h10",
  forklift: "M4 18V9h6l3 5v4M13 18h4M17 4v14M17 18h4M7 18.5a1.5 1.5 0 1 0 0-.01",
  pallet: "M3 15h18M3 19h18M5 15v4M12 15v4M19 15v4M6 8h12v7H6z",
  rack: "M4 3v18M20 3v18M4 8h16M4 14h16M4 20h16",
  charger: "M13 2 5 14h6l-1 8 8-12h-6z",
  gateway: "M12 20v-9M8.5 8.5a5 5 0 0 1 7 0M6 6a8.5 8.5 0 0 1 12 0M10.5 20h3",
  locate: "M12 3v3M12 18v3M3 12h3M18 12h3M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z",
  open: "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
  close: "M6 6l12 12M18 6 6 18",
  battery: "M3 8h15v8H3zM20 11v2",
  arrowUp: "M12 19V5M6 11l6-6 6 6",
  arrowDown: "M12 5v14M6 13l6 6 6-6",
  reset: "M4 12a8 8 0 1 0 2.4-5.7M4 4v4h4",
  machine: "M3 20h18M5 20V9h5v11M10 13h9v7M7 9V5h1.5v4M13 13v-3h3v3",
  worker: "M12 7.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM7.5 21v-6l-1.5-1 1.5-4.5h9l1.5 4.5-1.5 1v6M10 21v-5h4v5",
  sensor: "M12 13a1 1 0 1 0 0-.01M8.5 9.5a5 5 0 0 0 0 7M15.5 9.5a5 5 0 0 1 0 7M6 7a8.5 8.5 0 0 0 0 12M18 7a8.5 8.5 0 0 1 0 12",
  factory: "M3 21V10l6 3V10l6 3V6h6v15zM7 17h2M12 17h2M17 17h2",
  shield: "M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z",
  alert: "M12 4 2.8 20h18.4zM12 10v4M12 17v.01",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 16, className, strokeWidth = 1.8 }: { name: IconName; size?: number; className?: string; strokeWidth?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}

export const kindIcon: Record<Unit["kind"], IconName> = {
  forklift: "forklift", truck: "truck", pallet: "pallet", dock: "dock", rack: "rack", charger: "charger", gateway: "gateway",
  machine: "machine", worker: "worker",
};

export const kindLabel: Record<Unit["kind"], string> = {
  forklift: "Forklift", truck: "Truck", pallet: "Pallet", dock: "Dock", rack: "Rack", charger: "Charger", gateway: "Gateway",
  machine: "Machine", worker: "Worker",
};

export function Pill({ tone, children }: { tone: Tone; children: ReactNode }) {
  const t = toneColor[tone];
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[12px] font-medium" style={{ color: t.fg, background: t.bg }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: t.fg }} />
      {children}
    </span>
  );
}

export function StatusPill({ unit }: { unit: Pick<Unit, "kind" | "state"> }) {
  return <Pill tone={toneOf(unit)}>{stateLabel(unit.state)}</Pill>;
}

/** Violet badge reserved for real board/device data. */
export function LiveBadge() {
  return <span className="rounded-full bg-[#F3EDFF] px-1.5 py-px text-[11px] font-semibold tracking-wide text-live">LIVE</span>;
}

/** Grey badge for simulated data (tools/site_sim.py). Never violet. */
export function SimBadge() {
  return <span className="rounded-full bg-idle-bg px-1.5 py-px text-[11px] font-semibold tracking-wide text-ink-2">SIM</span>;
}

export const protocolLabel: Record<Device["protocol"], string> = { wifi: "Wi-Fi", ble: "BLE", thread: "Thread", matter: "Matter" };

/** "LIVE · Wi-Fi" or "SIM · Thread": the protocol is always labelled with where the data comes from. */
export function SourceProtocol({ d }: { d: Pick<Device, "source" | "protocol"> }) {
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      {d.source === "device" ? <LiveBadge /> : <SimBadge />}
      <span className="text-ink-2">{protocolLabel[d.protocol]}</span>
    </span>
  );
}

export function Bar({ pct, color = "var(--info)", className = "" }: { pct: number; color?: string; className?: string }) {
  const w = Math.max(0, Math.min(100, pct));
  return (
    <div className={`h-1.5 overflow-hidden rounded-full bg-idle-bg ${className}`}>
      <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${w}%`, background: color }} />
    </div>
  );
}

export function batteryColor(pct: number): string {
  return pct < 25 ? "var(--crit)" : pct < 50 ? "var(--warn)" : "var(--ok)";
}

/** Re-render every `ms` (for clocks and "12s ago"). */
export function useTick(ms = 1000): number {
  const [t, setT] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setT(Date.now()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return t;
}

/** "now", "12s ago", "4m ago", "2h ago", measured on the server clock. */
export function ago(receivedMs: number): string {
  const s = Math.max(0, Math.round((serverNow() - receivedMs) / 1000));
  if (s < 2) return "now";
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export function nodeLabel(id: string | null | undefined): string {
  if (!id) return "—";
  const n = useWorld.getState().layout?.nodes.find((q) => q.id === id);
  return n?.label ?? id;
}

/** Select a unit (shared, via the server) and center the local camera on it. */
export function selectAndCenter(id: string): void {
  send({ type: "select_unit", unit_id: id });
  const u = useWorld.getState().units[id];
  if (u) useView.getState().focusOn(u.x, u.z);
}

export function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={active}
      className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[13px] font-medium transition-colors ${active ? "bg-info-bg text-info" : "text-ink-2 hover:bg-idle-bg hover:text-ink"}`}>
      {children}
    </button>
  );
}
