// F2 batch A: main gate (security cabin, weighbridge, boom barrier), car park with EV chargers and two-wheeler park,
// admin block, canteen, first-aid room.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type * as THREE from "three";
import type { CampusBuilding, Layout } from "../../layout";
import { useWorld } from "../../store/world";
import { Baked } from "../Baked";
import { Box, Cyl, Decal, Label } from "../parts";
import { Building, palette, useBuilding, useNum } from "./shared";

function hash(i: number): number {
  const s = Math.sin(i * 12.9898) * 43758.5453;
  return s - Math.floor(s);
}
const CAR_COLORS = ["#F4F4F2", "#2B2B2B", "#9A9EA3", "#D91E2A", "#CFCFCC", "#5B5F65", "#F2C230"];

function Car({ x, z, c, rot = 0 }: { x: number; z: number; c: string; rot?: number }) {
  return (
    <group position={[x, 0, z]} rotation={[0, rot, 0]}>
      <Box size={[1.8, 0.7, 4.2]} at={[0, 0.25, 0]} color={c} />
      <Box size={[1.6, 0.6, 2.2]} at={[0, 0.95, -0.1]} color={palette.glass} />
      {[[-0.85, -1.3], [0.85, -1.3], [-0.85, 1.3], [0.85, 1.3]].map(([dx, dz]) => <Cyl key={`${dx}${dz}`} size={[0.55, 0.2, 0.55]} at={[dx!, 0.28, dz!]} color="#2B2B2B" axis="x" shadow={false} />)}
    </group>
  );
}

function CarPark({ layout }: { layout: Layout }) {
  const c = layout.campus!;
  const p = c.parking;
  const { x, z, w, d, rows, bays_per_row } = p.cars;
  const bayW = 2.6, bayD = 5.2;
  const cars = useMemo(() => {
    const out: { x: number; z: number; c: string }[] = [];
    for (let r = 0; r < rows; r++) {
      const rowZ = z + 2.5 + r * (bayD * 1.4 + 1.2);
      for (let b = 0; b < bays_per_row; b++) {
        const bx = x + 8 + b * bayW * 1.5;
        if (bx + bayW > x + w - 1) continue;
        if (hash(r * 31 + b) < 0.38) continue; // not every bay is taken
        out.push({ x: bx + bayW / 2, z: rowZ + bayD / 2, c: CAR_COLORS[Math.floor(hash(r * 7 + b * 3) * CAR_COLORS.length)]! });
      }
    }
    return out;
  }, [x, z, w, rows, bays_per_row]);
  return (
    <group>
      <Decal x={x + w / 2} z={z + d / 2} w={w} d={d} c="#D8D8D4" y={0.012} />
      <Baked>
        {Array.from({ length: rows }, (_, r) => {
          const rowZ = z + 2.5 + r * (bayD * 1.4 + 1.2);
          return Array.from({ length: bays_per_row + 1 }, (_, b) => {
            const bx = x + 8 + b * bayW * 1.5;
            return bx < x + w - 1 ? <Decal key={`${r}${b}`} x={bx} z={rowZ + bayD / 2} w={0.1} d={bayD} c="#FFFFFF" y={0.02} /> : null;
          });
        })}
        {cars.map((cr, i) => <Car key={i} x={cr.x} z={cr.z} c={cr.c} />)}
      </Baked>
      <Label text="Car park" at={[x + 26, 0.04, z + d - 1.4]} width={7} flat color={palette.steelDark} weight={700} />
      {p.ev_chargers.map((e) => <EvCharger key={e.id} x={e.x} z={e.z} />)}
      <Label text="EV charging" at={[p.ev_chargers[2]?.x ?? x + 6, 0.04, z + 4.6]} width={5} flat color={palette.green} weight={800} />
      <TwoWheelers layout={layout} />
    </group>
  );
}

function EvCharger({ x, z }: { x: number; z: number }) {
  const kw = useNum("PM-02", "power_kw") ?? 0;
  return (
    <group position={[x, 0, z]}>
      <Box size={[0.5, 1.4, 0.3]} at={[0, 0, 0]} color={palette.white} />
      <Box size={[0.36, 0.1, 0.05]} at={[0, 1.0, 0.16]} color={kw > 1 ? palette.green : palette.steel} shadow={false} />
      <Decal x={0} z={1.9} w={2.4} d={4.6} c="#CFE3D0" y={0.015} />
    </group>
  );
}

