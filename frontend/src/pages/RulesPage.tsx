// /rules: every rule in backend/rules/*.yaml in plain language, plus the alert history.
import { AlertRow } from "../hud/AlertsPanel";
import { Brand } from "../hud/Brand";
import { LivePill } from "../hud/LivePill";
import { PageTabs } from "../hud/PageTabs";
import { Pill, useTick } from "../hud/ui";
import { useWorld } from "../store/world";

const SUBJECT = { machine: "Machines", worker: "Workers", device: "Devices", gateway: "Real board", line: "Production line", site: "Campus" } as const;
const TONE = { critical: "crit", warning: "warn", info: "info" } as const;

export function RulesPage() {
  const data = useWorld((s) => s.alerts);
  useTick(5000);
  const rules = data?.rules ?? [];
  const alerts = data?.alerts ?? [];
  const openBy = (id: string) => alerts.filter((a) => a.rule_id === id && a.state !== "resolved").length;
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4">
          <Brand tight />
          <PageTabs className="ml-2" />
          <div className="ml-auto"><LivePill /></div>
        </header>
        <div className="flex gap-4">
          <section className="card min-w-0 flex-[3] p-4" aria-label="Rules">
            <div className="flex items-baseline justify-between">
              <h1 className="text-[20px] font-semibold">Rules</h1>
              <span className="text-[12px] text-ink-2">{rules.length} rules · backend/rules/*.yaml</span>
            </div>
            <p className="mt-1 text-[13px] text-ink-2">
              An alert is raised when a rule's condition holds for its whole duration, and resolves as soon as it no longer
              holds. Values that never arrived (or are stale) never trigger a rule.
            </p>
            <div className="mt-3 divide-y divide-[var(--card-border)]">
              {rules.map((r) => (
                <div key={r.id} className="flex items-start gap-3 py-3">
                  <div className="w-[92px] shrink-0 pt-0.5"><Pill tone={TONE[r.severity]}>{r.severity === "critical" ? "Critical" : r.severity === "warning" ? "Warning" : "Info"}</Pill></div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{r.name}</span>
                      <span className="text-[12px] text-ink-2">{SUBJECT[r.subject]}{r.for_s ? ` · after ${r.for_s} s` : ""}</span>
                      {!r.enabled && <span className="text-[12px] text-ink-2">· disabled</span>}
                    </div>
                    <div className="mt-0.5 text-[13px] text-ink">{r.plain}</div>
                  </div>
                  {openBy(r.id) > 0 && <span className="tabular shrink-0 rounded-full bg-warn-bg px-2 py-0.5 text-[12px] font-medium text-warn">{openBy(r.id)} open</span>}
                </div>
              ))}
            </div>
          </section>
          <section className="card min-w-0 flex-[2] self-start p-4" aria-label="Alert history">
            <h2 className="text-[15px] font-semibold">Alerts</h2>
            {alerts.length === 0 && <div className="py-4 text-ink-2">No alerts yet</div>}
            <div className="divide-y divide-[var(--card-border)]">{alerts.map((a) => <AlertRow key={a.id} a={a} compact />)}</div>
          </section>
        </div>
      </div>
    </div>
  );
}
