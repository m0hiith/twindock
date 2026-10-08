// Unit search. "/" focuses it from anywhere; arrows + Enter select and center the result.
import { useEffect, useMemo, useRef, useState } from "react";
import type { Unit } from "../contract";
import { useView, useWorld } from "../store/world";
import { Icon, kindIcon, kindLabel, LiveBadge, selectAndCenter, StatusPill } from "./ui";

const MAX_RESULTS = 8;
const EMPTY: Record<string, Unit> = {};

function haystack(u: Unit): string {
  return [u.id, u.label, u.kind, u.task, ...Object.values(u.meta ?? {})].filter((v) => v !== undefined).join(" ").toLowerCase();
}

export function Search() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const site = useWorld((s) => s.layout?.site);
  // Subscribe to units only while the results list is showing (units change at 20 Hz).
  const unitMap = useWorld((s) => (open && q.trim() ? s.units : EMPTY));
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

  const results = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return [];
    const order: Unit["kind"][] = ["forklift", "truck", "dock", "gateway", "pallet", "rack", "charger"];
    return units
      .filter((u) => haystack(u).includes(needle))
      .sort((a, b) => {
        const pa = a.id.toLowerCase().startsWith(needle) ? 0 : 1, pb = b.id.toLowerCase().startsWith(needle) ? 0 : 1;
        return pa - pb || order.indexOf(a.kind) - order.indexOf(b.kind) || a.id.localeCompare(b.id);
      })
      .slice(0, MAX_RESULTS);
  }, [q, units]);

  const siteHit = Boolean(site && q.trim() && `${site.id} ${site.name}`.toLowerCase().includes(q.trim().toLowerCase()));
  const count = results.length + (siteHit ? 1 : 0);

  const choose = (i: number) => {
    if (siteHit && i === 0) useView.getState().home();
    else {
      const u = results[i - (siteHit ? 1 : 0)];
      if (u) selectAndCenter(u.id);
    }
    setQ("");
    setOpen(false);
    input.current?.blur();
  };

  return (
    <div className="relative w-[340px]">
      <div className="flex h-9 items-center gap-2 rounded-xl border border-[var(--card-border)] bg-[#F6F6F6] px-3 focus-within:border-info focus-within:bg-white">
        <Icon name="search" className="text-ink-2" />
        <input ref={input} value={q} placeholder="Search sites, trucks, forklifts…" aria-label="Search"
          className="min-w-0 flex-1 bg-transparent text-[13px] text-ink outline-none placeholder:text-ink-2"
          onChange={(e) => { setQ(e.target.value); setActive(0); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(count - 1, a + 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
            else if (e.key === "Enter" && count > 0) choose(active);
            else if (e.key === "Escape") { setQ(""); input.current?.blur(); }
          }} />
        <kbd className="rounded-md border border-[var(--card-border)] bg-white px-1.5 text-[11px] font-medium text-ink-2">/</kbd>
      </div>
      {open && q.trim() && (
        <div className="card absolute inset-x-0 top-11 z-30 overflow-hidden p-1" role="listbox">
          {count === 0 && <div className="px-3 py-2.5 text-ink-2">No matches for "{q.trim()}"</div>}
          {siteHit && site && (
            <button type="button" role="option" aria-selected={active === 0} onMouseDown={() => choose(0)} onMouseEnter={() => setActive(0)}
              className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left ${active === 0 ? "bg-info-bg" : ""}`}>
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-idle-bg text-ink-2"><Icon name="dock" /></span>
              <span className="flex-1"><span className="font-semibold">{site.id}</span> <span className="text-ink-2">{site.name}</span></span>
              <span className="text-[12px] text-ink-2">Site</span>
            </button>
          )}
          {results.map((u, j) => {
            const i = j + (siteHit ? 1 : 0);
            return (
              <button key={u.id} type="button" role="option" aria-selected={active === i} onMouseDown={() => choose(i)} onMouseEnter={() => setActive(i)}
                className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left ${active === i ? "bg-info-bg" : ""}`}>
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-idle-bg text-ink-2"><Icon name={kindIcon[u.kind]} /></span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-1.5 font-semibold">{u.id}{u.source === "device" && <LiveBadge />}</span>
                  <span className="block truncate text-[12px] text-ink-2">{kindLabel[u.kind]} · {u.task ?? u.label}</span>
                </span>
                <StatusPill unit={u} />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
