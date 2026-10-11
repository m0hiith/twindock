// Forklift, built facing +x (forks forward). ~2.6 m long, 1.15 m wide: a 1.6 t counterbalance truck.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type * as THREE from "three";
import { model } from "../theme";
import { Baked } from "./Baked";
import { forkHeight } from "./interpolation";
import { Ball, Box, Cyl } from "./parts";

/** Fork height for a forklift state. Pallets.tsx uses the same so carried pallets sit on the forks. */
export function forkLift(state: string | undefined, carrying: boolean): number {
  if (state === "picking" || state === "loading") return 0.55; // raised while handling
  return carrying ? 0.3 : 0.08;
}
export const FORK_BASE_Y = 0.1;

function Wheel({ x, z, d }: { x: number; z: number; d: number }) {
  return <Cyl size={[d, 0.24, d]} at={[x, d / 2, z]} color={model.tyre} axis="z" />;
}

/** Amber beacon on the overhead guard: flashes while a pedestrian is too close (safety rule, K3). */
function Beacon() {
  const mat = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(({ clock }) => {
    if (!mat.current) return;
    const on = Math.floor(clock.elapsedTime * 4) % 2 === 0;
    mat.current.emissiveIntensity = on ? 2.4 : 0.1;
    mat.current.color.set(on ? "#FFB020" : "#7A5A10");
  });
  return (
    <mesh position={[-0.3, 2.14, 0]}>
      <cylinderGeometry args={[0.1, 0.12, 0.16, 12]} />
      <meshStandardMaterial ref={mat} color="#FFB020" emissive="#FFB020" emissiveIntensity={2} />
    </mesh>
  );
}

export function ForkliftModel({ id, state, carrying, hovered = false, beacon = false }: { id: string; state: string | undefined; carrying: boolean; hovered?: boolean; beacon?: boolean }) {
  const forks = useRef<THREE.Group>(null);
  useFrame((_, dt) => {
    const g = forks.current;
    if (!g) return;
    const target = forkLift(state, carrying);
    g.position.y += (target - g.position.y) * (1 - Math.exp(-6 * dt));
    forkHeight.set(id, g.position.y);
  });
  const body = model.forkliftBody;
  return (
    <group>
      {beacon && <Beacon />}
      <Baked outline={hovered}>
      {/* chassis and counterweight */}
      <Box size={[1.45, 0.55, 1.1]} at={[-0.27, 0.18, 0]} color={body} />
      <Box size={[0.42, 0.7, 1.12]} at={[-0.82, 0.16, 0]} color={body} />
      <Box size={[0.44, 0.08, 1.14]} at={[-0.82, 0.86, 0]} color={model.tyre} />
      <Wheel x={0.25} z={0.5} d={0.52} />
      <Wheel x={0.25} z={-0.5} d={0.52} />
      <Wheel x={-0.7} z={0.48} d={0.44} />
      <Wheel x={-0.7} z={-0.48} d={0.44} />
      {/* seat and driver */}
      <Box size={[0.42, 0.14, 0.55]} at={[-0.42, 0.73, 0]} color={model.tyre} />
      <Box size={[0.3, 0.48, 0.42]} at={[-0.42, 0.86, 0]} color={model.hiVis} />
      <Ball size={[0.27, 0.27, 0.27]} at={[-0.38, 1.5, 0]} color={model.skin} />
      {/* overhead guard */}
      {[-0.82, 0.22].flatMap((x) => [0.48, -0.48].map((z) => (
        <Box key={`${x}${z}`} size={[0.06, 1.28, 0.06]} at={[x, 0.73, z]} color={model.tyre} />
      )))}
      <Box size={[1.14, 0.06, 1.04]} at={[-0.3, 2.0, 0]} color={model.tyre} />
      {/* steering column */}
      <Box size={[0.06, 0.4, 0.06]} at={[0.05, 0.73, 0]} rot={[0, 0, -0.4]} color={model.tyre} />
      {/* mast */}
      <Box size={[0.1, 2.3, 0.1]} at={[0.52, 0.12, 0.32]} color={model.forkliftMast} />
      <Box size={[0.1, 2.3, 0.1]} at={[0.52, 0.12, -0.32]} color={model.forkliftMast} />
      <Box size={[0.1, 0.1, 0.74]} at={[0.52, 2.32, 0]} color={model.forkliftMast} />
      </Baked>
      {/* carriage and forks (lift) */}
      <group ref={forks} position={[0, forkLift(state, carrying), 0]}>
        <Box size={[0.07, 0.55, 0.78]} at={[0.6, FORK_BASE_Y, 0]} color={model.metal} />
        <Box size={[1.12, 0.05, 0.12]} at={[1.18, FORK_BASE_Y - 0.05, 0.24]} color={model.metal} />
        <Box size={[1.12, 0.05, 0.12]} at={[1.18, FORK_BASE_Y - 0.05, -0.24]} color={model.metal} />
      </group>
    </group>
  );
}
