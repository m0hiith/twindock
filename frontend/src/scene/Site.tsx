// Static site: ground, roads, markings, fence, decor. Drawn from layout.json so the 3D view, the
// Control Room map and the backend's waypoint graph always agree.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type * as THREE from "three";
import { cameraState } from "./camera";
import type { Layout, XZ } from "../layout";
import { useWorld } from "../store/world";
import { color, model } from "../theme";
import { Ball, Box, Cyl, Decal, Label, mat, unitPlane } from "./parts";

function hash(x: number, z: number): number {
  const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453;
  return s - Math.floor(s);
}

export function Ground({ layout }: { layout: Layout }) {
  const { x, z } = layout.bounds;
  const pad = 60; // ground runs past the bounds so panning never shows the void
  return (
    <mesh geometry={unitPlane} material={mat(color.ground)} position={[(x[0] + x[1]) / 2, 0, (z[0] + z[1]) / 2]}
      scale={[x[1] - x[0] + pad * 2, 1, z[1] - z[0] + pad * 2]} receiveShadow />
  );
}

function Segment({ a, b, width, c, y }: { a: XZ; b: XZ; width: number; c: string; y: number }) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const len = Math.hypot(dx, dz);
  return <Decal x={(a[0] + b[0]) / 2} z={(a[1] + b[1]) / 2} w={len} d={width} c={c} y={y} rot={-Math.atan2(dz, dx)} />;
}

export function Roads({ layout }: { layout: Layout }) {
  return (
    <group>
      {layout.roads.map((r) => r.points.slice(1).map((p, i) => {
        const a = r.points[i]!;
        const dx = p[0] - a[0], dz = p[1] - a[1];
        const len = Math.hypot(dx, dz);
        const dashes = r.dashed ? Math.floor(len / 4) : 0;
        return (
          <group key={`${r.id}${i}`}>
            <Segment a={a} b={p} width={r.width} c={color.road} y={r.dashed ? 0.006 : 0.008} />
            {Array.from({ length: dashes }, (_, k) => {
              const t = (k * 4 + 1) / len, t2 = (k * 4 + 3) / len;
              return <Segment key={k} a={[a[0] + dx * t, a[1] + dz * t]} b={[a[0] + dx * t2, a[1] + dz * t2]}
                width={0.18} c={color.laneMark} y={0.015} />;
            })}
          </group>
        );
      }))}
    </group>
  );
}

function Outline({ x, z, w, d, c = color.marking, t = 0.14, y = 0.03 }: { x: number; z: number; w: number; d: number; c?: string; t?: number; y?: number }) {
  return (
    <group>
      <Decal x={x + w / 2} z={z} w={w} d={t} c={c} y={y} />
      <Decal x={x + w / 2} z={z + d} w={w} d={t} c={c} y={y} />
      <Decal x={x} z={z + d / 2} w={t} d={d} c={c} y={y} />
      <Decal x={x + w} z={z + d / 2} w={t} d={d} c={c} y={y} />
    </group>
  );
}

export function Markings({ layout }: { layout: Layout }) {
  return (
    <group>
      {layout.parking.map((p) => (
        <Outline key={p.id} {...p} />
      ))}
      {layout.zones.map((zn) => (
        <group key={zn.id}>
          <Outline {...zn} />
          <Decal x={zn.x + zn.w / 2} z={zn.z + zn.d / 2} w={zn.w} d={zn.d} c={color.marking} y={0.02} opacity={0.08} />
        </group>
      ))}
      {/* dock bumpers and door numbers on the apron */}
      {layout.buildings.flatMap((b) => (b.doors ?? []).map((d) => (
        <group key={d.id}>
          <Box size={[0.35, 0.5, 0.3]} at={[d.x - 1.6, 0.6, b.z + b.d + 0.25]} color={model.tyre} />
          <Box size={[0.35, 0.5, 0.3]} at={[d.x + 1.6, 0.6, b.z + b.d + 0.25]} color={model.tyre} />
          <Decal x={d.x} z={b.z + b.d + 0.8} w={3.6} d={1.0} c={model.metal} y={0.025} />
        </group>
      )))}
    </group>
  );
}

