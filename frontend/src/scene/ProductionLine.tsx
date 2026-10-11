// FAC-01 assembly line: conveyor (belt and boxes move only while the line runs), M-01 press
// (the ram strokes while running), M-02 packer, QC bench and the outbound pallet spot. Machine
// states come from their (simulated) machine monitors via the server; with no fresh data the
// machine shows "no data" and nothing moves.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { Layout, ProductionLine as Line } from "../layout";
import { useView, useWorld } from "../store/world";
import { color, model } from "../theme";
import { pickHandlers } from "./Units";
import { Baked } from "./Baked";
import { Box, Cyl, Decal, Label, mat, OutlineContext } from "./parts";

const LIGHT: Record<string, string> = { running: color.ok, idle: color.warn, maintenance: color.warn, fault: color.crit };

function useMachineState(id: string): string {
  return useWorld((s) => s.units[id]?.state ?? "no_data");
}

function StackLight({ at, state }: { at: [number, number, number]; state: string }) {
  const lit = LIGHT[state];
  return (
    <group position={at}>
      <Cyl size={[0.08, 1.2, 0.08]} at={[0, 0.6, 0]} color={model.pole} />
      {[color.crit, color.warn, color.ok].map((c, i) => (
        <Cyl key={c} size={[0.22, 0.2, 0.22]} at={[0, 1.25 + i * 0.22, 0]} shadow={false}
          material={mat(lit === c ? c : "#D0D0D0", lit === c ? { emissive: c } : {})} />
      ))}
    </group>
  );
}

const warnRing = new THREE.MeshBasicMaterial({ color: color.warn, transparent: true, opacity: 0.6, depthWrite: false });

/** Pulsing amber ring while vibration is abnormal compared with the machine's baseline. */
function AbnormalRing({ id, r }: { id: string; r: number }) {
  const abnormal = useWorld((s) => s.production?.machines.find((m) => m.id === id)?.abnormal ?? false);
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const k = 1 + 0.08 * Math.sin(clock.elapsedTime * 5);
    ref.current.scale.set(k, k, k);
  });
  if (!abnormal) return null;
  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 0]} material={warnRing}>
      <ringGeometry args={[r, r + 0.25, 48]} />
    </mesh>
  );
}

function Machine({ m, children }: { m: Line["machines"][number]; children: (state: string) => React.ReactNode }) {
  const state = useMachineState(m.id);
  const hovered = useView((s) => s.hovered === m.id);
  return (
    <group position={[m.x, 0, m.z]} {...pickHandlers(m.id)}>
      <OutlineContext.Provider value={hovered}>{children(state)}</OutlineContext.Provider>
      <StackLight at={[m.w / 2 - 0.2, m.h, -m.d / 2 + 0.2]} state={state} />
      <AbnormalRing id={m.id} r={Math.max(m.w, m.d) * 0.75} />
    </group>
  );
}

function Press({ m }: { m: Line["machines"][number] }) {
  const ram = useRef<THREE.Group>(null);
  const state = useMachineState(m.id);
  const abnormal = useWorld((s) => s.production?.machines.find((x) => x.id === m.id)?.abnormal ?? false);
  useFrame(({ clock }) => {
    if (!ram.current) return;
    const t = clock.elapsedTime;
    // One stroke per ~1.5 s while running (shown faster than the real 6 s cycle so it reads as motion).
    ram.current.position.y = state === "running" ? 1.1 + 0.55 * (0.5 + 0.5 * Math.cos(t * 4.2)) : 1.65;
    ram.current.position.x = abnormal && state === "running" ? Math.sin(t * 60) * 0.03 : 0;
  });
  return (
    <Machine m={m}>
      {() => (
        <>
          <Box size={[m.w, 0.9, m.d]} at={[0, 0, 0]} color={model.metal} />
          <Box size={[0.4, m.h - 0.9, 0.5]} at={[-m.w / 2 + 0.3, 0.9, 0]} color={color.structureDark} />
          <Box size={[0.4, m.h - 0.9, 0.5]} at={[m.w / 2 - 0.3, 0.9, 0]} color={color.structureDark} />
          <Box size={[m.w, 0.6, m.d * 0.7]} at={[0, m.h - 0.6, 0]} color={color.structure} />
          <group ref={ram}><Box size={[m.w * 0.55, 0.45, m.d * 0.5]} at={[0, 0, 0]} color={color.ink} /></group>
        </>
      )}
    </Machine>
  );
}

function Packer({ m }: { m: Line["machines"][number] }) {
  return (
    <Machine m={m}>
      {() => (
        <>
          <Box size={[m.w, m.h - 0.5, m.d]} at={[0, 0, 0]} color={model.trailer} />
          <Box size={[m.w + 0.1, 0.5, m.d + 0.1]} at={[0, m.h - 0.5, 0]} color={model.metal} />
          <Box size={[m.w * 0.6, 0.9, 0.06]} at={[0, 0.9, m.d / 2 + 0.01]} color={model.cabGlass} />
          <Box size={[1.1, 1.0, 1.0]} at={[-m.w / 2 - 0.8, 0, -m.d / 2 + 0.5]} color={color.boxDark} />
        </>
      )}
    </Machine>
  );
}

