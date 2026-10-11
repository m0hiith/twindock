// F2 batch C: substation and transformer, diesel generator, air compressor room, water tanks and pumps, effluent
// treatment plant, hazardous materials store, fire pump house and tank, rooftop solar. Utilities animate with the
// state of their (simulated) devices: generator running, compressor cycling, tank levels, solar by time of day.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { Layout } from "../../layout";
import { useView } from "../../store/world";
import { Baked } from "../Baked";
import { Box, Cyl, Decal, Label } from "../parts";
import { Building, palette, sunFactor, Tank, useBuilding, useNum, usePick, Yard } from "./shared";

function SubstationYard({ layout }: { layout: Layout }) {
  const b = useBuilding("SUBSTATION", layout);
  const kw = useNum("PM-04", "power_kw");
  if (!b) return null;
  return (
    <Yard b={b} layout={layout} wall={1.1} sign="Substation" signBg={palette.red} c="#BDBDB8">
      {/* two oil-filled transformers: tank, cooling fins and three bushings each */}
      {[0, 1].map((i) => (
        <group key={i} position={[b.x + 5 + i * 5.5, 0, b.z + 6]}>
          <Box size={[3.0, 2.4, 2.2]} at={[0, 0.4, 0]} color={palette.steelDark} />
          <Box size={[0.35, 2.0, 2.0]} at={[1.7, 0.6, 0]} color={palette.steel} />
          <Box size={[0.35, 2.0, 2.0]} at={[-1.7, 0.6, 0]} color={palette.steel} />
          {[-0.8, 0, 0.8].map((dz) => <Cyl key={dz} size={[0.22, 0.9, 0.22]} at={[0, 3.3, dz]} color="#F4F4F2" />)}
          <Box size={[0.5, 0.4, 0.5]} at={[0, 2.8, 0]} color={palette.dark} shadow={false} />
        </group>
      ))}
      {/* switchgear cabin */}
      <Box size={[5, 3, 3]} at={[b.x + 11, 0, b.z + 2.6]} color={palette.white} />
      <Box size={[5.4, 0.3, 3.4]} at={[b.x + 11, 3, b.z + 2.6]} color={palette.red} />
      {/* gantry with insulators */}
      {[0, 1, 2].map((i) => <Cyl key={i} size={[0.12, 4.6, 0.12]} at={[b.x + 2 + i * 1.6, 2.3, b.z + 10.5]} color={palette.steel} />)}
      <Box size={[5, 0.12, 0.12]} at={[b.x + 3.6, 4.6, b.z + 10.5]} color={palette.steel} />
      {kw !== null && <Label text={`${kw.toFixed(0)} kW`} at={[b.x + b.w / 2, 0.06, b.z + b.d - 1.2]} width={4.4} flat color={palette.steelDark} weight={800} />}
    </Yard>
  );
}

const puffGeo = new THREE.SphereGeometry(0.35, 8, 6);
const puffMat = new THREE.MeshBasicMaterial({ color: "#8E9296", transparent: true, opacity: 0.45, depthWrite: false });

function GeneratorSet({ layout }: { layout: Layout }) {
  const b = useBuilding("GENERATOR", layout);
  const kw = useNum("PM-05", "power_kw");
  const level = useNum("TL-02", "level_pct");
  const running = (kw ?? 0) > 1;
  const body = useRef<THREE.Group>(null);
  const puffs = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    if (body.current) body.current.position.y = running ? Math.sin(t * 55) * 0.012 : 0; // engine shake
    puffs.current?.children.forEach((p, i) => {
      const k = running ? ((t * 0.6 + i / 5) % 1) : 1;
      p.visible = running;
      p.position.set(0, 4.6 + k * 3.2, 0);
      p.scale.setScalar(0.6 + k * 1.6);
      (p as THREE.Mesh).material = puffMat;
    });
  });
  if (!b) return null;
  const cx = b.x + b.w / 2, cz = b.z + b.d / 2;
  return (
    <Building b={b} layout={layout} sign="Generator" wall="#EDEDEA" roof={palette.steelDark} windows={false} signW={3.4}
      interior={<Box size={[b.w - 3, 1.6, b.d - 4]} at={[cx, 0, cz]} color={palette.safety} />}
      roofExtras={
        <group position={[b.x + b.w - 2.5, b.h + 0.35, b.z + 2.4]}>
          <Cyl size={[0.6, 4.2, 0.6]} at={[0, 2.1, 0]} color={palette.steelDark} />
          <group ref={puffs}>{Array.from({ length: 5 }, (_, i) => <mesh key={i} geometry={puffGeo} material={puffMat} />)}</group>
        </group>
      }>
      <group ref={body} />
      <Label text={running ? `Running ${kw?.toFixed(0)} kW` : "Stopped"} at={[cx, 0.06, b.z + b.d + 1.3]} width={5.4} flat color={running ? palette.green : palette.steelDark} weight={800} />
      <Tank x={205} z={-8} r={1.6} h={3} level={level === null ? null : level / 100} fill={palette.safety} shell="#E9E9E6" />
      <Label text="Diesel" at={[205, 0.06, -5.2]} width={2.4} flat color={palette.steelDark} weight={700} />
    </Building>
  );
}

