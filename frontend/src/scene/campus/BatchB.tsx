// F2 batch B: raw material store (with its dock doors and racks), QC lab, maintenance workshop and spare-parts store.
// The manufacturing hall's second line is drawn by ProductionLine.tsx (conveyor2 + M-03 / M-04).
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type * as THREE from "three";
import type { CampusBuilding, Layout } from "../../layout";
import { useWorld } from "../../store/world";
import { Baked } from "../Baked";
import { Box, Cyl, Decal, Label } from "../parts";
import { ribbedMaterial } from "../Warehouse";
import { Building, palette, useBuilding } from "./shared";

function Pallets({ b, rows, cols, x0, z0, gx, gz, h = 1.4 }: { b: CampusBuilding; rows: number; cols: number; x0: number; z0: number; gx: number; gz: number; h?: number }) {
  return (
    <Baked>
      {Array.from({ length: rows }, (_, r) => Array.from({ length: cols }, (_, k) => (
        <group key={`${r}${k}`} position={[b.x + x0 + k * gx, 0, b.z + z0 + r * gz]}>
          <Box size={[1.2, 0.15, 1.0]} at={[0, 0, 0]} color="#B98A5A" />
          <Box size={[1.1, h, 0.9]} at={[0, 0.15, 0]} color={(r + k) % 2 ? "#D9B48A" : "#C79A6B"} />
        </group>
      )))}
    </Baked>
  );
}

function DockDoor({ x, z, node }: { x: number; z: number; node: string }) {
  const panel = useRef<THREE.Group>(null);
  const open = useRef(0);
  const dockId = node === "RAW_DOCK_1" ? "DB-03" : "DB-04";
  useFrame((_, dt) => {
    const occ = useWorld.getState().devices[dockId]?.readings.door_position?.value === "open";
    open.current += ((occ ? 1 : 0) - open.current) * (1 - Math.exp(-3 * dt));
    if (panel.current) panel.current.scale.y = Math.max(0.06, 1 - open.current * 0.94);
  });
  return (
    <group position={[x, 0, z]}>
      <group ref={panel}><Box size={[0.12, 3.6, 3.6]} at={[0, 0, 0]} color="#EBEBEB" /></group>
      <Box size={[1.6, 0.2, 4.4]} at={[0.9, 3.7, 0]} color={palette.red} />
      <Box size={[0.9, 1.0, 3.0]} at={[0.6, 0, 0]} color={palette.dark} shadow={false} />
    </group>
  );
}

function RawStore({ layout }: { layout: Layout }) {
  const b = useBuilding("RAW_STORE", layout);
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Raw material store" wall={palette.white} roof={palette.red} windows={false} signW={7}
      interior={<>
        <Decal x={b.x + b.w / 2} z={b.z + b.d / 2} w={b.w - 2} d={0.12} c={palette.safety} y={0.07} />
        <Baked>
          {[0, 1].map((r) => (
            <group key={r}>
              <Box size={[b.w - 12, 0.12, 1.2]} at={[b.x + 12 + (b.w - 12) / 2, 1.6, b.z + 3 + r * 14]} color={palette.red} />
              <Box size={[b.w - 12, 0.12, 1.2]} at={[b.x + 12 + (b.w - 12) / 2, 3.2, b.z + 3 + r * 14]} color={palette.red} />
            </group>
          ))}
        </Baked>
        <Pallets b={b} rows={1} cols={7} x0={14} z0={3} gx={2.6} gz={0} h={1.2} />
        <Pallets b={b} rows={1} cols={7} x0={14} z0={17} gx={2.6} gz={0} h={1.6} />
        <Pallets b={b} rows={2} cols={3} x0={4} z0={8} gx={2.4} gz={2.4} h={1.0} />
      </>}>
      {(b.doors ?? []).filter((d) => d.wall === "east").map((d) => <DockDoor key={d.id} x={b.x + b.w} z={d.at} node={d.node} />)}
      <Label text="Dock 1" at={[b.x + b.w + 3.5, 0.04, 62]} width={3.2} flat color={palette.steelDark} weight={700} />
      <Label text="Dock 2" at={[b.x + b.w + 3.5, 0.04, 70]} width={3.2} flat color={palette.steelDark} weight={700} />
    </Building>
  );
}

