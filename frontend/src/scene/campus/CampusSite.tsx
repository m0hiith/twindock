// Campus ground furniture (F2): walkways with marked crossings, green belt, perimeter fence, hydrants, muster points.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { Layout, XZ } from "../../layout";
import { color } from "../../theme";
import { Baked } from "../Baked";
import { Box, Cyl, Decal, Label } from "../parts";
import { palette } from "./shared";

const WALK = "#D6D6D2";

function Seg({ a, b, w, c, y }: { a: XZ; b: XZ; w: number; c: string; y: number }) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  return <Decal x={(a[0] + b[0]) / 2} z={(a[1] + b[1]) / 2} w={Math.hypot(dx, dz)} d={w} c={c} y={y} rot={-Math.atan2(dz, dx)} />;
}

export function Walkways({ layout }: { layout: Layout }) {
  const c = layout.campus;
  if (!c) return null;
  const nodes = new Map(layout.nodes.map((n) => [n.id, n]));
  return (
    <Baked>
      {c.walkways.flatMap((w) => w.points.slice(1).map((p, i) => {
        const a = w.points[i]!;
        return <Seg key={`${w.id}${i}`} a={a} b={p} w={w.width} c={WALK} y={0.014} />;
      }))}
      {c.crossings.map((x) => {
        const a = nodes.get(x.a), b = nodes.get(x.b);
        if (!a || !b) return null;
        const len = Math.hypot(b.x - a.x, b.z - a.z);
        const n = Math.floor(len / 0.9);
        const rot = -Math.atan2(b.z - a.z, b.x - a.x);
        return (
          <group key={x.id}>
            {Array.from({ length: n }, (_, k) => {
              const t = (k + 0.5) / n;
              // zebra stripes across the road: short bars along the crossing direction, spaced across its width
              return [-1.2, 0, 1.2].map((o) => (
                <Decal key={`${k}${o}`} x={a.x + (b.x - a.x) * t + Math.sin(rot) * o} z={a.z + (b.z - a.z) * t + Math.cos(rot) * o} w={0.45} d={0.5} c="#FFFFFF" y={0.02} rot={rot} />
              ));
            })}
          </group>
        );
      })}
    </Baked>
  );
}

export function GreenBelt({ layout }: { layout: Layout }) {
  const c = layout.campus;
  if (!c) return null;
  return <Baked>{c.green_belt.map((g, i) => <Decal key={i} x={g.x + g.w / 2} z={g.z + g.d / 2} w={g.w} d={g.d} c={palette.grass} y={0.01} />)}</Baked>;
}

export function PerimeterFence({ layout }: { layout: Layout }) {
  const c = layout.campus;
  if (!c) return null;
  const parts: React.ReactNode[] = [];
  c.fence.lines.forEach((line, li) => {
    for (let i = 1; i < line.length; i++) {
      const a = line[i - 1], b = line[i];
      if (!a || !b || a.length === 0 || b.length === 0) continue;
      const dx = b[0]! - a[0]!, dz = b[1]! - a[1]!;
      const len = Math.hypot(dx, dz);
      const n = Math.max(1, Math.floor(len / 6));
      for (let k = 0; k <= n; k++) parts.push(<Box key={`p${li}${i}${k}`} size={[0.12, 1.6, 0.12]} at={[a[0]! + (dx * k) / n, 0, a[1]! + (dz * k) / n]} color="#BDBDBD" shadow={false} />);
      parts.push(<Box key={`r${li}${i}`} size={[len, 0.07, 0.07]} at={[(a[0]! + b[0]!) / 2, 1.35, (a[1]! + b[1]!) / 2]} rot={[0, -Math.atan2(dz, dx), 0]} color="#CFCFCF" shadow={false} />);
      parts.push(<Box key={`m${li}${i}`} size={[len, 0.06, 0.06]} at={[(a[0]! + b[0]!) / 2, 0.7, (a[1]! + b[1]!) / 2]} rot={[0, -Math.atan2(dz, dx), 0]} color="#CFCFCF" shadow={false} />);
    }
  });
  return <Baked>{parts}</Baked>;
}

const hydrantRed = palette.fireRed;
export function Hydrants({ layout }: { layout: Layout }) {
  const c = layout.campus;
  if (!c) return null;
  return (
    <Baked>
      {/* the ring main, a thin red line under the grass */}
      {c.hydrants.ring.map((p, i) => {
        const q = c.hydrants.ring[(i + 1) % c.hydrants.ring.length]!;
        return <Seg key={i} a={p} b={q} w={0.2} c={hydrantRed} y={0.012} />;
      })}
      {c.hydrants.points.map(([x, z], i) => (
        <group key={i}>
          <Cyl size={[0.34, 0.7, 0.34]} at={[x, 0.35, z]} color={hydrantRed} shadow={false} />
          <Cyl size={[0.44, 0.1, 0.44]} at={[x, 0.7, z]} color={hydrantRed} shadow={false} />
          <Box size={[0.5, 0.16, 0.16]} at={[x, 0.45, z]} color="#F4F4F2" shadow={false} />
        </group>
      ))}
    </Baked>
  );
}

const greenMat = new THREE.MeshBasicMaterial({ color: palette.green, transparent: true, opacity: 0.35, depthWrite: false });
export function MusterPoints({ layout }: { layout: Layout }) {
  const c = layout.campus;
  if (!c) return null;
  return (
    <group>
      {c.muster_points.map((m) => (
        <group key={m.id} position={[m.x, 0, m.z]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.03, 0]} material={greenMat}><circleGeometry args={[m.radius_m, 40]} /></mesh>
          <Cyl size={[0.12, 2.6, 0.12]} at={[0, 1.3, 0]} color={palette.steel} />
          <Box size={[1.5, 1.5, 0.1]} at={[0, 2.6, 0]} color={palette.green} />
          <Label text={m.id} at={[0, 3.35, 0.07]} width={1.35} color="#FFFFFF" bg={palette.green} weight={800} />
          <Label text="Muster point" at={[0, 0.05, 0]} width={5} flat color={palette.green} weight={800} />
        </group>
      ))}
    </group>
  );
}

const pulse = new THREE.MeshBasicMaterial({ color: color.warn, transparent: true, opacity: 0.35, depthWrite: false });
/** Crossing hotspots: a faint amber disc where walkers and vehicles meet (proximity warnings are most likely there). */
export function Hotspots({ layout }: { layout: Layout }) {
  const c = layout.campus;
  const ref = useRef<THREE.Group>(null);
  useFrame(({ clock }) => { if (ref.current) ref.current.scale.setScalar(1 + 0.06 * Math.sin(clock.elapsedTime * 2)); });
  if (!c) return null;
  return (
    <group>
      {c.crossings.map((x) => (
        <mesh key={x.id} rotation={[-Math.PI / 2, 0, 0]} position={[x.hotspot.x, 0.025, x.hotspot.z]} material={pulse}>
          <circleGeometry args={[x.hotspot.radius_m * 0.6, 32]} />
        </mesh>
      ))}
      <group ref={ref} />
    </group>
  );
}

