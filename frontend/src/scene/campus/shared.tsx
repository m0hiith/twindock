// Shared pieces for the campus buildings (F2): shell with roof and cutaway walls, signage, windows, door gaps,
// picking, mounting heights for device markers. Same low-poly language as the warehouse and factory.
import { useMemo, type ReactNode } from "react";
import * as THREE from "three";
import type { Campus, CampusBuilding, Layout, Wall as WallName } from "../../layout";
import { useView, useWorld } from "../../store/world";
import { color } from "../../theme";
import { Baked } from "../Baked";
import { Box, Label, mat } from "../parts";
import { Wall, wallSegs } from "../Warehouse";

export const T = 0.3;

export const palette = {
  white: "#F4F4F2", light: "#E4E4E1", concrete: "#CFCFCC", steel: "#9A9EA3", steelDark: "#5B5F65", glass: "#B9C4CC", dark: "#2B2B2B",
  red: color.structure, redDark: color.structureDark, yellow: color.marking, green: "#2BB673", grass: "#CFE3D0", water: "#9DB4B2",
  fireRed: "#D13B2E", safety: "#F2C230",
};

type Gap = { wall: WallName; at: number; w: number };

/** Where a building's door is: the wall nearest to its door node, and the position along that wall. */
export function doorGap(b: CampusBuilding, layout: Layout): Gap | null {
  const n = layout.nodes.find((q) => q.id === b.door);
  if (!n) return null;
  const dists: [WallName, number, number][] = [
    ["north", Math.abs(n.z - b.z), n.x], ["south", Math.abs(n.z - (b.z + b.d)), n.x],
    ["west", Math.abs(n.x - b.x), n.z], ["east", Math.abs(n.x - (b.x + b.w)), n.z],
  ];
  const [wall, , at] = dists.reduce((p, q) => (q[1] < p[1] ? q : p));
  return { wall, at, w: b.kind === "security" ? 1.0 : 1.8 };
}

export function gapsOf(b: CampusBuilding, layout: Layout): Gap[] {
  const out: Gap[] = [];
  const d = doorGap(b, layout);
  if (d) out.push(d);
  for (const x of b.doors ?? []) out.push({ wall: x.wall, at: x.at, w: x.w });
  return out;
}

/** Mount height (m) of each device type: where the real kit sits, so markers stand there instead of on the floor. */
export const MOUNT_HEIGHT: Record<string, number> = {
  env_sensor: 1.6, door_sensor: 1.1, dock_bay: 4.0, machine_monitor: 1.4, conveyor_monitor: 1.2, compressor_monitor: 1.4, power_meter: 1.5,
  gas_detector: 1.5, leak_sensor: 0.05, tank_level: 6.5, fire_panel: 1.4, truck_telematics: 2.2, helmet_clip: 1.9, asset_tag: 0.6, air_quality: 2.0,
  occupancy_sensor: 2.8, badge: 1.3, light: 3, gateway: 0,
};

/** Hooks the building's group up to picking: click selects it (inspect card), hover changes the cursor. */
export function usePick(id: string) {
  return useMemo(() => ({
    onClick: (e: { stopPropagation: () => void; delta?: number }) => {
      e.stopPropagation();
      if (e.delta !== undefined && e.delta > 4) return; // that was a drag
      useView.getState().setBuilding(id);
      const b = useWorld.getState().layout?.campus?.buildings.find((x) => x.id === id);
      if (b) useView.getState().focusOn(b.x + b.w / 2, b.z + b.d / 2);
    },
    onPointerOver: () => { document.body.style.cursor = "pointer"; },
    onPointerOut: () => { document.body.style.cursor = ""; },
  }), [id]);
}

/** Signage: the building's name on the wall above its door, readable from the outside. */
export function Sign({ b, text, gap, y, width = 5.5, bg = palette.dark, fg = "#FFFFFF" }: { b: CampusBuilding; text: string; gap: Gap | null; y: number; width?: number; bg?: string; fg?: string }) {
  if (!gap) return null;
  const off = 0.2;
  const pos: [number, number, number] =
    gap.wall === "north" ? [gap.at, y, b.z - off] : gap.wall === "south" ? [gap.at, y, b.z + b.d + off] :
    gap.wall === "west" ? [b.x - off, y, gap.at] : [b.x + b.w + off, y, gap.at];
  const rotY = gap.wall === "north" ? Math.PI : gap.wall === "south" ? 0 : gap.wall === "west" ? -Math.PI / 2 : Math.PI / 2;
  return <Label text={text} at={pos} width={width} rotY={rotY} color={fg} bg={bg} weight={700} />;
}

