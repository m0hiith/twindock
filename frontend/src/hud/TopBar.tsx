// Top bar: logo, search, site selector, Live clock, notifications (server events), operator.
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { Event } from "../contract";
import { useView, useWorld } from "../store/world";
import { AutoModeToggle } from "./AutoModeToggle";
import { LivePill } from "./LivePill";
import { FoldingSearch } from "./Search";
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

export function SiteSelector() {
  const sites = useWorld((s) => s.sites);
  const devices = useWorld((s) => s.devices);
  const current = useView((s) => s.site);
  const [open, setOpen, ref] = usePopover();
  const site = sites.find((s) => s.id === current) ?? sites[0];
  if (!site) return null;
  return (
    <div ref={ref} className="relative">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} aria-label={`Site: ${site.name}`}
        className="flex h-9 items-center gap-2 whitespace-nowrap rounded-xl border border-[var(--card-border)] px-3 text-[13px] font-medium hover:bg-idle-bg">
        <Icon name={site.kind === "factory" ? "factory" : "dock"} size={15} className="text-ink-2" />
        <span className="min-[1800px]:hidden">{site.id}</span><span className="hidden min-[1800px]:inline">{site.short}</span>
        <Icon name="chevronDown" size={14} className="text-ink-2" />
      </button>
      {open && (
        <div className="card absolute right-0 top-11 z-30 w-72 p-1">
          {sites.map((s) => {
            const all = Object.values(devices).filter((d) => d.site_id === s.id);
            const on = all.filter((d) => d.status === "online").length;
            const active = s.id === site.id;
            return (
              <button key={s.id} type="button" onClick={() => { useView.getState().setSite(s.id); setOpen(false); }}
                className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left ${active ? "bg-info-bg" : "hover:bg-idle-bg"}`}>
                <Icon name={s.kind === "factory" ? "factory" : "dock"} size={18} className="text-ink-2" />
                <div className="min-w-0 flex-1">
                  <div className="font-semibold">{s.id}</div>
                  <div className="truncate text-[12px] text-ink-2">{s.name} · {on}/{all.length} devices online</div>
                </div>
                {active && <Icon name="check" className="text-info" />}
              </button>
            );
          })}
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
    <div className="card pointer-events-auto flex h-[60px] items-center gap-2 px-4">
      <Brand tight />
      {/* Below 1800 px the bar is too narrow for everything: the logo keeps its mark, the site selector its id,
          and the search folds into an icon that opens over the bar when focused (click or "/"). */}
      <PageTabs className="ml-1" />
      <FoldingSearch />
      <div className="ml-auto flex shrink-0 items-center gap-2 whitespace-nowrap">
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
