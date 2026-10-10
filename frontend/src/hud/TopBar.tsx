// Top bar: logo, search, site selector, Live clock, notifications (server events), operator.
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { Event } from "../contract";
import { useWorld } from "../store/world";
import { AutoModeToggle } from "./AutoModeToggle";
import { LivePill } from "./LivePill";
import { Search } from "./Search";
import { ago, Icon, useTick } from "./ui";
import { Brand } from "./Brand";
import { PageTabs } from "./PageTabs";

/** Closes a popover on outside click or Escape. */
function usePopover(): [boolean, (v: boolean) => void, React.RefObject<HTMLDivElement | null>] {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("pointerdown", onDown);
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("pointerdown", onDown); window.removeEventListener("keydown", onKey); };
  }, [open]);
  return [open, setOpen, ref];
}

function IconButton({ label, onClick, children }: { label: string; onClick?: () => void; children: ReactNode }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick}
      className="relative grid h-9 w-9 place-items-center rounded-xl text-ink transition-colors hover:bg-idle-bg">
      {children}
    </button>
  );
}

function SiteSelector() {
  const site = useWorld((s) => s.layout?.site);
  const [open, setOpen, ref] = usePopover();
  if (!site) return null;
  return (
    <div ref={ref} className="relative">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
        className="flex h-9 items-center gap-2 rounded-xl border border-[var(--card-border)] px-3 text-[13px] font-medium hover:bg-idle-bg">
        {site.short}
        <Icon name="chevronDown" size={14} className="text-ink-2" />
      </button>
      {open && (
        <div className="card absolute right-0 top-11 z-30 w-64 p-1">
          <div className="flex items-center gap-3 rounded-lg bg-info-bg px-2.5 py-2">
            <div className="flex-1">
              <div className="font-semibold">{site.id}</div>
              <div className="text-[12px] text-ink-2">{site.name}</div>
            </div>
            <Icon name="check" className="text-info" />
          </div>
          <div className="px-2.5 pb-1.5 pt-2 text-[12px] text-ink-2">This backend serves one site.</div>
        </div>
      )}
    </div>
  );
}

const levelTone: Record<Event["level"], string> = { info: "var(--info)", warn: "var(--warn)", error: "var(--crit)" };

function Notifications() {
  const events = useWorld((s) => s.events);
  const [open, setOpen, ref] = usePopover();
  const [readSeq, setReadSeq] = useState(0);
  useTick(open ? 5000 : 60_000);
  const unread = events.filter((e) => e.seq > readSeq && e.level !== "info").length;
  const latest = events.slice(-30).reverse();
  const toggle = () => {
    if (!open) setReadSeq(events.at(-1)?.seq ?? 0);
    setOpen(!open);
  };
  return (
    <div ref={ref} className="relative">
      <IconButton label={unread ? `Notifications, ${unread} new` : "Notifications"} onClick={toggle}>
        <Icon name="bell" size={18} />
        {unread > 0 && (
          <span className="tabular absolute right-1 top-1 grid h-4 min-w-4 place-items-center rounded-full bg-crit px-1 text-[10px] font-semibold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </IconButton>
      {open && (
        <div className="card absolute right-0 top-11 z-30 w-[360px] overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--card-border)] px-4 py-3">
            <span className="text-[15px] font-semibold">Event log</span>
            <span className="text-[12px] text-ink-2">{events.length} this session</span>
          </div>
          <div className="max-h-[360px] overflow-y-auto py-1">
            {latest.length === 0 && <div className="px-4 py-6 text-center text-ink-2">No events yet</div>}
            {latest.map((e) => (
              <div key={e.seq} className="flex gap-3 px-4 py-2">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: levelTone[e.level] }} />
                <div className="min-w-0 flex-1">
                  <div className="text-ink">{e.text}</div>
                  <div className="text-[12px] text-ink-2">{e.source} · {ago(e.server_ts_ms)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function TopBar() {
  return (
    <div className="card pointer-events-auto flex h-[60px] items-center gap-4 px-4">
      <Brand />
      <PageTabs className="ml-2" />
      <div className="ml-2 hidden xl:block"><Search /></div>
      <div className="ml-auto flex items-center gap-2">
        <SiteSelector />
        <AutoModeToggle />
        <LivePill />
        <Notifications />
        <span className="grid h-9 w-9 place-items-center rounded-full bg-info-bg text-info" title="Operator (no sign-in on this demo)">
          <Icon name="user" size={18} />
        </span>
      </div>
    </div>
  );
}
