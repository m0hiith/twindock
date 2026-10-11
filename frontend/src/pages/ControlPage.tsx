// Control Room: the operator's manual control page, built for a phone first. Map on top, tabs
// below; on a wide screen the tabs become a side panel. Every action is an intent to the server.
import { useEffect, useMemo, useRef, useState } from "react";
import { destinationCandidates, destinationKeys } from "../control/candidates";
import { EventLog } from "../control/EventLog";
import { LogisticsPanel } from "../control/LogisticsPanel";
import { MaintenancePanel } from "../control/MaintenancePanel";
import { ProductionPanel } from "../control/ProductionPanel";
import { AlertsList } from "../hud/AlertsPanel";
import { DemoPanel } from "../control/DemoPanel";
import { GatewayPanel } from "../control/GatewayPanel";
import { MovePanel, UnitChips } from "../control/MovePanel";
import { ProposalSheet } from "../control/ProposalSheet";
import { SiteMap } from "../control/SiteMap";
import { useControl, type Checked } from "../control/state";
import { firstValid, useDryRuns } from "../control/useDryRuns";
import { AutoModeToggle } from "../hud/AutoModeToggle";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { Icon, TabButton } from "../hud/ui";
import type { LayoutNode } from "../layout";
import { send } from "../store/ws";
import { useWorld } from "../store/world";
import { Brand } from "../hud/Brand";
import { PageTabs } from "../hud/PageTabs";

type Tab = "move" | "gateway" | "log" | "factory" | "alerts" | "demo" | "maintenance" | "logistics";


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
  const decisions = useWorld((s) => s.control?.recommendations.length ?? 0);
  const [tab, setTab] = useState<Tab>("move");
  const layout = useWorld((s) => s.layout);
  const unit = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const proposal = useControl((s) => s.proposal);
  const { propose, setNotice } = useControl.getState();
  const warnCount = useWorld((s) => s.events.filter((e) => e.level !== "info").length);
  const openAlerts = useWorld((s) => (s.alerts?.alerts ?? []).filter((a) => a.state !== "resolved").length);

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
          <Brand compact title="" />
          <div className="min-w-0 flex-1">
            <div className="truncate text-[15px] font-semibold leading-tight">Control Room</div>
            <div className="hidden truncate text-[12px] text-ink-2 sm:block">{layout?.site.short}</div>
          </div>
          <ResetButton />
          <AutoModeToggle />
          <LivePill />
          <PageTabs className="hidden md:flex" />
        </header>
        <div className="flex justify-center px-3 empty:hidden"><FakeBoardBanner /></div>
        <div className="px-3 sm:px-4"><UnitChips /></div>
        <div className="relative mx-3 mb-2 mt-1 aspect-[57/86] max-h-[62vh] min-h-0 overflow-hidden rounded-2xl border border-[var(--card-border)] bg-[#F0F0F0] sm:mx-4 lg:mb-4 lg:aspect-auto lg:max-h-none lg:flex-1">
          <SiteMap checks={perNode} chosen={proposal?.target ?? null} path={proposal?.path ?? null} onNodeTap={onNodeTap}
            onBackground={() => { propose(null); setNotice(null); }} />
        </div>
      </div>

      <aside className="flex min-h-0 flex-1 flex-col lg:w-[420px] lg:flex-none lg:border-l lg:border-[var(--card-border)] lg:bg-white/60">
        <nav className="flex gap-1 overflow-x-auto px-3 pt-1 lg:px-4 lg:pt-4">
          <TabButton active={tab === "move"} onClick={() => setTab("move")}>Move</TabButton>
          <TabButton active={tab === "gateway"} onClick={() => setTab("gateway")}>Gateway</TabButton>
          <TabButton active={tab === "factory"} onClick={() => setTab("factory")}>Factory</TabButton>
          <TabButton active={tab === "maintenance"} onClick={() => setTab("maintenance")}>
            Maintenance{decisions > 0 && <span className="tabular rounded-full bg-warn-bg px-1.5 text-[11px] text-warn">{decisions}</span>}
          </TabButton>
          <TabButton active={tab === "logistics"} onClick={() => setTab("logistics")}>Logistics</TabButton>
          <TabButton active={tab === "demo"} onClick={() => setTab("demo")}>Demo</TabButton>
          <TabButton active={tab === "alerts"} onClick={() => setTab("alerts")}>
            Alerts{openAlerts > 0 && <span className="tabular rounded-full bg-crit-bg px-1.5 text-[11px] text-crit">{openAlerts}</span>}
          </TabButton>
          <TabButton active={tab === "log"} onClick={() => setTab("log")}>
            Event log{warnCount > 0 && <span className="tabular rounded-full bg-warn-bg px-1.5 text-[11px] text-warn">{warnCount}</span>}
          </TabButton>
        </nav>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-40 pt-3 lg:px-4">
          {tab === "move" && <MovePanel unit={unit} destinations={[...perNode.values()]} checking={checking} />}
          {tab === "gateway" && <GatewayPanel />}
          {tab === "factory" && <ProductionPanel />}
          {tab === "alerts" && <AlertsList />}
          {tab === "demo" && <DemoPanel />}
          {tab === "maintenance" && <MaintenancePanel />}
          {tab === "logistics" && <LogisticsPanel />}
          {tab === "log" && <EventLog />}
        </div>
      </aside>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex justify-center p-3 lg:left-auto lg:w-[420px]">
        <div className="pointer-events-auto w-full max-w-[520px]"><ProposalSheet /></div>
      </div>
    </div>
  );
}
