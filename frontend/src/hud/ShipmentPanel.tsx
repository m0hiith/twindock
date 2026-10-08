// Shipment tracking for one truck: a 5-step stepper derived from its server state and cargo,
// plus a shipment card. Follows the selected truck; otherwise the busiest truck at a dock.
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import type { Unit } from "../contract";
import { useWorld } from "../store/world";
import { Bar, Icon, LiveBadge, nodeLabel, selectAndCenter, StatusPill } from "./ui";

const STEPS = ["Arriving", "Docked", "Loading", "Departing", "Off site"] as const;

/** Index of the current step; STEPS.length when every step is done. */
function stepOf(t: Unit): number {
  const n = t.cargo?.length ?? 0, cap = Number(t.meta?.capacity ?? 0);
  switch (t.state) {
    case "arriving": return 0;
    case "docked": return n === 0 ? 1 : n >= cap ? 3 : 2; // full and waiting = next is departing
    case "loading": return 2;
    case "departing": return 3;
    case "gone": return STEPS.length;
    default: return 0;
  }
}

function rank(t: Unit): number {
  return ({ loading: 0, docked: 1, arriving: 2, departing: 3, gone: 4 } as Record<string, number>)[t.state] ?? 5;
}

function Stepper({ current }: { current: number }) {
  return (
    <ol className="flex items-start">
      {STEPS.map((label, i) => {
        const done = i < current, now = i === current;
        return (
          <li key={label} className="relative flex flex-1 flex-col items-center">
            {i > 0 && <span className={`absolute left-[-50%] top-[11px] h-0.5 w-full ${i <= current ? "bg-info" : "bg-[var(--card-border)]"}`} />}
            <span className={`z-10 grid h-6 w-6 place-items-center rounded-full ${done ? "bg-info text-white" : now ? "border-2 border-info bg-white" : "border-2 border-[var(--card-border)] bg-white"}`}>
              {done ? <Icon name="check" size={13} strokeWidth={2.6} /> : now ? <span className="h-2 w-2 rounded-full bg-info" /> : null}
            </span>
            <span className={`mt-1.5 text-[12px] ${done || now ? "font-medium text-ink" : "text-ink-2"}`}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

export function ShipmentPanel() {
  const trucks = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "truck").sort((a, b) => a.id.localeCompare(b.id))));
  const selected = useWorld((s) => s.selected);
  const [pinned, setPinned] = useState<string | null>(null);
  if (trucks.length === 0) return null;

  const sel = trucks.find((t) => t.id === selected);
  const t = sel ?? trucks.find((x) => x.id === pinned) ?? [...trucks].sort((a, b) => rank(a) - rank(b))[0]!;
  const i = trucks.indexOf(t);
  const cycle = (d: number) => setPinned(trucks[(i + d + trucks.length) % trucks.length]!.id);
  const cap = Number(t.meta?.capacity ?? 0), n = t.cargo?.length ?? 0;

  return (
    <div className="card pointer-events-auto flex w-[640px] gap-5 p-4">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[15px] font-semibold">Shipment tracking</div>
            <div className="text-[12px] text-ink-2">{sel ? "Selected truck" : pinned ? "Pinned truck" : "Most active truck"}</div>
          </div>
          {!sel && trucks.length > 1 && (
            <div className="flex items-center gap-1">
              <button type="button" aria-label="Previous truck" onClick={() => cycle(-1)} className="grid h-7 w-7 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="chevronLeft" /></button>
              <span className="tabular text-[12px] text-ink-2">{i + 1}/{trucks.length}</span>
              <button type="button" aria-label="Next truck" onClick={() => cycle(1)} className="grid h-7 w-7 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="chevronRight" /></button>
            </div>
          )}
        </div>
        <div className="mt-4"><Stepper current={stepOf(t)} /></div>
        <div className="mt-3 truncate text-ink-2">{t.task}</div>
      </div>

      <button type="button" onClick={() => selectAndCenter(t.id)} aria-label={`Select ${t.id}`}
        className="w-[230px] shrink-0 rounded-xl border border-[var(--card-border)] bg-[#F8FAFD] p-3 text-left transition-colors hover:border-info">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[15px] font-semibold">{t.id}{t.source === "device" && <LiveBadge />}</span>
          <StatusPill unit={t} />
        </div>
        <div className="mt-0.5 truncate text-[12px] text-ink-2">{String(t.meta?.carrier ?? "")} · {String(t.meta?.plate ?? "")}</div>
        <div className="mt-2 truncate text-[12px] text-ink-2">{String(t.meta?.route ?? "")}</div>
        <div className="mt-2 flex justify-between text-[12px]">
          <span className="text-ink-2">{t.docked_at ? nodeLabel(t.docked_at) : t.state === "gone" ? "Off site" : "Yard"}</span>
          <span className="tabular font-medium">{n}/{cap} pallets</span>
        </div>
        <Bar pct={cap ? (n / cap) * 100 : 0} className="mt-1.5" />
        <div className="mt-2 flex flex-wrap gap-1">
          {(t.cargo ?? []).map((id) => (
            <span key={id} title={String(useWorld.getState().units[id]?.meta?.contents ?? "")} className="rounded-md bg-white px-1.5 py-px text-[11px] font-medium text-ink-2 ring-1 ring-[var(--card-border)]">{id}</span>
          ))}
          {n === 0 && <span className="text-[12px] text-ink-2">Empty</span>}
        </div>
      </button>
    </div>
  );
}