export function FenceStatic({ layout }: { layout: Layout }) {
  const posts: XZ[] = [];
  const rails: { a: XZ; b: XZ }[] = [];
  for (const line of layout.fence.lines) {
    for (let i = 1; i < line.length; i++) {
      const a = line[i - 1]!, b = line[i]!;
      rails.push({ a, b });
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const n = Math.max(1, Math.round(len / 3.5));
      for (let k = 0; k <= n; k++) posts.push([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]);
    }
  }
  return (
    <group>
      {posts.map(([x, z], i) => <Box key={i} size={[0.1, 1.5, 0.1]} at={[x, 0, z]} color={model.fence} />)}
      {rails.map(({ a, b }, i) => {
        const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
        return [0.7, 1.35].map((y) => (
          <Box key={`${i}${y}`} size={[len, 0.06, 0.05]} at={[(a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2]}
            rot={[0, -Math.atan2(b[1] - a[1], b[0] - a[0]), 0]} color={model.fence} shadow={false} />
        ));
      })}
    </group>
  );
}

/** Barrier arm that lifts while a truck is near the gate. */
export function GateBarrier({ layout }: { layout: Layout }) {
  const { x, z0, z1 } = layout.fence.gate;
  const arm = useRef<THREE.Group>(null);
  const lift = useRef(0);
  useFrame((_, dt) => {
    const units = useWorld.getState().units;
    const near = Object.values(units).some((u) => u.kind === "truck" && u.state !== "gone" && Math.hypot(u.x - x, u.z - (z0 + z1) / 2) < 14);
    lift.current += ((near ? 1 : 0) - lift.current) * (1 - Math.exp(-3 * dt));
    if (arm.current) arm.current.rotation.x = -lift.current * 1.35;
  });
  const len = z1 - z0 - 0.4;
  return (
    <group>
      <Box size={[0.5, 1.1, 0.5]} at={[x, 0, z0]} color={model.metal} />
      <group ref={arm} position={[x, 1.0, z0]}>
        <Box size={[0.12, 0.12, len]} at={[0, 0, len / 2]} color="#FFFFFF" />
        {[0.15, 0.45, 0.75].map((f) => <Box key={f} size={[0.13, 0.13, len * 0.12]} at={[0, 0, len * f]} color={color.crit} shadow={false} />)}
      </group>
    </group>
  );
}

export function Trees({ layout }: { layout: Layout }) {
  return (
    <group>
      {layout.decor.trees.map(([x, z]) => {
        const s = 0.8 + hash(x, z) * 0.5;
        return (
          <group key={`${x},${z}`} position={[x, 0, z]} scale={s}>
            <Cyl size={[0.28, 1.4, 0.28]} at={[0, 0.7, 0]} color={model.trunk} />
            <Ball size={[2.2, 2.4, 2.2]} at={[0, 2.4, 0]} color={color.tree} />
          </group>
        );
      })}
    </group>
  );
}

export function Containers({ layout }: { layout: Layout }) {
  return (
    <group>
      {layout.decor.containers.map((c, i) => (
        <group key={i} position={[c.x, 0, c.z]} rotation={[0, -c.heading_rad, 0]}>
          <Box size={[6.06, 2.59, 2.44]} color={c.color} />
          {Array.from({ length: 11 }, (_, k) => [1.23, -1.23].map((zz) => (
            <Box key={`${k}${zz}`} size={[0.12, 2.4, 0.04]} at={[-2.6 + k * 0.52, 0.1, zz]} color={c.color === color.structure ? color.structureDark : "#777777"} shadow={false} />
          )))}
          <Box size={[0.04, 2.4, 2.3]} at={[3.04, 0.1, 0]} color={c.color === color.structure ? color.structureDark : "#777777"} shadow={false} />
        </group>
      ))}
    </group>
  );
}

export function Racks({ layout }: { layout: Layout }) {
  const H = 4.2;
  return (
    <group>
      {layout.racks.map((r) => {
        const frames = r.slots.length + 1;
        const bay = r.w / r.slots.length;
        return (
          <group key={r.id}>
            {Array.from({ length: frames }, (_, i) => [r.z + 0.05, r.z + r.d - 0.05].map((z) => (
              <Box key={`${i}${z}`} size={[0.1, H, 0.1]} at={[r.x + i * bay, 0, z]} color={model.rackUpright} />
            )))}
            {[1.75, 3.35].flatMap((y) => [r.z + 0.05, r.z + r.d - 0.05].map((z) => (
              <Box key={`${y}${z}`} size={[r.w, 0.12, 0.08]} at={[r.x + r.w / 2, y, z]} color={model.rackBeam} />
            )))}
            {[1.87, 3.47].map((y) => (
              <Box key={y} size={[r.w, 0.04, r.d - 0.1]} at={[r.x + r.w / 2, y, r.z + r.d / 2]} color={model.trailerTrim} />
            ))}
          </group>
        );
      })}
    </group>
  );
}

export function Chargers({ layout }: { layout: Layout }) {
  return (
    <group>
      {layout.chargers.map((c) => <Charger key={c.id} id={c.id} node={layout.nodes.find((n) => n.id === c.node)} />)}
    </group>
  );
}

function Charger({ id, node }: { id: string; node: { x: number; z: number } | undefined }) {
  const occupied = useWorld((s) => s.units[id]?.state === "occupied");
  if (!node) return null;
  return (
    <group position={[0.45, 0, node.z]}>
      <Box size={[0.4, 1.5, 0.6]} color="#FFFFFF" />
      <Box size={[0.03, 0.4, 0.4]} at={[0.21, 0.9, 0]} color={model.tyre} />
      <Box size={[0.03, 0.08, 0.3]} at={[0.22, 1.37, 0]} material={mat(occupied ? color.ok : color.idle, { emissive: occupied ? color.ok : undefined })} shadow={false} />
      <Decal x={node.x - 0.45 + 0.4} z={0} w={2.9} d={1.7} c={color.ok} y={0.025} opacity={0.12} />
    </group>
  );
}

/** Painted ground labels. Not baked: they turn with the 90° camera steps so they always read upright. */
export function GroundLabels({ layout }: { layout: Layout }) {
  const g = useRef<THREE.Group>(null);
  useFrame(() => {
    g.current?.children.forEach((m) => { m.rotation.z = -(cameraState.yaw - Math.PI / 4); });
  });
  return (
    <group ref={g}>
      {layout.parking.map((p, i) => (
        <Label key={p.id} text={`Bay ${i + 1}`} at={[p.x + p.w / 2, 0.035, p.z + p.d - 1.6]} width={5.2} flat color={color.ink2} weight={700} />
      ))}
      {layout.zones.map((zn) => (
        <Label key={zn.id} text={zn.name} at={[zn.x + zn.w / 2, 0.035, zn.z + zn.d / 2]} width={4.8} flat color={color.warn} weight={700} />
      ))}
      {layout.racks.map((r) => (
        <Label key={r.id} text={`Rack ${r.row}`} at={[r.x - 1.6, 0.035, r.z + r.d / 2]} width={4.4} flat color={color.ink2} weight={700} />
      ))}
    </group>
  );
}
