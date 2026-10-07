// Warehouse shell as a cutaway: walls facing the camera drop to a kerb so the floor stays visible
// from every 90° view; walls facing away stand full height with ribbed cladding and dock doors.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { Layout } from "../layout";
import { useWorld } from "../store/world";
import { color, model } from "../theme";
import { cameraState } from "./camera";
import { Box, Cyl, Decal, Label } from "./parts";

const TALL = 5.5;
const LOW = 0.9;
const T = 0.3; // wall thickness
const DOOR_H = 3.8;

const ribTextures = new Map<number, THREE.MeshStandardMaterial>();
function ribbedMaterial(lengthM: number): THREE.MeshStandardMaterial {
  const key = Math.round(lengthM * 10);
  let m = ribTextures.get(key);
  if (m) return m;
  const c = document.createElement("canvas");
  c.width = 64;
  c.height = 8;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = color.structure;
  ctx.fillRect(0, 0, 64, 8);
  ctx.fillStyle = color.structureDark;
  ctx.fillRect(48, 0, 10, 8);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.RepeatWrapping;
  t.repeat.set(lengthM / 0.9, 1); // one rib every 0.9 m
  m = new THREE.MeshStandardMaterial({ map: t, roughness: 0.8 });
  ribTextures.set(key, m);
  return m;
}

interface Seg { from: number; to: number }

/** One straight wall. `along` is "x" for north/south walls. normal = outward direction. */
function Wall({ along, fixed, segs, normal, doors }: {
  along: "x" | "z"; fixed: number; segs: Seg[]; normal: [number, number];
  doors?: { id: string; dock: string; x: number; w: number }[];
}) {
  const walls = useRef<THREE.Group>(null);
  const doorGroup = useRef<THREE.Group>(null);
  const h = useRef(TALL);
  useFrame((_, dt) => {
    const facing = Math.cos(cameraState.yaw) * normal[0] + Math.sin(cameraState.yaw) * normal[1] > 0.05;
    const target = facing ? LOW : TALL;
    h.current += (target - h.current) * (1 - Math.exp(-8 * dt));
    if (walls.current) walls.current.scale.y = h.current / TALL;
    if (doorGroup.current) doorGroup.current.visible = h.current > DOOR_H + 0.4;
  });
  const place = (a: number, b: number): { pos: [number, number, number]; size: [number, number, number] } =>
    along === "x"
      ? { pos: [(a + b) / 2, 0, fixed], size: [b - a, TALL, T] }
      : { pos: [fixed, 0, (a + b) / 2], size: [T, TALL, b - a] };
  return (
    <group>
      <group ref={walls}>
        {segs.map((s) => {
          const { pos, size } = place(s.from, s.to);
          return <Box key={s.from} size={size} at={pos} material={ribbedMaterial(s.to - s.from)} />;
        })}
      </group>
      {doors && (
        <group ref={doorGroup}>
          {doors.map((d) => <DockDoor key={d.id} {...d} z={fixed} />)}
        </group>
      )}
    </group>
  );
}

function DockDoor({ id, dock, x, w, z }: { id: string; dock: string; x: number; w: number; z: number }) {
  const panel = useRef<THREE.Group>(null);
  const open = useRef(0);
  const dockUnitId = useWorld((s) => s.layout?.docks.find((d) => d.node === dock)?.id);
  useFrame((_, dt) => {
    const st = dockUnitId ? useWorld.getState().units[dockUnitId]?.state : undefined;
    const target = st === "occupied" ? 1 : 0;
    open.current += (target - open.current) * (1 - Math.exp(-3 * dt));
    const g = panel.current;
    if (g) {
      const hh = Math.max(0.05, DOOR_H * (1 - open.current * 0.92));
      g.scale.y = hh / DOOR_H;
      g.position.y = DOOR_H - hh;
    }
  });
  return (
    <group>
      <Box size={[w, TALL - DOOR_H, T]} at={[x, DOOR_H, z]} material={ribbedMaterial(w)} />
      <Box size={[0.18, DOOR_H, T + 0.06]} at={[x - w / 2 + 0.09, 0, z]} color={color.structureDark} />
      <Box size={[0.18, DOOR_H, T + 0.06]} at={[x + w / 2 - 0.09, 0, z]} color={color.structureDark} />
      <group ref={panel}>
        <Box size={[w - 0.36, DOOR_H, 0.08]} at={[x, 0, z]} color={model.door} />
        {[0.2, 0.4, 0.6, 0.8].map((f) => (
          <Box key={f} size={[w - 0.36, 0.05, 0.1]} at={[x, DOOR_H * f, z]} color={model.doorSlat} shadow={false} />
        ))}
      </group>
      <Cyl size={[0.42, w - 0.36, 0.42]} at={[x, DOOR_H + 0.15, z - 0.25]} color={model.doorSlat} axis="x" />
      <Label text={id} at={[x, DOOR_H + 0.85, z + T / 2 + 0.02]} width={2.4} color="#FFFFFF" weight={700} />
    </group>
  );
}

