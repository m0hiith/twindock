// One directional light with soft shadows plus hemisphere fill (CLAUDE.md). The shadow camera
// covers the whole site, so shadows stay put while panning.
import { useEffect, useRef } from "react";
import type * as THREE from "three";
import type { Layout } from "../layout";

export function Lights({ layout }: { layout: Layout }) {
  const sun = useRef<THREE.DirectionalLight>(null);
  const cx = (layout.bounds.x[0] + layout.bounds.x[1]) / 2;
  const cz = (layout.bounds.z[0] + layout.bounds.z[1]) / 2;
  useEffect(() => {
    const l = sun.current;
    if (!l) return;
    l.target.position.set(cx, 0, cz);
    l.target.updateMatrixWorld();
    const cam = l.shadow.camera;
    cam.left = -62; cam.right = 62; cam.top = 62; cam.bottom = -62; cam.near = 1; cam.far = 260;
    cam.updateProjectionMatrix();
  }, [cx, cz]);
  return (
    <>
      <hemisphereLight args={["#FFFFFF", "#C8D2EA", 1.25]} />
      <directionalLight ref={sun} position={[cx - 45, 90, cz - 30]} intensity={1.9} castShadow
        shadow-mapSize={[2048, 2048]} shadow-bias={-0.0004} shadow-normalBias={0.04} shadow-radius={4} />
    </>
  );
}
