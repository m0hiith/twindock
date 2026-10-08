// Selected unit, quick actions and the destination list. Every option shown here was checked by
// the server (dry run); disabled ones carry the server's reason.
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import type { Unit } from "../contract";
import { Icon, kindIcon, LiveBadge, nodeLabel, StatusPill } from "../hud/ui";
import { send } from "../store/ws";
import { useWorld } from "../store/world";
import { quickCandidates, quickKinds, quickLabel, type QuickKind } from "./candidates";
import { actionVerb, useControl, type Checked } from "./state";
import { useDryRuns } from "./useDryRuns";

export function UnitChips() {
  const movers = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "forklift" || u.kind === "truck")
    .sort((a, b) => a.kind.localeCompare(b.kind) || a.id.localeCompare(b.id))));
  const selected = useWorld((s) => s.selected);
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]">
      {movers.map((u) => {
        const on = u.id === selected;
        return (
          <button key={u.id} type="button" onClick={() => send({ type: "select_unit", unit_id: on ? null : u.id })} aria-pressed={on}
            className={`flex h-10 shrink-0 items-center gap-1.5 rounded-xl border px-3 text-[13px] font-semibold transition-colors ${on ? "border-info bg-info text-white" : "border-[var(--card-border)] bg-white text-ink"}`}>
            <Icon name={kindIcon[u.kind]} size={15} />
            {u.id}
            {u.source === "device" && <span className={`h-1.5 w-1.5 rounded-full ${on ? "bg-white" : "bg-live"}`} title="Tracked by the board" />}
          </button>
        );
      })}
    </div>
  );
}

function OptionRow({ c, onPick }: { c: Checked; onPick: (c: Checked) => void }) {
  return (
    <button type="button" disabled={!c.ok} onClick={() => onPick(c)}
      className="flex min-h-11 w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition-colors enabled:hover:bg-info-bg disabled:cursor-not-allowed">
      <span className="min-w-0 flex-1">
        <span className={`block font-medium ${c.ok ? "text-ink" : "text-idle"}`}>{c.label}</span>
        <span className={`block truncate text-[12px] ${c.ok ? "text-ink-2" : "text-idle"}`}>
          {c.ok ? [actionVerb[c.action].split(" ")[0], c.sub].filter(Boolean).join(" · ") : c.reason}
        </span>
      </span>
      {c.ok && <Icon name="chevronRight" size={14} className="text-ink-2" />}
    </button>
  );
}

function QuickPicker({ unit, kind, onClose }: { unit: Unit; kind: QuickKind; onClose: () => void }) {
  const layout = useWorld((s) => s.layout);
  const units = useWorld((s) => s.units);
  const candidates = layout ? quickCandidates(kind, units, layout) : [];
  const { results, checking } = useDryRuns(unit.id, candidates);
  const propose = useControl((s) => s.propose);
  const list = candidates.map((c) => results.get(c.key)).filter((r): r is Checked => r !== undefined)
    .sort((a, b) => Number(b.ok) - Number(a.ok));
  return (
    <div className="mt-2 rounded-xl border border-[var(--card-border)] bg-[#F8FAFD] p-1.5">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-[13px] font-semibold">{quickLabel[kind]}</span>
        <button type="button" onClick={onClose} aria-label="Close" className="grid h-8 w-8 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="close" size={14} /></button>
      </div>
      {candidates.length === 0 && <div className="px-2.5 pb-2 text-ink-2">Nothing to choose from right now</div>}
      {list.length === 0 && candidates.length > 0 && <div className="px-2.5 pb-2 text-ink-2">{checking ? "Checking with the server…" : "No answer from the server"}</div>}
      <div className="max-h-64 overflow-y-auto">
        {list.map((c) => <OptionRow key={c.key} c={c} onPick={(x) => { propose({ ...x, unit_id: unit.id }); onClose(); }} />)}
      </div>
    </div>
  );
}

export function MovePanel({ unit, destinations, checking }: { unit: Unit | undefined; destinations: Checked[]; checking: boolean }) {
  const [quick, setQuick] = useState<QuickKind | null>(null);
  const [openFor, setOpenFor] = useState<string | null>(null);
  const propose = useControl((s) => s.propose);
  if (openFor !== (unit?.id ?? null)) { setOpenFor(unit?.id ?? null); setQuick(null); }

  if (!unit) {
    return <div className="rounded-xl bg-idle-bg px-4 py-6 text-center text-ink-2">Tap a forklift or truck on the map, or pick one above.</div>;
  }
  if (unit.kind !== "forklift" && unit.kind !== "truck") {
    return <div className="rounded-xl bg-idle-bg px-4 py-6 text-center text-ink-2">{unit.label ?? unit.id} can't be moved. Select a forklift or truck.</div>;
  }
  const device = unit.source === "device";
  const ok = destinations.filter((d) => d.ok), blocked = destinations.filter((d) => !d.ok);

  return (
    <div>
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-info-bg text-info"><Icon name={kindIcon[unit.kind]} size={20} /></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[17px] font-semibold">{unit.id}{device && <LiveBadge />}<StatusPill unit={unit} /></div>
          <div className="truncate text-ink-2">{unit.task}</div>
          {unit.kind === "forklift" && unit.plan && unit.plan.length > 0 && (
            <div className="mt-0.5 truncate text-[12px] text-ink-2">BTN0 next: {actionVerb[unit.plan[0]!.action]} {nodeLabel(unit.plan[0]!.node)}</div>
          )}
        </div>
      </div>

      {device ? (
        <div className="mt-3 rounded-xl bg-[#F3EDFF] px-3 py-2.5 text-[13px] text-live">Tracked by the board. Manual moves are disabled.</div>
      ) : (
        <>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {quickKinds(unit).map((k) => (
              <button key={k} type="button" onClick={() => setQuick(quick === k ? null : k)} aria-expanded={quick === k}
                className={`min-h-11 rounded-xl border px-3 py-2 text-left text-[13px] font-medium transition-colors ${quick === k ? "border-info bg-info-bg text-info" : "border-[var(--card-border)] bg-white hover:border-info"}`}>
                {quickLabel[k]}
              </button>
            ))}
          </div>
          {quick && <QuickPicker unit={unit} kind={quick} onClose={() => setQuick(null)} />}

          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-[13px] font-semibold">Destinations</span>
            <span className="text-[12px] text-ink-2">{checking ? "Checking…" : `${ok.length} available`}</span>
          </div>
          <div className="mt-1">
            {ok.map((c) => <OptionRow key={c.key} c={c} onPick={(x) => propose({ ...x, unit_id: unit.id })} />)}
            {blocked.length > 0 && <div className="mt-2 px-2.5 text-[12px] font-medium text-ink-2">Unavailable</div>}
            {blocked.map((c) => <OptionRow key={c.key} c={c} onPick={() => undefined} />)}
          </div>
        </>
      )}
    </div>
  );
}