const beltTex = (() => {
  const c = document.createElement("canvas");
  c.width = 64;
  c.height = 8;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = "#3A3A3A";
  ctx.fillRect(0, 0, 64, 8);
  ctx.fillStyle = "#4A4A4A";
  ctx.fillRect(0, 0, 6, 8);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = THREE.RepeatWrapping;
  return t;
})();

const BOXES = 9;
const boxGeo = new THREE.BoxGeometry(0.6, 0.45, 0.6);
const boxMat = new THREE.MeshStandardMaterial({ color: color.box, roughness: 0.9 });

function Conveyor({ line }: { line: Line }) {
  const { from, to, width } = line.conveyor;
  const len = Math.abs(to[0] - from[0]);
  const cx = (from[0] + to[0]) / 2, z = from[1];
  const running = useWorld((s) => line.machines.some((m) => s.units[m.id]?.state === "running"));
  const mat = useMemo(() => {
    const t = beltTex.clone();
    t.needsUpdate = true;
    t.repeat.set(len / 1.2, 1);
    return new THREE.MeshStandardMaterial({ map: t, roughness: 0.9 });
  }, [len]);
  const boxes = useRef<THREE.InstancedMesh>(null);
  const travel = useRef(0);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  useFrame((_, dt) => {
    if (running) travel.current += dt * 1.2; // belt speed (m/s, shown)
    if (mat.map) mat.map.offset.x = travel.current / 1.2;
    const im = boxes.current;
    if (!im) return;
    for (let i = 0; i < BOXES; i++) {
      // Flow is east -> west: raw parts enter at the east end, finished cartons leave at the west.
      const s = (travel.current + (i * len) / BOXES) % len;
      dummy.position.set(Math.max(from[0], to[0]) - s, 1.05, z);
      dummy.updateMatrix();
      im.setMatrixAt(i, dummy.matrix);
    }
    im.instanceMatrix.needsUpdate = true;
  });
  return (
    <group>
      {/* Static frame merged into a few meshes; the belt keeps its material, so its texture still scrolls. */}
      <Baked>
        <Box size={[len, 0.12, width]} at={[cx, 0.7, z]} material={mat} />
        <Box size={[len, 0.1, 0.12]} at={[cx, 0.72, z - width / 2]} color={model.metal} />
        <Box size={[len, 0.1, 0.12]} at={[cx, 0.72, z + width / 2]} color={model.metal} />
        {Array.from({ length: Math.floor(len / 3) + 1 }, (_, i) => (
          <Box key={i} size={[0.12, 0.7, width]} at={[Math.min(from[0], to[0]) + i * 3, 0, z]} color={model.metal} />
        ))}
      </Baked>
      <instancedMesh ref={boxes} args={[boxGeo, boxMat, BOXES]} castShadow />
    </group>
  );
}

export function ProductionLine({ layout }: { layout: Layout }) {
  const line = layout.production_line;
  const out = layout.nodes.find((n) => n.id === line?.outbound_node);
  if (!line) return null;
  const press = line.machines.find((m) => m.kind === "press");
  const packer = line.machines.find((m) => m.kind === "packer");
  const spots = out?.spots ?? [];
  const xs = spots.map((p) => p[0]), zs = spots.map((p) => p[1]);
  return (
    <group>
      <Conveyor line={line} />
      {press && <Press m={press} />}
      {packer && <Packer m={packer} />}
      <Baked>
        <group position={[line.qc.x, 0, line.qc.z + 2.2]}>
          <Box size={[2.4, 0.9, 1.1]} at={[0, 0, 0]} color={model.metal} />
          <Box size={[0.9, 0.6, 0.08]} at={[0, 0.95, -0.3]} color={color.ink} />
        </group>
      </Baked>
      {line.machines.map((m) => (
        <Label key={m.id} text={`${m.id} ${m.label}`} at={[m.x, 0.04, m.z + m.d / 2 + 1.3]} width={4.6} flat color={color.ink2} weight={700} />
      ))}
      <Label text={line.qc.label} at={[line.qc.x, 0.04, line.qc.z + 3.9]} width={2.4} flat color={color.ink2} weight={700} />
      {spots.length > 0 && (
        <>
          <Decal x={(Math.min(...xs) + Math.max(...xs)) / 2} z={(Math.min(...zs) + Math.max(...zs)) / 2}
            w={Math.max(...xs) - Math.min(...xs) + 2} d={Math.max(...zs) - Math.min(...zs) + 2} c={color.marking} y={0.025} opacity={0.35} />
          <Label text="Outbound" at={[(Math.min(...xs) + Math.max(...xs)) / 2, 0.04, Math.min(...zs) - 1.6]} width={3.6} flat color={color.warn} weight={700} />
        </>
      )}
    </group>
  );
}
