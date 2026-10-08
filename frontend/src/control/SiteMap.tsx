// Top-down 2D map of the same layout the 3D twin uses (GET /api/layout), drawn in metres.
// On a portrait screen the whole map is turned 90° so it fills a phone; labels stay upright.
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useShallow } from "zustand/react/shallow";
import type { Unit } from "../contract";
import type { Layout, LayoutNode } from "../layout";
import { send } from "../store/ws";
import { useWorld } from "../store/world";
import { color, model } from "../theme";
import type { Checked } from "./state";

// Visible extent (metres): warehouse, apron, yard lane, gate and the road stretch where arriving
// trucks wait (ROAD_E, x = 74), without the far road ends.
const X0 = -6, X1 = 80, Z0 = -3, Z1 = 54;

const PortraitCtx = createContext(false);

/** Text that stays upright when the map is turned. */
function Label({ x, z, children, size = 1.5, fill = color.ink2, weight = 500, anchor = "middle" }: {
  x: number; z: number; children: ReactNode; size?: number; fill?: string; weight?: number; anchor?: "start" | "middle" | "end";
}) {
  const portrait = useContext(PortraitCtx);
  return (
    <text x={x} y={z} fontSize={size} fill={fill} fontWeight={weight} textAnchor={anchor} dominantBaseline="central"
      transform={portrait ? `rotate(-90 ${x} ${z})` : undefined} style={{ pointerEvents: "none", userSelect: "none" }}>
      {children}
    </text>
  );
}

function Static({ layout }: { layout: Layout }) {
  const wh = layout.buildings.find((b) => b.kind === "warehouse")!;
  return (
    <g>
      {layout.roads.map((r) => {
        const [a, b] = [r.points[0]!, r.points[r.points.length - 1]!];
        return (
          <g key={r.id}>
            <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color.road} strokeWidth={r.width} />
            {r.dashed && <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="#fff" strokeWidth={0.25} strokeDasharray="2 2" />}
          </g>
        );
      })}
      {layout.fence.lines.map((l, i) => (
        <polyline key={i} points={l.map((p) => p.join(",")).join(" ")} fill="none" stroke={model.fence} strokeWidth={0.3} />
      ))}
      {layout.parking.map((p) => (
        <rect key={p.id} x={p.x} y={p.z} width={p.w} height={p.d} fill="none" stroke={color.marking} strokeWidth={0.25} />
      ))}
      {layout.buildings.map((b) => (
        <g key={b.id}>
          <rect x={b.x} y={b.z} width={b.w} height={b.d} rx={0.4} fill={b.kind === "warehouse" ? model.floor : "#DCE4FB"} stroke={color.structure} strokeWidth={0.5} />
          {b.kind === "office" && <Label x={b.x + b.w / 2} z={b.z + b.d / 2}>{b.label ?? "Office"}</Label>}
        </g>
      ))}
      {wh.doors?.map((d) => (
        <g key={d.id}>
          <line x1={d.x} y1={wh.z + wh.d} x2={d.x + d.w} y2={wh.z + wh.d} stroke={model.floor} strokeWidth={0.7} />
          <line x1={d.x} y1={wh.z + wh.d} x2={d.x + d.w} y2={wh.z + wh.d} stroke={color.ink2} strokeWidth={0.15} strokeDasharray="0.4 0.3" />
        </g>
      ))}
      {layout.zones.map((z) => (
        <g key={z.id}>
          <rect x={z.x} y={z.z} width={z.w} height={z.d} fill="#FFF8E1" stroke={color.marking} strokeWidth={0.2} strokeDasharray="0.8 0.5" />
          <Label x={z.x + z.w / 2 + 0.8} z={z.z + z.d - 1.3} size={1.2}>{z.name}</Label>
        </g>
      ))}
      {layout.racks.map((r) => (
        <g key={r.id}>
          <rect x={r.x} y={r.z} width={r.w} height={r.d} fill="#E3E9F8" stroke={model.rackUpright} strokeWidth={0.2} />
          {r.slots.slice(1).map((_, i) => {
            const x = r.x + ((i + 1) * r.w) / r.slots.length;
            return <line key={i} x1={x} y1={r.z} x2={x} y2={r.z + r.d} stroke={model.rackUpright} strokeWidth={0.15} />;
          })}
        </g>
      ))}
      <circle cx={layout.gateway.x} cy={layout.gateway.z} r={layout.gateway.ble_range_m} fill={color.live} fillOpacity={0.04} stroke={color.live} strokeOpacity={0.35} strokeWidth={0.15} />
    </g>
  );
}

