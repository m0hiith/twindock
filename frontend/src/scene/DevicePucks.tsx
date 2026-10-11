// Site-twin device markers: small low-poly sensor pucks with a status ring. Hidden by default;
// the "Devices" map control shows them. GW-01 already has its pole (GatewayPole), so it gets no puck.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { useShallow } from "zustand/react/shallow";
import type { Device } from "../contract";
import { deviceTone, type Tone } from "../status";
import { useView, useWorld } from "../store/world";
import { color } from "../theme";
import { pickHandlers } from "./Units";
import { MOUNT_HEIGHT } from "./campus/shared";
import { Box, Cyl, mat } from "./parts";

const TONE_HEX: Record<Tone, string> = {
  ok: color.ok, info: color.info, warn: color.warn, crit: color.crit, idle: color.idle, live: color.live,
};
const ringGeo = new THREE.RingGeometry(0.62, 0.8, 32).rotateX(-Math.PI / 2);
const selGeo = new THREE.RingGeometry(1.05, 1.2, 40).rotateX(-Math.PI / 2);
const ringMats = new Map<string, THREE.MeshBasicMaterial>();
function ringMat(hex: string): THREE.MeshBasicMaterial {
  let m = ringMats.get(hex);
  if (!m) {
    m = new THREE.MeshBasicMaterial({ color: hex, depthWrite: false });
    ringMats.set(hex, m);
  }
  return m;
}

function Puck({ d, selected }: { d: Device; selected: boolean }) {
  const g = useRef<THREE.Group>(null);
  const goal = useMemo(() => new THREE.Vector3(), []);
  // Badges move: ease towards the latest reported position instead of jumping once a second.
  useFrame((_, dt) => {
    if (!g.current) return;
    goal.set(d.x, 0, d.z);
    g.current.position.lerp(goal, 1 - Math.exp(-4 * dt));
  });
  const tone = TONE_HEX[deviceTone(d)];
  const mount = d.type === "badge" ? 0 : (MOUNT_HEIGHT[d.type] ?? 0);
  return (
    <group ref={g} position={[d.x, 0, d.z]} {...pickHandlers(d.id)}>
      <mesh geometry={ringGeo} position={[0, 0.06, 0]} material={ringMat(tone)} />
      {selected && <mesh geometry={selGeo} position={[0, 0.07, 0]} material={ringMat(color.accent)} />}
      {/* The marker stands where the real kit is mounted (wall, ceiling, tank top), with a thin stem down to its floor ring. */}
      {mount > 0.3 && <Box size={[0.04, mount, 0.04]} at={[0, 0.06, 0]} color="#BDBDBD" shadow={false} />}
      <Cyl size={[0.5, 0.22, 0.5]} at={[0, 0.06 + mount, 0]} color="#FFFFFF" shadow={false} />
      <Cyl size={[0.2, 0.04, 0.2]} at={[0, 0.28 + mount, 0]} shadow={false} material={mat(d.status === "online" ? tone : color.idle)} />
    </group>
  );
}

export function DevicePucks() {
  const show = useView((s) => s.showDevices);
  const devices = useWorld(useShallow((s) => Object.values(s.devices).filter((d) => d.type !== "gateway")));
  const selected = useWorld((s) => s.selected);
  if (!show) return null;
  return <group>{devices.map((d) => <Puck key={d.id} d={d} selected={selected === d.id} />)}</group>;
}