/** Window band along the outside of the four walls, skipping the door. */
export function Windows({ b, y0 = 1.6, hh = 1.1, spacing = 3.2, gap, c = palette.glass }: { b: CampusBuilding; y0?: number; hh?: number; spacing?: number; gap: Gap | null; c?: string }) {
  const items: ReactNode[] = [];
  const mk = (wall: WallName, a: number, len: number, fixed: number) => {
    const n = Math.max(1, Math.floor(len / spacing));
    for (let i = 0; i < n; i++) {
      const at = a + (len / n) * (i + 0.5);
      if (gap && gap.wall === wall && Math.abs(gap.at - at) < gap.w / 2 + 1.0) continue;
      const alongX = wall === "north" || wall === "south";
      items.push(<Box key={`${wall}${i}`} size={alongX ? [spacing * 0.6, hh, 0.12] : [0.12, hh, spacing * 0.6]}
        at={alongX ? [at, y0, fixed] : [fixed, y0, at]} color={c} shadow={false} />);
    }
  };
  mk("north", b.x, b.w, b.z - 0.02);
  mk("south", b.x, b.w, b.z + b.d + 0.02);
  mk("west", b.z, b.d, b.x - 0.02);
  mk("east", b.z, b.d, b.x + b.w + 0.02);
  return <Baked>{items}</Baked>;
}

/**
 * Walls and roof of one building. Closed: full-height walls and a flat roof. Interiors (cutaway): no roof, and the walls
 * facing the camera drop to a kerb (same behaviour as the warehouse and factory).
 */
export function Shell({ b, layout, wall = palette.white, roof = palette.steelDark, roofExtras, floor = palette.light }: {
  b: CampusBuilding; layout: Layout; wall?: string; roof?: string; roofExtras?: ReactNode; floor?: string;
}) {
  const cutaway = useView((s) => s.cutaway);
  const gaps = gapsOf(b, layout);
  const g = (w: WallName) => gaps.filter((x) => x.wall === w);
  const wm = useMemo(() => mat(wall), [wall]);
  const segsN = wallSegs(b.x - T / 2, b.x + b.w + T / 2, g("north"));
  const segsS = wallSegs(b.x - T / 2, b.x + b.w + T / 2, g("south"));
  const segsW = wallSegs(b.z, b.z + b.d, g("west"));
  const segsE = wallSegs(b.z, b.z + b.d, g("east"));
  return (
    <group>
      <Box size={[b.w, 0.06, b.d]} at={[b.x + b.w / 2, 0, b.z + b.d / 2]} color={floor} shadow={false} />
      {cutaway ? (
        <>
          <Wall along="x" fixed={b.z} segs={segsN} normal={[0, -1]} material={wm} tall={b.h} />
          <Wall along="x" fixed={b.z + b.d} segs={segsS} normal={[0, 1]} material={wm} tall={b.h} />
          <Wall along="z" fixed={b.x} segs={segsW} normal={[-1, 0]} material={wm} tall={b.h} />
          <Wall along="z" fixed={b.x + b.w} segs={segsE} normal={[1, 0]} material={wm} tall={b.h} />
        </>
      ) : (
        <Baked>
          {segsN.map((s) => <Box key={`n${s.from}`} size={[s.to - s.from, b.h, T]} at={[(s.from + s.to) / 2, 0, b.z]} material={wm} />)}
          {segsS.map((s) => <Box key={`s${s.from}`} size={[s.to - s.from, b.h, T]} at={[(s.from + s.to) / 2, 0, b.z + b.d]} material={wm} />)}
          {segsW.map((s) => <Box key={`w${s.from}`} size={[T, b.h, s.to - s.from]} at={[b.x, 0, (s.from + s.to) / 2]} material={wm} />)}
          {segsE.map((s) => <Box key={`e${s.from}`} size={[T, b.h, s.to - s.from]} at={[b.x + b.w, 0, (s.from + s.to) / 2]} material={wm} />)}
        </Baked>
      )}
      {!cutaway && (
        <group>
          <Box size={[b.w + 0.7, 0.35, b.d + 0.7]} at={[b.x + b.w / 2, b.h, b.z + b.d / 2]} color={roof} />
          <Box size={[b.w + 0.7, 0.18, 0.18]} at={[b.x + b.w / 2, b.h + 0.35, b.z - 0.3]} color={palette.concrete} shadow={false} />
          <Box size={[b.w + 0.7, 0.18, 0.18]} at={[b.x + b.w / 2, b.h + 0.35, b.z + b.d + 0.3]} color={palette.concrete} shadow={false} />
          {roofExtras}
        </group>
      )}
    </group>
  );
}