function CompressorRoom({ layout }: { layout: Layout }) {
  const b = useBuilding("COMPRESSOR", layout);
  const current = useNum("CP-01", "current_a");
  const bar = useNum("CP-01", "pressure_bar");
  const loaded = (current ?? 0) > 30;
  const fan = useRef<THREE.Group>(null);
  useFrame((_, dt) => { if (fan.current) fan.current.rotation.y += dt * (loaded ? 9 : 0.6); });
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Compressor room" wall="#E4E4E1" roof={palette.steelDark} windows={false} signW={5.8}
      roofExtras={
        <group position={[b.x + 5, b.h + 0.35, b.z + 6]}>
          <Cyl size={[2.2, 0.5, 2.2]} at={[0, 0.25, 0]} color={palette.steel} />
          <group ref={fan} position={[0, 0.55, 0]}>
            {[0, 1, 2].map((i) => <Box key={i} size={[1.8, 0.06, 0.28]} at={[0, 0, 0]} rot={[0, (i * Math.PI) / 3, 0]} color={palette.dark} shadow={false} />)}
          </group>
        </group>
      }
      interior={<>
        {[0, 1].map((i) => (
          <group key={i} position={[b.x + 4 + i * 5.2, 0, b.z + 4.2]}>
            <Box size={[3.2, 1.9, 1.6]} at={[0, 0, 0]} color={palette.safety} />
            <Box size={[2.4, 0.4, 1.4]} at={[0, 1.9, 0]} color={palette.steelDark} />
          </group>
        ))}
        <Cyl size={[1.4, 3.2, 1.4]} at={[b.x + b.w - 2, 1.6, b.z + b.d - 3]} color={palette.steel} />
        <Box size={[b.w - 3, 0.18, 0.18]} at={[b.x + b.w / 2, 3.0, b.z + b.d - 1.2]} color={palette.fireRed} shadow={false} />
      </>}>
      <Label text={bar === null ? "No data" : `${bar.toFixed(1)} bar · ${loaded ? "loaded" : "unloaded"}`} at={[b.x + b.w / 2, 0.06, b.z + b.d + 1.3]} width={6} flat color={palette.steelDark} weight={800} />
    </Building>
  );
}

function WaterTanks({ layout }: { layout: Layout }) {
  const c = layout.campus!;
  const l1 = useNum("TL-01", "level_pct"), l2 = useNum("TL-03", "level_pct");
  const pump = useBuilding("PUMP_HOUSE", layout);
  const pick = usePick("PUMP_HOUSE");
  return (
    <group>
      <group {...pick}>
        <Tank x={c.tanks[0]!.x} z={c.tanks[0]!.z} r={c.tanks[0]!.r} h={c.tanks[0]!.h} level={l1 === null ? null : l1 / 100} />
        <Tank x={c.tanks[1]!.x} z={c.tanks[1]!.z} r={c.tanks[1]!.r} h={c.tanks[1]!.h} level={l2 === null ? null : l2 / 100} />
        <Box size={[0.2, 0.2, 10]} at={[180.5, 0.3, 29]} color={palette.steel} shadow={false} />
      </group>
      {pump && <Building b={pump} layout={layout} sign="Pumps" wall="#E9E9E6" roof={palette.steelDark} windows={false} signW={2.2} />}
      <Label text="Water tanks" at={[180.5, 0.06, 36.8]} width={6} flat color={palette.steelDark} weight={800} />
    </group>
  );
}

