// Open alerts pulse on the 3D map where they happened (monitoring centre). Critical red, warning amber;
// acknowledged alerts stop pulsing and stay as a steady ring until they resolve.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import { useShallow } from "zustand/react/shallow";
import { useWorld } from "../store/world";
import { color } from "../theme";

const geo = new THREE.RingGeometry(1.0, 1.3, 48).rotateX(-Math.PI / 2);
const mats = {
  critical: new THREE.MeshBasicMaterial({ color: color.crit, transparent: true, opacity: 0.85, depthWrite: false }),
  warning: new THREE.MeshBasicMaterial({ color: color.warn, transparent: true, opacity: 0.8, depthWrite: false }),
  info: new THREE.MeshBasicMaterial({ color: color.idle, transparent: true, opacity: 0.6, depthWrite: false }),
};

function Ring({ x, z, severity, steady }: { x: number; z: number; severity: keyof typeof mats; steady: boolean }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    const m = ref.current;
    if (!m) return;
    const base = severity === "critical" ? 2.4 : 1.8;
    const k = steady ? base : base * (1 + 0.35 * Math.abs(Math.sin(clock.elapsedTime * (severity === "critical" ? 3 : 1.8))));
    m.scale.set(k, 1, k);
  });
  return <mesh ref={ref} geometry={geo} material={mats[severity]} position={[x, 0.12, z]} />;
}

export function AlertPulses() {
  const rings = useWorld(useShallow((s) => (s.alerts?.alerts ?? [])
    .filter((a) => a.state !== "resolved" && a.target.x !== undefined && a.target.z !== undefined)
    .map((a) => `${a.id}|${a.target.x}|${a.target.z}|${a.severity}|${a.state}`)));
  return (
    <>
      {rings.map((r) => {
        const [id, x, z, sev, state] = r.split("|");
        return <Ring key={id} x={Number(x)} z={Number(z)} severity={sev as keyof typeof mats} steady={state === "acknowledged"} />;
      })}
    </>
  );
}
