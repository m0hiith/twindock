// Control Room: the operator's manual control page, built for a phone first. Map on top, tabs
// below; on a wide screen the tabs become a side panel. Every action is an intent to the server.
import { useEffect, useMemo, useRef, useState } from "react";
import { destinationCandidates, destinationKeys } from "../control/candidates";
import { EventLog } from "../control/EventLog";
import { GatewayPanel } from "../control/GatewayPanel";
import { MovePanel, UnitChips } from "../control/MovePanel";
import { ProposalSheet } from "../control/ProposalSheet";
import { SiteMap } from "../control/SiteMap";
import { useControl, type Checked } from "../control/state";
import { firstValid, useDryRuns } from "../control/useDryRuns";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { Icon, TabButton } from "../hud/ui";
import type { LayoutNode } from "../layout";
import { send } from "../store/ws";
import { useWorld } from "../store/world";

type Tab = "move" | "gateway" | "log";

function AutoModeToggle() {
  const auto = useWorld((s) => s.autoMode);
  const run = useControl((s) => s.run);
  const [waiting, setWaiting] = useState(false);
  const toggle = async () => {
    setWaiting(true);
    await run({ type: "set_auto_mode", enabled: !auto }, `Auto mode ${auto ? "off" : "on"}`);
    setWaiting(false);
  };
  return (
    <button type="button" role="switch" aria-checked={auto} onClick={toggle} disabled={waiting}
      className={`flex h-9 items-center gap-2 rounded-xl border px-3 text-[13px] font-medium transition-colors ${auto ? "border-warn bg-warn-bg text-warn" : "border-[var(--card-border)] bg-white text-ink"}`}>
      <span className={`relative h-4 w-7 rounded-full transition-colors ${auto ? "bg-warn" : "bg-[#D5DAE5]"}`}>
        <span className={`absolute top-0.5 h-3 w-3 rounded-full bg-white transition-[left] ${auto ? "left-3.5" : "left-0.5"}`} />
      </span>
      Auto{waiting ? "…" : auto ? " on" : " off"}
    </button>
  );
}

/** One click restores the seed world (POST /api/reset). The page then updates from the
 *  server's world_snapshot, like every other change. */
function ResetButton() {
  const [state, setState] = useState<"idle" | "busy" | "failed">("idle");
  const reset = async () => {
    setState("busy");
    try {
      const r = await fetch("/api/reset", { method: "POST" });
      if (!r.ok) throw new Error(String(r.status));
      useControl.getState().propose(null);
      setState("idle");
    } catch {
      setState("failed");
      setTimeout(() => setState("idle"), 3000);
    }
  };
  return (
    <button type="button" onClick={reset} disabled={state === "busy"} title="Restore the seed world"
      className={`flex h-9 items-center gap-1.5 rounded-xl border px-3 text-[13px] font-medium transition-colors ${state === "failed" ? "border-crit bg-crit-bg text-crit" : "border-[var(--card-border)] bg-white text-ink hover:bg-idle-bg"}`}>
      <Icon name="reset" size={15} />
      <span className="hidden sm:inline">{state === "busy" ? "Resetting…" : state === "failed" ? "Reset failed" : "Reset world"}</span>
      <span className="sr-only sm:hidden">Reset world</span>
    </button>
  );
}