function TwoWheelers({ layout }: { layout: Layout }) {
  const t = layout.campus!.parking.two_wheelers;
  return (
    <group>
      <Decal x={t.x + t.w / 2} z={t.z + t.d / 2} w={t.w} d={t.d} c="#D8D8D4" y={0.012} />
      <Baked>
        {Array.from({ length: 6 }, (_, i) => hash(i + 40) > 0.25 && (
          <group key={i} position={[t.x + 1.2 + i * 1.5, 0, t.z + t.d / 2]}>
            <Box size={[0.4, 0.5, 1.8]} at={[0, 0.25, 0]} color={CAR_COLORS[i % CAR_COLORS.length]!} />
            <Box size={[0.5, 0.1, 0.5]} at={[0, 0.8, 0.1]} color="#2B2B2B" />
          </group>
        ))}
      </Baked>
      <Label text="Two-wheelers" at={[t.x + t.w / 2, 0.04, t.z + t.d - 0.9]} width={5} flat color={palette.steelDark} weight={700} />
    </group>
  );
}

function Gate({ layout }: { layout: Layout }) {
  const c = layout.campus!;
  const wb = c.weighbridge, bar = c.barrier;
  const cabin = useBuilding("SEC_CABIN", layout);
  const arm = useRef<THREE.Group>(null);
  const open = useRef(0);
  useFrame((_, dt) => {
    // The boom lifts while a truck is within 9 m of it, then drops.
    const near = Object.values(useWorld.getState().units).some((u) => u.kind === "truck" && Math.hypot(u.x - bar.x, u.z - (bar.z0 + bar.z1) / 2) < 9);
    open.current += ((near ? 1 : 0) - open.current) * (1 - Math.exp(-3 * dt));
    if (arm.current) arm.current.rotation.x = -open.current * 1.25;
  });
  return (
    <group>
      <Box size={[wb.w, 0.22, wb.d]} at={[wb.x + wb.w / 2, 0, wb.z + wb.d / 2]} color={palette.steel} />
      <Decal x={wb.x + wb.w / 2} z={wb.z + wb.d / 2} w={wb.w - 0.6} d={0.12} c={palette.safety} y={0.24} />
      <Box size={[0.5, 2.6, 0.5]} at={[wb.x + wb.w + 0.6, 0, wb.z - 0.8]} color={palette.dark} />
      <Label text="Weighbridge" at={[wb.x + wb.w / 2, 0.26, wb.z + wb.d + 1.2]} width={6} flat color={palette.steelDark} weight={800} />
      {/* boom barrier: post, counterweight housing and a striped arm across the lane */}
      <Box size={[0.7, 1.2, 0.7]} at={[bar.x, 0, bar.z0 - 0.4]} color={palette.red} />
      <group position={[bar.x, 1.0, bar.z0 - 0.4]}>
        <group ref={arm}>
          {Array.from({ length: 7 }, (_, i) => (
            <Box key={i} size={[0.14, 0.14, (bar.z1 - bar.z0) / 7]} at={[0, 0, 0.35 + (i * (bar.z1 - bar.z0)) / 7]} color={i % 2 ? "#FFFFFF" : palette.red} shadow={false} />
          ))}
        </group>
      </group>
      <Label text="Main gate" at={[bar.x, 0.04, bar.z1 + 2.2]} width={5} flat color={palette.red} weight={800} />
      {cabin && (
        <Building b={cabin} layout={layout} sign="Security" wall={palette.white} roof={palette.red} windows={false} signW={3}
          interior={<>
            <Box size={[2.2, 0.9, 0.7]} at={[cabin.x + cabin.w / 2, 0, cabin.z + cabin.d / 2]} color={palette.steel} />
            <Box size={[0.5, 0.35, 0.4]} at={[cabin.x + cabin.w / 2, 0.9, cabin.z + cabin.d / 2]} color={palette.dark} />
          </>}>
          <Box size={[cabin.w - 0.4, 1.0, 0.12]} at={[cabin.x + cabin.w / 2, 1.2, cabin.z + 0.05]} color={palette.glass} shadow={false} />
          <Box size={[cabin.w - 0.4, 1.0, 0.12]} at={[cabin.x + cabin.w / 2, 1.2, cabin.z + cabin.d - 0.05]} color={palette.glass} shadow={false} />
          <Label text="Visitor check-in" at={[cabin.x + cabin.w / 2, 0.04, cabin.z - 1.6]} width={5} flat color={palette.steelDark} weight={700} />
        </Building>
      )}
    </group>
  );
}

function Desks({ b, rows = 3, per = 4, gx = 3.2, gz = 3.4, x0 = 3, z0 = 3 }: { b: CampusBuilding; rows?: number; per?: number; gx?: number; gz?: number; x0?: number; z0?: number }) {
  return (
    <Baked>
      {Array.from({ length: rows }, (_, r) => Array.from({ length: per }, (_, k) => (
        <group key={`${r}${k}`} position={[b.x + x0 + k * gx, 0, b.z + z0 + r * gz]}>
          <Box size={[1.5, 0.75, 0.8]} at={[0, 0, 0]} color="#D8C3A5" />
          <Box size={[0.5, 0.35, 0.05]} at={[0, 0.78, -0.2]} color={palette.dark} shadow={false} />
          <Box size={[0.5, 0.5, 0.5]} at={[0, 0, 0.8]} color={palette.steelDark} />
        </group>
      )))}
    </Baked>
  );
}

