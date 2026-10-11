// Building blocks shared by the /wiring views: pan/zoom for the SVG canvases, hover tooltip, badges.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Pill } from "../hud/ui";
import { statusHelp, statusLabel, statusTone, type Status } from "./model";

export interface HoverInfo {
  x: number;
  y: number;
  title: string;
  rows: [string, string][];
}

export function Tooltip({ info }: { info: HoverInfo | null }) {
  if (!info) return null;
  return (
    <div className="card pointer-events-none absolute z-20 max-w-[320px] px-3 py-2 text-[13px]"
      style={{ left: info.x + 14, top: info.y + 14 }}>
      <div className="font-semibold">{info.title}</div>
      {info.rows.length > 0 && (
        <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
          {info.rows.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-ink-2">{k}</dt>
              <dd className="font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

export function StatusBadge({ status, help = false }: { status: Status; help?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Pill tone={statusTone[status]}>{statusLabel[status]}</Pill>
      {help && <span className="text-[13px] text-ink-2">{statusHelp[status]}</span>}
    </span>
  );
}

export interface ViewBox { x: number; y: number; w: number; h: number }

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 4;

/**
 * Wheel to zoom around the pointer, drag to pan. Returns `dragged()` so click handlers can ignore
 * the click that ends a drag.
 */
export function usePanZoom(full: { x?: number; y?: number; w: number; h: number }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [vb, setVb] = useState<ViewBox>({ x: full.x ?? 0, y: full.y ?? 0, w: full.w, h: full.h });
  const drag = useRef<{ x: number; y: number; vb: ViewBox; moved: boolean } | null>(null);
  const lastDragMoved = useRef(false);

  const toSvg = useCallback((clientX: number, clientY: number, box: ViewBox) => {
    const el = svgRef.current;
    if (!el) return { x: 0, y: 0 };
    const r = el.getBoundingClientRect();
    // preserveAspectRatio="xMidYMid meet": one scale for both axes, content centred.
    const s = Math.min(r.width / box.w, r.height / box.h);
    const ox = (r.width - box.w * s) / 2;
    const oy = (r.height - box.h * s) / 2;
    return { x: box.x + (clientX - r.left - ox) / s, y: box.y + (clientY - r.top - oy) / s };
  }, []);

  const zoomBy = useCallback((f: number, at?: { x: number; y: number }) => {
    setVb((v) => {
      const zoom = full.w / v.w;
      const nz = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * f));
      const w = full.w / nz;
      const h = full.h / nz;
      const cx = at?.x ?? v.x + v.w / 2;
      const cy = at?.y ?? v.y + v.h / 2;
      return { x: cx - ((cx - v.x) / v.w) * w, y: cy - ((cy - v.y) / v.h) * h, w, h };
    });
  }, [full.w, full.h]);

  const fit = useCallback(() => setVb({ x: full.x ?? 0, y: full.y ?? 0, w: full.w, h: full.h }), [full]);

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      setVb((v) => {
        const p = toSvg(e.clientX, e.clientY, v);
        const zoom = full.w / v.w;
        const nz = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * Math.exp(-e.deltaY * 0.0015)));
        const w = full.w / nz;
        const h = full.h / nz;
        return { x: p.x - ((p.x - v.x) / v.w) * w, y: p.y - ((p.y - v.y) / v.h) * h, w, h };
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [toSvg, full.w, full.h]);

  const handlers = {
    onPointerDown: (e: React.PointerEvent<SVGSVGElement>) => {
      if (e.button !== 0) return;
      drag.current = { x: e.clientX, y: e.clientY, vb, moved: false };
    },
    onPointerMove: (e: React.PointerEvent<SVGSVGElement>) => {
      const d = drag.current;
      if (!d) return;
      const dx = e.clientX - d.x;
      const dy = e.clientY - d.y;
      if (!d.moved && Math.hypot(dx, dy) < 4) return;
      if (!d.moved) svgRef.current?.setPointerCapture(e.pointerId);
      d.moved = true;
      const r = svgRef.current?.getBoundingClientRect();
      if (!r) return;
      const s = Math.min(r.width / d.vb.w, r.height / d.vb.h);
      setVb({ ...d.vb, x: d.vb.x - dx / s, y: d.vb.y - dy / s });
    },
    onPointerUp: () => {
      lastDragMoved.current = drag.current?.moved ?? false;
      drag.current = null;
    },
  };

  /** Callback ref for the <svg>; `extra` also receives the element (e.g. for export). */
  const attach = useCallback((extra?: (el: SVGSVGElement | null) => void) => (el: SVGSVGElement | null) => {
    svgRef.current = el;
    extra?.(el);
  }, []);

  return {
    attach, vb, handlers, fit, zoomBy,
    zoom: full.w / vb.w,
    /** True right after a drag, so the click that ends it does not select a part. */
    dragged: () => lastDragMoved.current,
    viewBox: `${vb.x} ${vb.y} ${vb.w} ${vb.h}`,
  };
}

export function ZoomControls({ onIn, onOut, onFit, children }: { onIn: () => void; onOut: () => void; onFit: () => void; children?: ReactNode }) {
  const btn = "grid h-9 w-9 place-items-center rounded-xl text-[17px] font-medium text-ink hover:bg-idle-bg";
  return (
    <div className="card absolute right-3 top-3 z-10 flex items-center gap-0.5 p-1" data-export-skip>
      <button type="button" className={btn} onClick={onIn} aria-label="Zoom in" title="Zoom in">+</button>
      <button type="button" className={btn} onClick={onOut} aria-label="Zoom out" title="Zoom out">−</button>
      <button type="button" className={`${btn} w-auto px-2.5 text-[13px]`} onClick={onFit} title="Fit to view">Fit</button>
      {children}
    </div>
  );
}

/** Mouse position relative to a container, for placing the tooltip. */
export function relPos(e: { clientX: number; clientY: number }, container: HTMLElement | null): { x: number; y: number } {
  const r = container?.getBoundingClientRect();
  return { x: e.clientX - (r?.left ?? 0), y: e.clientY - (r?.top ?? 0) };
}

export const FONT = "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
