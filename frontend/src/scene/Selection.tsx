// Selected unit: blue corner brackets on the ground + floating pill label; its destination gets
// a map pin and the remaining path is drawn on the ground. Hover gets a lighter bracket.
import { Line } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { Unit } from "../contract";
import { useView, useWorld } from "../store/world";
import { color } from "../theme";
import { displayed } from "./interpolation";
import { Ball, mat, unitBox } from "./parts";

/** Footprint (length along heading, width) and label height per kind. */
export function footprint(u: Pick<Unit, "kind" | "id">, layout = useWorld.getState().layout): { l: number; w: number; h: number; rot: boolean } {
  switch (u.kind) {
    case "forklift": return { l: 3.0, w: 1.7, h: 2.6, rot: true };
    case "truck": return { l: 10.8, w: 3.1, h: 4.3, rot: true };
    case "pallet": return { l: 1.5, w: 1.7, h: 1.6, rot: true };
    case "dock": return { l: 4.6, w: 3.4, h: 4.6, rot: false };
    case "charger": return { l: 1.6, w: 1.6, h: 2.0, rot: false };
    case "gateway": return { l: 1.8, w: 1.8, h: 4.2, rot: false };
    case "rack": {
      const r = layout?.racks.find((x) => x.id === u.id);
      return { l: (r?.w ?? 26) + 1, w: (r?.d ?? 2.5) + 1, h: 5, rot: false };
    }
  }
}

function Brackets({ l, w, c, opacity = 1 }: { l: number; w: number; c: string; opacity?: number }) {
  const arm = Math.min(1.2, Math.min(l, w) * 0.35), t = 0.16, y = 0.05;
  const m = opacity < 1 ? mat(c, { transparent: opacity }) : mat(c);
  const corners: [number, number][] = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
  return (
    <group>
      {corners.map(([sx, sz]) => (
        <group key={`${sx}${sz}`} position={[(sx * l) / 2, y, (sz * w) / 2]}>
          <mesh geometry={unitBox} material={m} scale={[arm, 0.04, t]} position={[(-sx * arm) / 2, 0, (-sz * t) / 2]} />
          <mesh geometry={unitBox} material={m} scale={[t, 0.04, arm]} position={[(-sx * t) / 2, 0, (-sz * arm) / 2]} />
        </group>
      ))}
    </group>
  );
}

/** Follows a unit's displayed pose (falls back to server pose for static units). */
function Follow({ id, rot, children }: { id: string; rot: boolean; children: React.ReactNode }) {
  const g = useRef<THREE.Group>(null);
  useFrame(() => {
    const u = useWorld.getState().units[id];
    const p = displayed.get(id) ?? (u ? { x: u.x, z: u.z, h: u.heading_rad } : null);
    if (!p || !g.current) return;
    g.current.position.set(p.x, 0, p.z);
    g.current.rotation.y = rot ? -p.h : 0;
  });
  return <group ref={g}>{children}</group>;
}

/** DOM element of the selection pill (hud/SelectionPill.tsx); positioned here every frame. */
export const pillAnchor: { el: HTMLDivElement | null } = { el: null };
const v = new THREE.Vector3();

function PillTracker({ id, h }: { id: string; h: number }) {
  const { camera, size } = useThree();
  useFrame(() => {
    const el = pillAnchor.el;
    const u = useWorld.getState().units[id];
    const p = displayed.get(id) ?? (u ? { x: u.x, z: u.z, h: 0 } : null);
    if (!el || !p) return;
    v.set(p.x, h, p.z).project(camera);
    const x = ((v.x + 1) / 2) * size.width, y = ((1 - v.y) / 2) * size.height;
    el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -100%)`;
    el.style.visibility = "visible";
  });
  return null;
}

function MapPin({ x, z }: { x: number; z: number }) {
  const g = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (g.current) g.current.position.y = 2.2 + Math.sin(clock.elapsedTime * 2.4) * 0.15;
  });
  return (
    <group position={[x, 0, z]} scale={1.5}>
      <group ref={g}>
        <mesh rotation={[Math.PI, 0, 0]} position={[0, 0.55, 0]} material={mat(color.info)} castShadow>
          <coneGeometry args={[0.42, 1.1, 20]} />
        </mesh>
        <Ball size={[0.86, 0.86, 0.86]} at={[0, 1.1, 0]} color={color.info} />
        <Ball size={[0.34, 0.34, 0.34]} at={[0, 1.12, 0.35]} color="#FFFFFF" shadow={false} />
      </group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.04, 0]} material={mat(color.info, { transparent: 0.25 })}>
        <circleGeometry args={[0.7, 32]} />
      </mesh>
    </group>
  );
}

function PathLine({ unitId, path }: { unitId: string; path: string[] }) {
  const layout = useWorld((s) => s.layout);
  const pts = useMemo(() => {
    if (!layout) return [];
    return path.map((id) => layout.nodes.find((n) => n.id === id)).filter(Boolean).map((n) => [n!.x, 0.06, n!.z] as [number, number, number]);
  }, [layout, path]);
  const line = useRef<{ geometry: { setPositions: (p: number[]) => void } } | null>(null);
  useFrame(() => {
    const p = displayed.get(unitId);
    if (!p || !line.current || pts.length === 0) return;
    line.current.geometry.setPositions([p.x, 0.06, p.z, ...pts.flat()]);
  });
  if (pts.length === 0) return null;
  return <Line ref={line as never} points={[pts[0]!, ...pts]} color={color.info} lineWidth={3} dashed dashSize={0.6} gapSize={0.4} />;
}

export function SelectionOverlay() {
  const selected = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const hoveredId = useView((s) => s.hovered);
  const hovered = useWorld((s) => (hoveredId && hoveredId !== s.selected ? s.units[hoveredId] : undefined));
  const layout = useWorld((s) => s.layout);
  const target = selected?.target_node ? layout?.nodes.find((n) => n.id === selected.target_node) : undefined;
  return (
    <group>
      {hovered && (() => {
        const f = footprint(hovered);
        return <Follow id={hovered.id} rot={f.rot}><Brackets l={f.l} w={f.w} c={color.info} opacity={0.45} /></Follow>;
      })()}
      {selected && (() => {
        const f = footprint(selected);
        return (
          <>
            <Follow id={selected.id} rot={f.rot}><Brackets l={f.l} w={f.w} c={color.info} /></Follow>
            <PillTracker id={selected.id} h={f.h} />
          </>
        );
      })()}
      {selected && target && selected.path && selected.path.length > 0 && (
        <>
          <PathLine unitId={selected.id} path={selected.path} />
          <MapPin x={target.x} z={target.z} />
        </>
      )}
    </group>
  );
}