const waterMat = new THREE.MeshStandardMaterial({ color: "#8FA9A8", roughness: 0.25 });
function Aerator({ x, z }: { x: number; z: number }) {
  const g = useRef<THREE.Group>(null);
  useFrame((_, dt) => { if (g.current) g.current.rotation.y += dt * 2.4; });
  return (
    <group position={[x, 0.55, z]}>
      <Cyl size={[0.2, 0.6, 0.2]} at={[0, 0, 0]} color={palette.steelDark} />
      <group ref={g}>{[0, 1].map((i) => <Box key={i} size={[1.8, 0.1, 0.22]} at={[0, 0.5, 0]} rot={[0, i * Math.PI / 2, 0]} color={palette.steel} shadow={false} />)}</group>
    </group>
  );
}

function Etp({ layout }: { layout: Layout }) {
  const e = layout.campus!.etp;
  const level = useNum("TL-04", "level_pct");
  const wet = useNum("LK-03", "wet");
  const b = { id: "ETP", x: e.x, z: e.z, w: e.w, d: e.d, door: e.door, name: "Effluent treatment plant" };
  return (
    <Yard b={b} layout={layout} wall={1.2} sign="Effluent treatment plant" c="#BDBDB8">
      {e.basins.map((q, i) => (
        <group key={i}>
          <Box size={[q.w, 0.9, q.d]} at={[q.x + q.w / 2, 0, q.z + q.d / 2]} color="#C9C9C5" />
          <mesh position={[q.x + q.w / 2, 0.92, q.z + q.d / 2]} scale={[q.w - 0.5, 1, q.d - 0.5]} material={waterMat}><planeGeometry args={[1, 1]} /></mesh>
          <Label text={q.label} at={[q.x + q.w / 2, 0.06, q.z + q.d + 0.9]} width={Math.max(3, q.w * 0.8)} flat color={palette.steelDark} weight={700} />
        </group>
      ))}
      {e.basins[1] && <Aerator x={e.basins[1].x + e.basins[1].w / 2} z={e.basins[1].z + e.basins[1].d / 2} />}
      <Box size={[3, 2.6, 2.4]} at={[e.x + 14.5, 0, e.z + 2]} color={palette.white} />
      <Box size={[3.4, 0.25, 2.8]} at={[e.x + 14.5, 2.6, e.z + 2]} color={palette.red} />
      <Tank x={205} z={18} r={1.5} h={3.2} level={level === null ? null : level / 100} fill="#8FA9A8" />
      {wet !== null && wet > 0 && <Label text="Leak" at={[e.x + 8, 0.08, e.z + 20]} width={3} flat color={palette.fireRed} weight={800} />}
    </Yard>
  );
}

function Hazmat({ layout }: { layout: Layout }) {
  const b = useBuilding("HAZMAT", layout);
  const co = useNum("GD-04", "co_ppm");
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Hazardous materials" wall="#F1ECD8" roof={palette.steelDark} windows={false} signW={7} floor="#E8E3C8"
      interior={
        <Baked>
          {Array.from({ length: 3 }, (_, r) => Array.from({ length: 5 }, (_, k) => (
            <Cyl key={`${r}${k}`} size={[0.7, 1.0, 0.7]} at={[b.x + 3 + k * 2.2, 0.5, b.z + 3 + r * 3]} color={(r + k) % 2 ? palette.fireRed : palette.safety} />
          )))}
        </Baked>
      }>
      {/* bund: a low wall round the store, 2 m clear of it */}
      {[[b.x - 1.6, b.z - 1.6, b.w + 3.2, 0.3], [b.x - 1.6, b.z + b.d + 1.3, b.w + 3.2, 0.3], [b.x - 1.6, b.z - 1.6, 0.3, b.d + 3.2], [b.x + b.w + 1.3, b.z - 1.6, 0.3, b.d + 3.2]].map(([x, z, w, d], i) => (
        <Box key={i} size={[w!, 0.7, d!]} at={[x! + w! / 2, 0, z! + d! / 2]} color="#C9C9C5" />
      ))}
      <Decal x={b.x + b.w / 2} z={b.z + b.d + 2.6} w={3} d={3} c={palette.safety} y={0.03} rot={Math.PI / 4} />
      <Label text="!" at={[b.x + b.w / 2, 0.06, b.z + b.d + 2.6]} width={1.6} flat color={palette.dark} weight={900} />
      {co !== null && <Label text={`CO ${co.toFixed(0)} ppm`} at={[b.x + b.w / 2, 0.06, b.z - 2.6]} width={4.6} flat color={co > 35 ? palette.fireRed : palette.steelDark} weight={800} />}
    </Building>
  );
}

