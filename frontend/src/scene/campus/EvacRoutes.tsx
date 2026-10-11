// Walking routes to the nearest muster point (F3): drawn while an evacuation runs or a gas alarm is on. Advice only:
// they follow the walkways and avoid musters next to the hazard. Zone-level (one per zone with people), so nobody is singled out.
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { useWorld } from "../../store/world";
import { palette } from "./shared";

const mat = new THREE.LineDashedMaterial({ color: palette.green, dashSize: 1.2, gapSize: 0.8, linewidth: 2 });
const arrow = new THREE.MeshBasicMaterial({ color: palette.green });

function Route({ points }: { points: [number, number][] }) {
  const line = useMemo(() => {
    const g = new THREE.BufferGeometry().setFromPoints(points.map(([x, z]) => new THREE.Vector3(x, 0.2, z)));
    const l = new THREE.Line(g, mat);
    l.computeLineDistances();
    return l;
  }, [points]);
  const dot = useRef<THREE.Mesh>(null);
  const total = useMemo(() => points.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - points[i]![0], p[1] - points[i]![1]), 0), [points]);
  useFrame(({ clock }) => {
    if (!dot.current || total === 0) return;
    let d = ((clock.elapsedTime * 6) % total);
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1]!, b = points[i]!;
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (d <= len) { const t = len ? d / len : 0; dot.current.position.set(a[0] + (b[0] - a[0]) * t, 0.5, a[1] + (b[1] - a[1]) * t); return; }
      d -= len;
    }
  });
  return (
    <group>
      <primitive object={line} />
      <mesh ref={dot} material={arrow}><sphereGeometry args={[0.45, 10, 8]} /></mesh>
    </group>
  );
}

export function EvacRoutes() {
  const routes = useWorld((s) => s.safety?.routes);
  if (!routes?.length) return null;
  return <group>{routes.map((r) => <Route key={r.zone_id} points={r.points as [number, number][]} />)}</group>;
}