/** Short map labels; long names ("Charger C1") collide at phone size. */
function mapLabel(n: LayoutNode, layout: Layout): string | null {
  switch (n.type) {
    case "rack_slot": return null;         // the rack row letter is drawn once per rack
    case "zone": return null;              // the zone's name is drawn inside it
    case "dock": return layout.docks.find((d) => d.node === n.id)?.door ?? null;
    case "charger": return layout.chargers.find((c) => c.node === n.id)?.label.replace("Charger ", "") ?? null;
    default: return n.label ?? null;
  }
}

const TARGET_TYPES = new Set<LayoutNode["type"]>(["rack_slot", "zone", "dock", "charger", "bay", "gate"]);

function NodeMarker({ n, check, chosen, onTap }: { n: LayoutNode; check: Checked | undefined; chosen: boolean; onTap: (n: LayoutNode) => void }) {
  const ok = check?.ok === true;
  const fill = chosen ? color.info : ok ? "#FFFFFF" : color.idleBg;
  const stroke = chosen ? color.info : ok ? color.info : color.idle;
  return (
    <g onClick={(e) => { e.stopPropagation(); onTap(n); }} style={{ cursor: "pointer" }} role="button" aria-label={`${n.label ?? n.id}${check && !ok ? `, unavailable: ${check.reason}` : ""}`}>
      <circle cx={n.x} cy={n.z} r={2.2} fill="transparent" />
      <circle cx={n.x} cy={n.z} r={0.9} fill={fill} stroke={stroke} strokeWidth={0.3} strokeDasharray={check && !ok ? "0.35 0.3" : undefined} />
    </g>
  );
}

function UnitGlyph({ u, selected }: { u: Unit; selected: boolean }) {
  const deg = (u.heading_rad * 180) / Math.PI;
  const tap = (e: React.MouseEvent) => { e.stopPropagation(); send({ type: "select_unit", unit_id: u.id }); };
  const ring = selected && <circle r={u.kind === "truck" ? 6.4 : 2} fill="none" stroke={color.info} strokeWidth={0.35} />;
  const live = u.source === "device" && <circle r={u.kind === "truck" ? 6.9 : 2.5} fill="none" stroke={color.live} strokeWidth={0.25} strokeDasharray="0.6 0.4" />;
  if (u.kind === "forklift") {
    return (
      <g transform={`translate(${u.x} ${u.z})`} onClick={tap} style={{ cursor: "pointer" }} role="button" aria-label={`${u.id}, ${u.state}`}>
        <circle r={2.6} fill="transparent" />
        {ring}{live}
        <g transform={`rotate(${deg})`}>
          <rect x={-1.1} y={-0.75} width={2.2} height={1.5} rx={0.35} fill={model.forkliftBody} stroke={color.structureDark} strokeWidth={0.2} />
          <rect x={1.1} y={-0.55} width={0.7} height={0.2} fill={color.structureDark} />
          <rect x={1.1} y={0.35} width={0.7} height={0.2} fill={color.structureDark} />
          {u.carrying && <rect x={1.15} y={-0.6} width={1.1} height={1.2} fill={color.pallet} stroke={color.boxDark} strokeWidth={0.12} />}
        </g>
        <Label x={0} z={-2.2} size={1.3} fill={color.ink} weight={600}>{u.id}</Label>
      </g>
    );
  }
  if (u.kind === "truck") {
    if (u.state === "gone") return null;
    return (
      <g transform={`translate(${u.x} ${u.z})`} onClick={tap} style={{ cursor: "pointer" }} role="button" aria-label={`${u.id}, ${u.state}`}>
        {ring}{live}
        <g transform={`rotate(${deg})`}>
          <rect x={-5.4} y={-1.5} width={8} height={3} rx={0.3} fill="#FFFFFF" stroke={color.structureDark} strokeWidth={0.2} />
          <rect x={2.8} y={-1.4} width={2.6} height={2.8} rx={0.5} fill={color.structure} />
        </g>
        <Label x={0} z={0} size={1.3} fill={color.ink} weight={600}>{u.id}</Label>
      </g>
    );
  }
  return null;
}