function Admin({ layout }: { layout: Layout }) {
  const b = useBuilding("ADMIN", layout);
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Admin and reception" wall={palette.white} roof={palette.steelDark} y0={1.2} hh={1.2} spacing={3.4}
      roofExtras={<>
        <Box size={[3, 1.2, 2.2]} at={[b.x + 5, b.h + 0.35, b.z + 5]} color={palette.concrete} />
        <Box size={[3, 1.2, 2.2]} at={[b.x + 12, b.h + 0.35, b.z + 5]} color={palette.concrete} />
      </>}
      interior={<>
        <Box size={[b.w - 0.4, 0.2, b.d - 0.4]} at={[b.x + b.w / 2, 3.6, b.z + b.d / 2]} color={palette.light} shadow={false} />
        <Box size={[4, 1.0, 0.9]} at={[b.x + b.w / 2, 0, b.z + 2.2]} color={palette.steel} />
        <Desks b={b} rows={2} per={5} x0={3} z0={6.5} gx={3.4} gz={3.6} />
      </>}>
      <Box size={[6, 0.25, 2.6]} at={[b.x + b.w / 2, 3.1, b.z - 1.3]} color={palette.red} />
      <Box size={[0.2, 3.1, 0.2]} at={[b.x + b.w / 2 - 2.8, 0, b.z - 2.4]} color={palette.steel} />
      <Box size={[0.2, 3.1, 0.2]} at={[b.x + b.w / 2 + 2.8, 0, b.z - 2.4]} color={palette.steel} />
      <Cyl size={[0.12, 7, 0.12]} at={[b.x + b.w + 1.6, 3.5, b.z - 1.4]} color={palette.steel} />
    </Building>
  );
}

function Canteen({ layout }: { layout: Layout }) {
  const b = useBuilding("CANTEEN", layout);
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Canteen" wall="#F2E4D0" roof={palette.steelDark} y0={1.1} hh={1.3} spacing={3}
      roofExtras={<Cyl size={[0.9, 1.6, 0.9]} at={[b.x + b.w - 3, b.h + 0.8, b.z + 3]} color={palette.steel} />}
      interior={<>
        <Box size={[b.w - 3, 0.95, 0.9]} at={[b.x + b.w / 2, 0, b.z + b.d - 1.4]} color={palette.steel} />
        <Baked>
          {Array.from({ length: 3 }, (_, r) => Array.from({ length: 3 }, (_, k) => (
            <group key={`${r}${k}`} position={[b.x + 3.4 + k * 4.2, 0, b.z + 2.6 + r * 2.7]}>
              <Box size={[2.2, 0.75, 1.0]} at={[0, 0, 0]} color="#D8C3A5" />
              <Box size={[2.4, 0.4, 0.3]} at={[0, 0, -0.75]} color={palette.red} />
              <Box size={[2.4, 0.4, 0.3]} at={[0, 0, 0.75]} color={palette.red} />
            </group>
          )))}
        </Baked>
      </>} />
  );
}

function Medical({ layout }: { layout: Layout }) {
  const b = useBuilding("MEDICAL", layout);
  if (!b) return null;
  const cx = b.x + b.w / 2, cz = b.z + b.d / 2;
  return (
    <Building b={b} layout={layout} sign="First aid" wall="#FFFFFF" roof={palette.light} y0={1.2} hh={1.0} spacing={3} signW={3.4}
      roofExtras={<>
        <Box size={[2.6, 0.08, 0.7]} at={[cx, b.h + 0.4, cz]} color={palette.fireRed} shadow={false} />
        <Box size={[0.7, 0.08, 2.6]} at={[cx, b.h + 0.4, cz]} color={palette.fireRed} shadow={false} />
      </>}
      interior={<>
        <Box size={[2, 0.6, 0.9]} at={[b.x + 2.2, 0, b.z + 3]} color="#FFFFFF" />
        <Box size={[1.6, 1.8, 0.5]} at={[b.x + b.w - 1.6, 0, b.z + 2]} color={palette.steel} />
      </>} />
  );
}

export function BatchA({ layout }: { layout: Layout }) {
  if (!layout.campus) return null;
  return (
    <group>
      <Gate layout={layout} />
      <CarPark layout={layout} />
      <Admin layout={layout} />
      <Canteen layout={layout} />
      <Medical layout={layout} />
    </group>
  );
}
