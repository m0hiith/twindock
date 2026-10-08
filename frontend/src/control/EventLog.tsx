// Every command this screen sent, with the server's ack or reject, merged with the server's
// broadcast events (physical buttons, auto mode, LED timeouts...). Newest first.
import type { Event } from "../contract";
import { ago, useTick } from "../hud/ui";
import { serverClock, useWorld } from "../store/world";
import { useControl, type LogEntry } from "./state";

type Row = { kind: "cmd"; t: number; e: LogEntry } | { kind: "event"; t: number; e: Event };

const levelColour: Record<Event["level"], string> = { info: "var(--info)", warn: "var(--warn)", error: "var(--crit)" };

export function EventLog() {
  const log = useControl((s) => s.log);
  const events = useWorld((s) => s.events);
  useTick(5000);
  const rows: Row[] = [
    ...log.map((e): Row => ({ kind: "cmd", t: e.sent_ms + serverClock.offsetMs, e })),
    ...events.map((e): Row => ({ kind: "event", t: e.server_ts_ms, e })),
  ].sort((a, b) => b.t - a.t).slice(0, 80);

  if (rows.length === 0) return <div className="rounded-xl bg-idle-bg px-4 py-6 text-center text-ink-2">No commands or events yet</div>;
  return (
    <ol className="divide-y divide-[var(--card-border)]">
      {rows.map((r) => {
        if (r.kind === "event") {
          const e = r.e;
          return (
            <li key={`e${e.seq}`} className="flex gap-3 py-2.5">
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: levelColour[e.level] }} />
              <div className="min-w-0 flex-1">
                <div>{e.text}</div>
                <div className="text-[12px] text-ink-2">{e.source} · {ago(e.server_ts_ms)}</div>
              </div>
            </li>
          );
        }
        const { e } = r;
        const state = e.ack === null ? "pending" : e.ack.type === "local_failure" ? "undelivered" : e.ack.ok ? "ok" : "rejected";
        return (
          <li key={`c${e.cmd_id}`} className="flex gap-3 py-2.5">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${state === "ok" ? "bg-ok" : state === "rejected" ? "bg-crit" : "bg-idle"}`} />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-medium">{e.text}</span>
                <span className={`shrink-0 rounded-full px-2 py-px text-[11px] font-semibold ${state === "ok" ? "bg-ok-bg text-ok" : state === "rejected" ? "bg-crit-bg text-crit" : "bg-idle-bg text-idle"}`}>
                  {state === "ok" ? "Accepted" : state === "rejected" ? "Rejected" : state === "undelivered" ? "Not delivered" : "Sent"}
                </span>
              </div>
              <div className="text-[12px] text-ink-2">
                You · {ago(r.t)}{e.ack && (e.ack.type === "local_failure" || !e.ack.ok) && e.ack.reason ? ` · ${e.ack.reason}` : ""}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