/** A campus building: shell, windows, signage, picking, plus whatever interior and exterior the caller supplies. */
export function Building({ b, layout, children, interior, sign, wall, roof, roofExtras, windows = true, y0, hh, spacing, signW, floor }: {
  b: CampusBuilding; layout: Layout; children?: ReactNode; interior?: ReactNode; sign?: string; wall?: string; roof?: string; roofExtras?: ReactNode;
  windows?: boolean; y0?: number; hh?: number; spacing?: number; signW?: number; floor?: string;
}) {
  const gap = doorGap(b, layout);
  const pick = usePick(b.id);
  const selected = useView((s) => s.building === b.id);
  return (
    <group {...pick}>
      <Shell b={b} layout={layout} wall={wall} roof={roof} roofExtras={roofExtras} floor={floor} />
      {windows && <Windows b={b} gap={gap} y0={y0 ?? Math.min(2, b.h / 2.4)} hh={hh ?? Math.min(1.3, b.h / 4)} spacing={spacing} />}
      <Sign b={b} text={sign ?? b.name} gap={gap} y={Math.min(b.h - 0.6, 3.6)} width={signW ?? Math.min(7, Math.max(3.6, (sign ?? b.name).length * 0.42))} />
      {interior}
      {children}
      {selected && <SelectionBrackets b={b} />}
    </group>
  );
}

const bracketMat = new THREE.MeshBasicMaterial({ color: color.accent });
function SelectionBrackets({ b }: { b: CampusBuilding }) {
  const L = 2.2, t = 0.18, p = 0.8;
  const corners: [number, number, number, number][] = [[b.x - p, b.z - p, 1, 1], [b.x + b.w + p, b.z - p, -1, 1], [b.x - p, b.z + b.d + p, 1, -1], [b.x + b.w + p, b.z + b.d + p, -1, -1]];
  return (
    <group>
      {corners.flatMap(([x, z, sx, sz], i) => [
        <mesh key={`${i}a`} material={bracketMat} position={[x + (sx * L) / 2, 0.08, z]}><boxGeometry args={[L, 0.06, t]} /></mesh>,
        <mesh key={`${i}b`} material={bracketMat} position={[x, 0.08, z + (sz * L) / 2]}><boxGeometry args={[t, 0.06, L]} /></mesh>,
      ])}
    </group>
  );
}

/** Device readings by id, for animations (generator running, compressor loaded, tank level). */
export function useReading(deviceId: string, channel: string): unknown {
  return useWorld((s) => s.devices[deviceId]?.readings[channel]?.value);
}
export function useNum(deviceId: string, channel: string): number | null {
  const v = useReading(deviceId, channel);
  const online = useWorld((s) => s.devices[deviceId]?.status === "online");
  return online && typeof v === "number" ? v : null;
}

/** Sun factor 0..1 from local time of day (sunrise 6:00, sunset 18:00): drives rooftop solar output. */
export function sunFactor(date = new Date()): number {
  const h = date.getHours() + date.getMinutes() / 60;
  return h <= 6 || h >= 18 ? 0 : Math.sin((Math.PI * (h - 6)) / 12);
}

export function useCampus(layout: Layout): Campus | null {
  return layout.campus ?? null;
}

export function useBuilding(id: string, layout: Layout): CampusBuilding | undefined {
  return useMemo(() => layout.campus?.buildings.find((b) => b.id === id), [id, layout]);
}