function Bench({ x, z, w = 2.2, c = palette.steel }: { x: number; z: number; w?: number; c?: string }) {
  return (
    <group position={[x, 0, z]}>
      <Box size={[w, 0.9, 0.9]} at={[0, 0, 0]} color={c} />
      <Box size={[w * 0.5, 0.35, 0.3]} at={[0, 0.9, -0.2]} color={palette.glass} shadow={false} />
    </group>
  );
}

function QcLab({ layout }: { layout: Layout }) {
  const b = useBuilding("QC_LAB", layout);
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="QC lab" wall="#FFFFFF" roof={palette.light} y0={1.2} hh={1.4} spacing={2.6} signW={3.4}
      roofExtras={<Box size={[2.4, 0.9, 2.4]} at={[b.x + b.w - 3, b.h + 0.35, b.z + 3]} color={palette.steel} />}
      interior={<>
        <Baked>
          {[0, 1, 2].map((i) => <Bench key={i} x={b.x + 4 + i * 4.2} z={b.z + 4} c="#FFFFFF" />)}
          {[0, 1, 2].map((i) => <Bench key={`b${i}`} x={b.x + 4 + i * 4.2} z={b.z + 9} c="#FFFFFF" />)}
        </Baked>
        <Box size={[1.4, 1.9, 0.7]} at={[b.x + b.w - 1.2, 0, b.z + b.d - 2]} color={palette.steel} />
      </>} />
  );
}

function Workshop({ layout }: { layout: Layout }) {
  const b = useBuilding("WORKSHOP", layout);
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Maintenance workshop" wall="#E9E9E6" roof={palette.steelDark} y0={2.6} hh={1.0} spacing={3.6} signW={8}
      roofExtras={<>
        <Box size={[b.w * 0.5, 0.25, 1.2]} at={[b.x + b.w / 2, b.h + 0.4, b.z + b.d / 2]} color={palette.concrete} shadow={false} />
        <Cyl size={[0.7, 1.4, 0.7]} at={[b.x + 5, b.h + 0.9, b.z + 4]} color={palette.steel} />
      </>}
      interior={<>
        <Baked>
          {[0, 1, 2].map((i) => <Bench key={i} x={b.x + 5 + i * 4.5} z={b.z + 3} w={3} c={palette.concrete} />)}
          <group position={[b.x + b.w - 7, 0, b.z + 3]}>
            <Box size={[2.4, 1.1, 1.0]} at={[0, 0, 0]} color={palette.red} />
            <Box size={[0.6, 1.0, 0.6]} at={[0, 1.1, 0]} color={palette.steelDark} />
          </group>
          {/* spare-parts store: shelving on the east end */}
          {[0, 1, 2].map((r) => (
            <group key={r} position={[b.x + b.w - 3.2, 0, b.z + 6 + r * 3]}>
              <Box size={[0.9, 0.1, 2.6]} at={[0, 0.5, 0]} color={palette.safety} />
              <Box size={[0.9, 0.1, 2.6]} at={[0, 1.4, 0]} color={palette.safety} />
              <Box size={[0.9, 0.1, 2.6]} at={[0, 2.3, 0]} color={palette.safety} />
              <Box size={[0.9, 2.4, 0.08]} at={[0, 0, 1.3]} color={palette.steelDark} />
              <Box size={[0.9, 2.4, 0.08]} at={[0, 0, -1.3]} color={palette.steelDark} />
              <Box size={[0.7, 0.5, 2.0]} at={[0, 0.6, 0]} color="#C79A6B" />
            </group>
          ))}
        </Baked>
        <Label text="Spare parts" at={[b.x + b.w - 3.2, 0.1, b.z + b.d - 2]} width={3.2} flat color={palette.steelDark} weight={700} />
      </>}>
      {/* roll-up door on the south wall */}
      <Box size={[4, 3.4, 0.12]} at={[b.x + 8, 0, b.z + b.d + 0.02]} material={ribbedMaterial(4)} />
    </Building>
  );
}

export function BatchB({ layout }: { layout: Layout }) {
  if (!layout.campus) return null;
  return (
    <group>
      <RawStore layout={layout} />
      <QcLab layout={layout} />
      <Workshop layout={layout} />
    </group>
  );
}
