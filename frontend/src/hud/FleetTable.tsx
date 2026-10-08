// Docks / Forklifts / Trucks panel. Clicking a row selects the unit (shared) and centers on it.
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import type { Unit } from "../contract";
import { useWorld } from "../store/world";
import { Bar, batteryColor, Icon, LiveBadge, selectAndCenter, StatusPill, TabButton } from "./ui";

type Tab = "dock" | "forklift" | "truck";
const TABS: { id: Tab; label: string }[] = [
  { id: "dock", label: "Docks" },
  { id: "forklift", label: "Forklifts" },
  { id: "truck", label: "Trucks" },
];

/** Progress column: battery for forklifts, cargo for trucks and for the truck at a dock. */
function progress(u: Unit, units: Record<string, Unit>): { pct: number; text: string; color?: string } | null {
  if (u.kind === "forklift" && u.battery_pct !== undefined) {
    return { pct: u.battery_pct, text: `${Math.round(u.battery_pct)}%`, color: batteryColor(u.battery_pct) };
  }
  const truck = u.kind === "truck" ? u : u.kind === "dock" ? Object.values(units).find((t) => t.kind === "truck" && t.docked_at === u.node) : undefined;
  if (!truck) return null;
  const n = truck.cargo?.length ?? 0, cap = Number(truck.meta?.capacity ?? 0);
  return { pct: cap ? (n / cap) * 100 : 0, text: `${n}/${cap}` };
}

export function FleetTable() {
  const [tab, setTab] = useState<Tab>("forklift");
  const units = useWorld((s) => s.units);
  const selected = useWorld((s) => s.selected);
  const counts = useWorld(useShallow((s) => {
    const c = { dock: 0, forklift: 0, truck: 0 };
    for (const u of Object.values(s.units)) if (u.kind in c) c[u.kind as Tab]++;
    return c;
  }));
  const rows = Object.values(units).filter((u) => u.kind === tab).sort((a, b) => a.id.localeCompare(b.id));

  return (
    <div className="card pointer-events-auto flex w-[520px] flex-col p-3">
      <div className="flex items-center gap-1 px-1">
        {TABS.map((t) => (
          <TabButton key={t.id} active={tab === t.id} onClick={() => setTab(t.id)}>
            {t.label}
            <span className={`tabular rounded-full px-1.5 text-[11px] ${tab === t.id ? "bg-white text-info" : "bg-idle-bg text-ink-2"}`}>{counts[t.id]}</span>
          </TabButton>
        ))}
      </div>
      <div className="mt-2 grid grid-cols-[96px_1fr_92px_88px_16px] gap-3 border-b border-[var(--card-border)] px-2 pb-1.5 text-[12px] text-ink-2">
        <span>ID</span><span>Assignment</span><span>Status</span><span>{tab === "forklift" ? "Battery" : "Cargo"}</span><span />
      </div>
      <div className="max-h-[208px] overflow-y-auto">
        {rows.map((u) => {
          const p = progress(u, units);
          const sel = u.id === selected;
          return (
            <button key={u.id} type="button" onClick={() => selectAndCenter(u.id)} aria-current={sel}
              className={`grid w-full grid-cols-[96px_1fr_92px_88px_16px] items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors ${sel ? "bg-info-bg" : "hover:bg-[#F6F8FC]"}`}>
              <span className="flex items-center gap-1 whitespace-nowrap font-semibold">{u.kind === "dock" ? u.label : u.id}{u.source === "device" && <LiveBadge />}</span>
              <span className="truncate text-ink">{u.task}</span>
              <span><StatusPill unit={u} /></span>
              {p ? (
                <span className="flex items-center gap-2">
                  <Bar pct={p.pct} color={p.color} className="flex-1" />
                  <span className="tabular w-7 text-right text-[12px] text-ink-2">{p.text}</span>
                </span>
              ) : <span className="text-[12px] text-ink-2">—</span>}
              <Icon name="chevronRight" size={14} className="text-ink-2" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
