// Camera presets (F4): the campus overview, each site, each building, and "follow" the selected vehicle or worker.
import { useEffect, useRef, useState } from "react";
import { useView, useWorld } from "../store/world";
import { send } from "../store/ws";

const icon = { width: 18, height: 18, fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export function CameraMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const layout = useWorld((s) => s.layout);
  const selected = useWorld((s) => s.selected);
  const unit = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const follow = useView((s) => s.follow);
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    window.addEventListener("pointerdown", onDown);
    return () => window.removeEventListener("pointerdown", onDown);
  }, [open]);
  useEffect(() => { if (!unit && follow) useView.getState().setFollow(false); }, [unit, follow]);
  const buildings = layout?.campus?.buildings ?? [];
  const go = (fn: () => void) => () => { fn(); setOpen(false); };
  const view = (site: string) => go(() => { useView.getState().setFollow(false); useView.getState().setSite(site); });
  const toBuilding = (id: string, x: number, z: number) => go(() => {
    const v = useView.getState();
    v.setFollow(false);
    if (useWorld.getState().selected) send({ type: "select_unit", unit_id: null });
    v.setBuilding(id);
    v.focusOn(x, z);
    v.setZoom(1.8);
  });
  const item = "block w-full rounded-lg px-2.5 py-1.5 text-left text-[13px] hover:bg-idle-bg";
  return (
    <div ref={ref} className="relative">
      <button type="button" aria-label="Camera views" title="Camera views: overview, buildings, follow" aria-expanded={open} onClick={() => setOpen(!open)}
        className={`grid h-9 w-9 place-items-center transition-colors ${follow ? "bg-[var(--accent)] text-white" : "text-ink hover:bg-info-bg"}`}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M3 8h3l2-3h8l2 3h3v11H3z" /><circle cx="12" cy="13" r="3.5" /></svg>
      </button>
      {open && (
        <div className="card absolute right-11 top-0 z-30 max-h-[70vh] w-60 overflow-y-auto p-1.5" role="menu">
          <div className="px-2.5 pb-1 pt-0.5 text-[11px] font-semibold uppercase tracking-wide text-ink-2">Views</div>
          <button type="button" role="menuitem" className={item} onClick={view("ALL")}>Campus overview</button>
          <button type="button" role="menuitem" className={item} onClick={view("WH-01")}>Warehouse and yard (WH-01)</button>
          <button type="button" role="menuitem" className={item} onClick={view("FAC-01")}>Factory and east side (FAC-01)</button>
          <div className="px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-2">Follow</div>
          <button type="button" role="menuitem" className={`${item} disabled:opacity-40`} disabled={!unit}
            onClick={go(() => useView.getState().setFollow(!follow))}>
            {follow ? `Stop following ${selected}` : unit ? `Follow ${unit.id} (${unit.kind})` : "Select a vehicle or worker to follow it"}
          </button>
          <div className="px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-2">Buildings</div>
          {buildings.map((b) => <button key={b.id} type="button" role="menuitem" className={item} onClick={toBuilding(b.id, b.x + b.w / 2, b.z + b.d / 2)}>{b.name}</button>)}
        </div>
      )}
    </div>
  );
}