function Pallets() {
  const pallets = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "pallet" && (u.state === "stored" || u.state === "staged"))));
  return (
    <g style={{ pointerEvents: "none" }}>
      {pallets.map((p) => <rect key={p.id} x={p.x - 0.6} y={p.z - 0.6} width={1.2} height={1.2} rx={0.15} fill={color.box} stroke={color.boxDark} strokeWidth={0.12} />)}
    </g>
  );
}

function PathPreview({ unit, path, layout }: { unit: Unit; path: string[]; layout: Layout }) {
  const pts = [[unit.x, unit.z], ...path.map((id) => layout.nodes.find((n) => n.id === id)).filter((n): n is LayoutNode => !!n).map((n) => [n.x, n.z])];
  const end = pts[pts.length - 1]!;
  return (
    <g style={{ pointerEvents: "none" }}>
      <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke={color.info} strokeWidth={0.5} strokeDasharray="1 0.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={end[0]} cy={end[1]} r={1.5} fill={color.info} fillOpacity={0.18} />
    </g>
  );
}

export function SiteMap({ checks, chosen, path, onNodeTap, onBackground }: {
  checks: Map<string, Checked>; chosen: string | null; path: string[] | null; onNodeTap: (n: LayoutNode) => void; onBackground: () => void;
}) {
  const layout = useWorld((s) => s.layout);
  const movers = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "forklift" || u.kind === "truck")));
  const selectedId = useWorld((s) => s.selected);
  const selected = movers.find((u) => u.id === selectedId);
  const box = useRef<HTMLDivElement>(null);
  const [portrait, setPortrait] = useState(false);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => { if (e) setPortrait(e.contentRect.width < e.contentRect.height * 0.95); });
    ro.observe(el);
    return () => ro.disconnect();
  }, [layout]); // the box only exists once the layout has loaded

  if (!layout) return null;
  const W = X1 - X0, H = Z1 - Z0;
  const nodes = layout.nodes.filter((n) => TARGET_TYPES.has(n.type) && (!selected || n.kinds.includes(selected.kind as "forklift" | "truck")));
  return (
    <div ref={box} className="relative h-full w-full">
      <svg viewBox={portrait ? `0 0 ${H} ${W}` : `${X0} ${Z0} ${W} ${H}`} className="h-full w-full touch-manipulation select-none"
        preserveAspectRatio="xMidYMid meet" onClick={onBackground} role="img" aria-label="Site map">
        <PortraitCtx.Provider value={portrait}>
        <g transform={portrait ? `translate(${Z1} ${-X0}) rotate(90)` : undefined}>
          <Static layout={layout} />
          <Pallets />
          {selected && path && <PathPreview unit={selected} path={path} layout={layout} />}
          {selected && selected.source !== "device" && nodes.map((n) => <NodeMarker key={n.id} n={n} check={checks.get(n.id)} chosen={chosen === n.id} onTap={onNodeTap} />)}
          {nodes.map((n) => {
            const text = mapLabel(n, layout);
            if (!text) return null;
            // 1.9 m below the node on screen: +z in landscape, +x once the map is turned.
            return <Label key={`l-${n.id}`} x={n.x + (portrait ? 1.9 : 0)} z={n.z + (portrait ? 0 : 1.9)} size={1.15}>{text}</Label>;
          })}
          {layout.racks.map((r) => <Label key={`r-${r.id}`} x={r.x - 1.6} z={r.z + r.d / 2} size={1.2} weight={600}>{r.row}</Label>)}
          <g>
            <rect x={layout.gateway.x - 0.6} y={layout.gateway.z - 0.6} width={1.2} height={1.2} rx={0.2} fill={color.live} />
          </g>
          {movers.map((u) => <UnitGlyph key={u.id} u={u} selected={u.id === selectedId} />)}
        </g>
        </PortraitCtx.Provider>
      </svg>
    </div>
  );
}