export function Warehouse({ layout }: { layout: Layout }) {
  const b = layout.buildings.find((x) => x.kind === "warehouse");
  const southSegs = useMemo(() => {
    if (!b) return [];
    const cuts = (b.doors ?? []).map((d) => [d.x - d.w / 2, d.x + d.w / 2] as const).sort((p, q) => p[0] - q[0]);
    const segs: Seg[] = [];
    let at = b.x - T / 2;
    for (const [a, c] of cuts) {
      segs.push({ from: at, to: a });
      at = c;
    }
    segs.push({ from: at, to: b.x + b.w + T / 2 });
    return segs;
  }, [b]);
  if (!b) return null;
  const { x, z, w, d } = b;
  return (
    <group>
      <Decal x={x + w / 2} z={z + d / 2} w={w} d={d} c={model.floor} y={0.012} />
      <Wall along="x" fixed={z} segs={[{ from: x - T / 2, to: x + w + T / 2 }]} normal={[0, -1]} />
      <Wall along="x" fixed={z + d} segs={southSegs} normal={[0, 1]} doors={b.doors} />
      <Wall along="z" fixed={x} segs={[{ from: z, to: z + d }]} normal={[-1, 0]} />
      <Wall along="z" fixed={x + w} segs={[{ from: z, to: z + d }]} normal={[1, 0]} />
      <FloorMarkings layout={layout} />
    </group>
  );
}

/** Yellow aisle lines and dock staging boxes painted on the warehouse floor. */
function FloorMarkings({ layout }: { layout: Layout }) {
  const y = 0.03;
  const lines: { x: number; z: number; w: number; d: number }[] = [
    { x: 19.6, z: 18.4, w: 33, d: 0.12 },
    { x: 19.6, z: 21.6, w: 33, d: 0.12 },
  ];
  for (const dk of layout.docks) {
    const n = layout.nodes.find((q) => q.id === dk.node);
    if (!n) continue;
    lines.push({ x: n.x, z: 24.3, w: 3.6, d: 0.1 }, { x: n.x - 1.8, z: 26.0, w: 0.1, d: 3.4 }, { x: n.x + 1.8, z: 26.0, w: 0.1, d: 3.4 });
  }
  return (
    <group>
      {lines.map((l, i) => <Decal key={i} x={l.x} z={l.z} w={l.w} d={l.d} c={color.marking} y={y} />)}
    </group>
  );
}

export function Office({ layout }: { layout: Layout }) {
  const b = layout.buildings.find((x) => x.kind === "office");
  if (!b) return null;
  const ribs = Math.floor(b.w / 0.7);
  return (
    <group position={[b.x + b.w / 2, 0, b.z + b.d / 2]}>
      <Box size={[b.w, b.h, b.d]} material={ribbedMaterial(b.w)} />
      <Box size={[b.w + 0.04, 0.9, b.d + 0.04]} at={[0, 1.6, 0]} color={model.cabGlass} />
      <Box size={[b.w + 0.6, 0.25, b.d + 0.6]} at={[0, b.h, 0]} color={color.structureDark} />
      {Array.from({ length: ribs }, (_, i) => (
        <Box key={i} size={[0.12, 0.12, b.d + 0.6]} at={[-b.w / 2 + 0.35 + i * 0.7, b.h + 0.25, 0]} color={color.structure} shadow={false} />
      ))}
      <Box size={[1.4, 2.2, 0.1]} at={[0, 0, b.d / 2 + 0.02]} color={model.door} />
    </group>
  );
}

