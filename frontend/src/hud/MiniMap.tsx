// Mini-map (F4): the whole campus from above with the area the camera sees. Click or drag to go there.
import { useRef } from "react";
import { useView, useWorld } from "../store/world";
import { color } from "../theme";

const W = 230;

export function MiniMap({ className = "" }: { className?: string }) {
  const layout = useWorld((s) => s.layout);
  const rect = useView((s) => s.viewRect);
  const building = useView((s) => s.building);
  const svg = useRef<SVGSVGElement>(null);
  if (!layout) return null;
  const [x0, x1] = layout.bounds.x, [z0, z1] = layout.bounds.z;
  const w = x1 - x0, h = z1 - z0;
  const H = Math.round((W * h) / w);
  const c = layout.campus;
  const go = (e: React.PointerEvent) => {
    const r = svg.current!.getBoundingClientRect();
    const x = x0 + ((e.clientX - r.left) / r.width) * w, z = z0 + ((e.clientY - r.top) / r.height) * h;
    useView.getState().focusOn(Math.max(x0, Math.min(x1, x)), Math.max(z0, Math.min(z1, z)));
  };
  const rects = [...layout.buildings.map((b) => ({ id: b.id, x: b.x, z: b.z, w: b.w, d: b.d, hot: false })),
    ...(c?.buildings ?? []).map((b) => ({ id: b.id, x: b.x, z: b.z, w: b.w, d: b.d, hot: building === b.id }))];
  return (
    <div className={`card pointer-events-auto overflow-hidden p-1.5 ${className}`} aria-label="Mini-map">
      <svg ref={svg} width={W} height={H} viewBox={`${x0} ${z0} ${w} ${h}`} className="block cursor-crosshair touch-none rounded-lg bg-[#EDEDED]"
        onPointerDown={(e) => { (e.target as Element).setPointerCapture?.(e.pointerId); go(e); }}
        onPointerMove={(e) => { if (e.buttons === 1) go(e); }}>
        {layout.roads.map((r) => <polyline key={r.id} points={r.points.map((p) => p.join(",")).join(" ")} fill="none" stroke="#D6D6D6" strokeWidth={r.width} strokeLinejoin="round" />)}
        {rects.map((b) => <rect key={b.id} x={b.x} y={b.z} width={b.w} height={b.d} fill={b.hot ? color.accent : "#B8B8B8"} />)}
        {c?.muster_points.map((m) => <circle key={m.id} cx={m.x} cy={m.z} r={3} fill="#2BB673" />)}
        {rect && <polygon points={rect.map((p) => p.join(",")).join(" ")} fill={`${color.accent}14`} stroke={color.accent} strokeWidth={Math.max(1, w / 150)} strokeLinejoin="round" />}
      </svg>
    </div>
  );
}
