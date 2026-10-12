// Search (F4): buildings, devices, vehicles, workers (by id or role), sites and alerts. "/" focuses it from anywhere; arrows + Enter
// choose, and the camera flies to the result and opens its card.
import { useEffect, useMemo, useRef, useState } from "react";
import type { Unit } from "../contract";
import { TYPE_LABEL } from "../fleet/logic";
import { useView, useWorld } from "../store/world";
import { send } from "../store/ws";
import { flyTo } from "./AlertsPanel";
import { Icon, kindIcon, kindLabel, LiveBadge, selectAndCenter, SimBadge, StatusPill, type IconName } from "./ui";

const MAX_RESULTS = 9;
const EMPTY: Record<string, Unit> = {};

function haystack(u: Unit): string {
  return [u.id, u.label, u.kind, u.task, ...Object.values(u.meta ?? {})].filter((v) => v !== undefined).join(" ").toLowerCase();
}

interface Item {
  key: string; icon: IconName; title: string; sub: string; tag: string; badge?: "live" | "sim"; unit?: Unit; run: () => void; rank: number;
}

export function Search() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const layout = useWorld((s) => s.layout);
  const sites = useWorld((s) => s.sites);
  // Subscribe to the fast-changing stores only while the results list is showing (units change at 20 Hz).
  const unitMap = useWorld((s) => (open && q.trim() ? s.units : EMPTY));
  const devices = useWorld((s) => (open && q.trim() ? s.devices : null));
  const alerts = useWorld((s) => (open && q.trim() ? s.alerts?.alerts : undefined));
  const units = useMemo(() => Object.values(unitMap), [unitMap]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.metaKey || e.ctrlKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      e.preventDefault();
      input.current?.focus();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const items = useMemo((): Item[] => {
    const needle = q.trim().toLowerCase();
    if (!needle) return [];
    const starts = (id: string) => (id.toLowerCase().startsWith(needle) ? 0 : 1);
    const out: Item[] = [];
    for (const s of sites) {
      if (`${s.id} ${s.name} ${s.short}`.toLowerCase().includes(needle)) {
        out.push({ key: `site-${s.id}`, icon: s.kind === "factory" ? "factory" : "dock", title: s.id, sub: s.name, tag: "Site", rank: 0, run: () => useView.getState().setSite(s.id) });
      }
    }
    const buildings = [...(layout?.campus?.buildings ?? []).map((b) => ({ id: b.id, name: b.name, x: b.x + b.w / 2, z: b.z + b.d / 2, kind: b.kind, campus: true })),
      ...(layout?.buildings ?? []).map((b) => ({ id: b.id, name: b.label ?? b.id, x: b.x + b.w / 2, z: b.z + b.d / 2, kind: b.kind, campus: false }))];
    for (const b of buildings) {
      if (`${b.id} ${b.name} ${b.kind}`.toLowerCase().includes(needle)) {
        out.push({ key: `b-${b.id}`, icon: "dock", title: b.name, sub: b.id, tag: "Building", rank: 1 + starts(b.name) * 0.1, run: () => {
          const v = useView.getState();
          v.setFollow(false);
          if (b.campus) { if (useWorld.getState().selected) send({ type: "select_unit", unit_id: null }); v.setBuilding(b.id); }
          v.focusOn(b.x, b.z);
          v.setZoom(1.8);
        } });
      }
    }
    for (const u of units) {
      if (!haystack(u).includes(needle)) continue;
      const role = u.kind === "worker" ? String(u.meta?.role ?? "").replace(/_/g, " ") : "";
      out.push({ key: `u-${u.id}`, icon: kindIcon[u.kind], title: u.id, sub: `${role ? `${role} · ` : `${kindLabel[u.kind]} · `}${u.task ?? u.label ?? ""}`, tag: kindLabel[u.kind],
        badge: u.source === "device" ? "live" : u.source === "sim" ? "sim" : undefined, unit: u, rank: 2 + starts(u.id) * 0.1, run: () => selectAndCenter(u.id) });
    }
    for (const d of Object.values(devices ?? {})) {
      if (d.type === "gateway") continue;
      if (`${d.id} ${d.label ?? ""} ${d.type} ${TYPE_LABEL[d.type]} ${d.kit ?? ""}`.toLowerCase().includes(needle)) {
        out.push({ key: `d-${d.id}`, icon: "sensor", title: d.id, sub: `${TYPE_LABEL[d.type]} · ${d.label ?? ""}`, tag: "Device", badge: d.source === "device" ? "live" : "sim", rank: 3 + starts(d.id) * 0.1,
          run: () => { useView.getState().setShowDevices(true); send({ type: "select_unit", unit_id: d.id }); useView.getState().focusOn(d.x, d.z); } });
      }
    }
    for (const a of alerts ?? []) {
      if (a.state === "resolved") continue;
      if (`${a.title} ${a.message} ${a.subject_id}`.toLowerCase().includes(needle)) {
        out.push({ key: `a-${a.id}`, icon: "alert", title: a.title, sub: a.message, tag: a.severity === "critical" ? "Critical alert" : "Alert", rank: 4, run: () => flyTo(a, location.pathname.startsWith("/monitor")) });
      }
    }
    return out.sort((a, b) => a.rank - b.rank || a.title.localeCompare(b.title)).slice(0, MAX_RESULTS);
  }, [q, sites, layout, units, devices, alerts]);

  const choose = (i: number) => {
    items[i]?.run();
    setQ("");
    setOpen(false);
    input.current?.blur();
  };

  return (
    <div className="relative w-full">
      <div onClick={() => input.current?.focus()}
        className="flex h-9 cursor-text items-center gap-2 overflow-hidden rounded-xl border border-[var(--card-border)] bg-[#F6F6F6] px-2.5 focus-within:border-info focus-within:bg-white">
        <Icon name="search" className="shrink-0 text-ink-2" />
        <input ref={input} value={q} placeholder="Search buildings, devices, vehicles, workers, alerts…" aria-label="Search"
          className="min-w-0 flex-1 bg-transparent text-[13px] text-ink outline-none placeholder:text-ink-2"
          onChange={(e) => { setQ(e.target.value); setActive(0); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(items.length - 1, a + 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
            else if (e.key === "Enter" && items.length > 0) choose(active);
            else if (e.key === "Escape") { setQ(""); input.current?.blur(); }
          }} />
        <kbd className="shrink-0 rounded-md border border-[var(--card-border)] bg-white px-1.5 text-[11px] font-medium text-ink-2">/</kbd>
      </div>
      {open && q.trim() && (
        <div className="card absolute inset-x-0 top-11 z-30 overflow-hidden p-1" role="listbox">
          {items.length === 0 && <div className="px-3 py-2.5 text-ink-2">No matches for "{q.trim()}"</div>}
          {items.map((it, i) => (
            <button key={it.key} type="button" role="option" aria-selected={active === i} onMouseDown={() => choose(i)} onMouseEnter={() => setActive(i)}
              className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left ${active === i ? "bg-info-bg" : ""}`}>
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-idle-bg text-ink-2"><Icon name={it.icon} /></span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 font-semibold">{it.title}{it.badge === "live" && <LiveBadge />}{it.badge === "sim" && <SimBadge />}</span>
                <span className="block truncate text-[12px] text-ink-2">{it.sub}</span>
              </span>
              {it.unit ? <StatusPill unit={it.unit} /> : <span className="shrink-0 text-[12px] text-ink-2">{it.tag}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** The search for crowded headers: a full box from 1800 px; below that an icon that opens over the header when
 *  focused (click or "/"), so it never pushes the page tabs out. */
export function FoldingSearch() {
  return (
    <div className="relative h-9 w-9 shrink-0 min-[1800px]:w-auto min-[1800px]:min-w-[200px] min-[1800px]:max-w-[340px] min-[1800px]:flex-1">
      <div className="absolute left-0 top-0 z-30 w-9 transition-[width] duration-150 focus-within:w-[340px] min-[1800px]:static min-[1800px]:w-full min-[1800px]:focus-within:w-full"><Search /></div>
    </div>
  );
}