function FirePump({ layout }: { layout: Layout }) {
  const b = useBuilding("FIRE_PUMP", layout);
  const level = useNum("TL-05", "level_pct");
  const t = layout.campus!.tanks.find((x) => x.id === "FT-1")!;
  if (!b) return null;
  return (
    <Building b={b} layout={layout} sign="Fire pump house" wall="#F2DAD6" roof={palette.fireRed} windows={false} signW={5.6}
      interior={<>
        <Box size={[2.6, 1.3, 1.2]} at={[b.x + 3, 0, b.z + 3]} color={palette.fireRed} />
        <Box size={[2.2, 1.0, 1.1]} at={[b.x + 7, 0, b.z + 3]} color={palette.steelDark} />
      </>}>
      <Tank x={t.x} z={t.z} r={t.r} h={t.h} level={level === null ? null : level / 100} shell="#E7BDB7" fill="#8FA9A8" />
      <Cyl size={[0.25, 5, 0.25]} at={[t.x + t.r + 0.6, 2.5, t.z]} color={palette.fireRed} />
      <Label text="Fire water" at={[t.x, 0.06, t.z + t.r + 1.4]} width={4} flat color={palette.fireRed} weight={800} />
    </Building>
  );
}

// ------------------------------------------------------------------ rooftop solar

const panelMat = new THREE.MeshStandardMaterial({ color: "#2E3238", roughness: 0.35, metalness: 0.2, emissive: "#000000" });
const cellGeo = new THREE.BoxGeometry(1, 1, 1);

function SolarArray({ panels, y }: { panels: [number, number, number, number][]; y: number }) {
  const group = useRef<THREE.Group>(null);
  const cells = useMemo(() => panels.flatMap(([x, z, w, d]) => {
    const out: { x: number; z: number }[] = [];
    for (let i = 0; i < Math.floor(w / 2.2); i++) for (let j = 0; j < Math.floor(d / 1.4); j++) out.push({ x: x + 1.1 + i * 2.2, z: z + 0.8 + j * 1.4 });
    return out;
  }), [panels]);
  useFrame(() => {
    const f = sunFactor();
    panelMat.color.setRGB(0.18 + 0.2 * f, 0.2 + 0.22 * f, 0.22 + 0.28 * f); // brighter in the sun
    panelMat.emissive.setRGB(0.12 * f, 0.1 * f, 0.02 * f);
  });
  return (
    <group ref={group} position={[0, y, 0]}>
      {cells.map((c, i) => <mesh key={i} geometry={cellGeo} material={panelMat} position={[c.x, 0.2, c.z]} scale={[2.0, 0.08, 1.25]} rotation={[-0.14, 0, 0]} />)}
    </group>
  );
}

export function SolarRoofs({ layout }: { layout: Layout }) {
  const c = layout.campus!;
  const cutaway = useView((s) => s.cutaway);
  const overview = useView((s) => s.site) === "ALL";
  return (
    <group>
      {c.solar.map((s) => {
        const b = layout.buildings.find((q) => q.id === s.building) ?? c.buildings.find((q) => q.id === s.building);
        if (!b) return null;
        const campusOwned = c.buildings.some((q) => q.id === s.building);
        // New buildings show their panels while the roof is closed; the warehouse and the factory hall are always cut away
        // (their interiors are the point of /twin), so their arrays show in the overview where the roofs are drawn flat.
        if (campusOwned ? cutaway : !overview) return null;
        const h = ("h" in b ? b.h : 6) + 0.5;
        return (
          <group key={s.id}>
            {!campusOwned && <Box size={[b.w + 0.6, 0.3, b.d + 0.6]} at={[b.x + b.w / 2, h - 0.5, b.z + b.d / 2]} color={palette.steel} shadow={false} />}
            <SolarArray panels={s.panels} y={h} />
          </group>
        );
      })}
    </group>
  );
}

export function BatchC({ layout }: { layout: Layout }) {
  if (!layout.campus) return null;
  return (
    <group>
      <SubstationYard layout={layout} />
      <GeneratorSet layout={layout} />
      <CompressorRoom layout={layout} />
      <WaterTanks layout={layout} />
      <Etp layout={layout} />
      <Hazmat layout={layout} />
      <FirePump layout={layout} />
      <SolarRoofs layout={layout} />
    </group>
  );
}