export function ControlPage() {
  const [tab, setTab] = useState<Tab>("move");
  const layout = useWorld((s) => s.layout);
  const unit = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const proposal = useControl((s) => s.proposal);
  const { propose, setNotice } = useControl.getState();
  const warnCount = useWorld((s) => s.events.filter((e) => e.level !== "info").length);

  // Re-derive candidates only when what they depend on changes, not on every position update.
  const candKey = unit ? `${unit.id}:${unit.kind}:${Boolean(unit.carrying)}:${unit.source}` : "";
  const dest = useMemo(() => destinationCandidates(unit, layout), [candKey, layout]); // eslint-disable-line react-hooks/exhaustive-deps
  const manual = unit !== undefined && unit.source !== "device";
  const { results, checking } = useDryRuns(manual ? unit.id : null, dest.list);

  const perNode = useMemo(() => {
    const m = new Map<string, Checked>();
    if (!unit) return m;
    for (const n of dest.nodes) {
      const c = firstValid(results, destinationKeys(unit, n));
      if (c) m.set(n.id, c);
    }
    return m;
  }, [results, dest, unit?.id, unit?.carrying]); // eslint-disable-line react-hooks/exhaustive-deps

  // Drop a proposal that no longer belongs to the selected unit (someone else changed selection).
  useEffect(() => {
    if (proposal && proposal.unit_id !== unit?.id) propose(null);
  }, [proposal, unit?.id, propose]);

  // /control?unit=FL-01 (the twin's "Open in Control Room") selects that unit once connected.
  const conn = useWorld((s) => s.conn);
  const wanted = useRef(new URLSearchParams(location.search).get("unit"));
  useEffect(() => {
    if (conn !== "live" || !wanted.current) return;
    send({ type: "select_unit", unit_id: wanted.current });
    wanted.current = null;
    history.replaceState(null, "", "/control");
  }, [conn]);

  const onNodeTap = (n: LayoutNode) => {
    if (!unit || !manual) return;
    const c = perNode.get(n.id);
    if (!c) setNotice(`${n.label ?? n.id}: still checking with the server`);
    else if (!c.ok) setNotice(`${n.label ?? n.id}: ${c.reason ?? "not available"}`);
    else propose({ ...c, unit_id: unit.id });
  };

  return (
    <div className="flex h-full flex-col bg-[var(--ground)] lg:flex-row">
      <div className="flex min-h-0 flex-col lg:flex-1">
        <header className="flex items-center gap-2 px-3 pb-2 pt-3 sm:px-4">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-structure text-white"><Icon name="logo" size={17} strokeWidth={2.2} /></span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[15px] font-semibold leading-tight">Control Room</div>
            <div className="hidden truncate text-[12px] text-ink-2 sm:block">{layout?.site.short}</div>
          </div>
          <ResetButton />
          <AutoModeToggle />
          <LivePill />
          <a href="/twin" className="hidden h-9 items-center rounded-xl border border-[var(--card-border)] bg-white px-3 text-[13px] font-medium sm:flex">Open twin</a>
        </header>
        <div className="flex justify-center px-3 empty:hidden"><FakeBoardBanner /></div>
        <div className="px-3 sm:px-4"><UnitChips /></div>
        <div className="relative mx-3 mb-2 mt-1 aspect-[57/86] max-h-[62vh] min-h-0 overflow-hidden rounded-2xl border border-[var(--card-border)] bg-[#EEF1F8] sm:mx-4 lg:mb-4 lg:aspect-auto lg:max-h-none lg:flex-1">
          <SiteMap checks={perNode} chosen={proposal?.target ?? null} path={proposal?.path ?? null} onNodeTap={onNodeTap}
            onBackground={() => { propose(null); setNotice(null); }} />
        </div>
      </div>

      <aside className="flex min-h-0 flex-1 flex-col lg:w-[420px] lg:flex-none lg:border-l lg:border-[var(--card-border)] lg:bg-white/60">
        <nav className="flex gap-1 px-3 pt-1 lg:px-4 lg:pt-4">
          <TabButton active={tab === "move"} onClick={() => setTab("move")}>Move</TabButton>
          <TabButton active={tab === "gateway"} onClick={() => setTab("gateway")}>Gateway</TabButton>
          <TabButton active={tab === "log"} onClick={() => setTab("log")}>
            Event log{warnCount > 0 && <span className="tabular rounded-full bg-warn-bg px-1.5 text-[11px] text-warn">{warnCount}</span>}
          </TabButton>
        </nav>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-40 pt-3 lg:px-4">
          {tab === "move" && <MovePanel unit={unit} destinations={[...perNode.values()]} checking={checking} />}
          {tab === "gateway" && <GatewayPanel />}
          {tab === "log" && <EventLog />}
        </div>
      </aside>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex justify-center p-3 lg:left-auto lg:w-[420px]">
        <div className="pointer-events-auto w-full max-w-[520px]"><ProposalSheet /></div>
      </div>
    </div>
  );
}
