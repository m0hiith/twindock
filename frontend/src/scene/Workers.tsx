// Workers (simulated BLE badges) as small low-poly people in hi-vis, plus pulsing safety rings:
// amber = pedestrian within the warning distance of a moving forklift, red = critical distance or a
// restricted zone. The same ring is drawn under the forklift involved.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import { useShallow } from "zustand/react/shallow";
import { useView, useWorld } from "../store/world";
import { color, model } from "../theme";
import { useInterpolatedPose } from "./interpolation";
import { Box, Ball, Cyl, OutlineContext } from "./parts";
import { pickHandlers } from "./Units";

const ringMats = { warning: new THREE.MeshBasicMaterial({ color: color.warn, transparent: true, opacity: 0.75, depthWrite: false }),
  critical: new THREE.MeshBasicMaterial({ color: color.crit, transparent: true, opacity: 0.8, depthWrite: false }) };
const ringGeo = new THREE.RingGeometry(1.0, 1.25, 40).rotateX(-Math.PI / 2);

function Pulse({ level, scale = 1 }: { level: "warning" | "critical"; scale?: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    const k = scale * (1 + 0.25 * (0.5 + 0.5 * Math.sin(clock.elapsedTime * (level === "critical" ? 9 : 5))));
    ref.current?.scale.set(k, 1, k);
  });
  return <mesh ref={ref} geometry={ringGeo} position={[0, 0.06, 0]} material={ringMats[level]} />;
}

function Worker({ id }: { id: string }) {
  const ref = useRef<THREE.Group>(null);
  useInterpolatedPose(id, ref);
  const hovered = useView((s) => s.hovered === id);
  const state = useWorld((s) => s.units[id]?.state);
  const alert = useWorld((s) => {
    const w = s.safety?.workers.find((x) => x.id === id);
    if (!w) return null;
    if (w.restricted_zone || w.near?.level === "critical") return "critical" as const;
    return w.near ? ("warning" as const) : null;
  });
  if (state === "no_data") return null; // no fresh badge position: don't draw a guess
  return (
    <group ref={ref} {...pickHandlers(id)}>
      <OutlineContext.Provider value={hovered}>
        <Box size={[0.22, 0.8, 0.18]} at={[0, 0, -0.13]} color={color.ink} />
        <Box size={[0.22, 0.8, 0.18]} at={[0, 0, 0.13]} color={color.ink} />
        <Box size={[0.34, 0.7, 0.56]} at={[0, 0.8, 0]} color={model.hiVis} />
        <Box size={[0.36, 0.06, 0.58]} at={[0, 1.1, 0]} color="#E5E7E5" shadow={false} />
        <Ball size={[0.3, 0.3, 0.3]} at={[0, 1.66, 0]} color={model.skin} />
        <Cyl size={[0.36, 0.14, 0.36]} at={[0, 1.78, 0]} color={color.marking} />
      </OutlineContext.Provider>
      {alert && <Pulse level={alert} />}
    </group>
  );
}

function ForkliftRing({ id, level }: { id: string; level: "warning" | "critical" }) {
  const ref = useRef<THREE.Group>(null);
  useInterpolatedPose(id, ref);
  return <group ref={ref}><Pulse level={level} scale={2.2} /></group>;
}

export function Workers() {
  const ids = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "worker").map((u) => u.id)));
  const near = useWorld(useShallow((s) => (s.safety?.workers ?? []).filter((w) => w.near).map((w) => `${w.near!.forklift}:${w.near!.level}`)));
  // One ring per forklift, the worst level if several workers are near it.
  const byForklift = new Map<string, "warning" | "critical">();
  for (const k of near) {
    const [f, level] = k.split(":") as [string, "warning" | "critical"];
    if (byForklift.get(f) !== "critical") byForklift.set(f, level);
  }
  return (
    <group>
      {ids.map((id) => <Worker key={id} id={id} />)}
      {[...byForklift].map(([f, level]) => <ForkliftRing key={f} id={f} level={level} />)}
    </group>
  );
}
