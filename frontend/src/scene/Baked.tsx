// Merges static children into one mesh per material (and shadow flags), cutting draw calls for
// the many small static parts (fence posts, ribs, trees, racks). Children render once, hidden,
// so their transforms can be baked; animated or interactive parts must stay outside.
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { color } from "../theme";
import { OutlineContext } from "./parts";
import * as THREE from "three";
import { mergeGeometries, mergeVertices } from "three/examples/jsm/utils/BufferGeometryUtils.js";

// Hover outline as an inverted hull: back faces pushed out along smoothed normals by a fixed
// world thickness. (drei <Outlines> does not render with our orthographic camera.)
const OUTLINE_M = 0.05;
const hullMat = new THREE.MeshBasicMaterial({ color: color.info, side: THREE.BackSide });
hullMat.onBeforeCompile = (shader) => {
  shader.vertexShader = shader.vertexShader.replace("#include <begin_vertex>",
    `#include <begin_vertex>
    transformed += normalize(normal) * ${OUTLINE_M.toFixed(3)};`);
};

function hullGeometry(g: THREE.BufferGeometry): THREE.BufferGeometry {
  const h = new THREE.BufferGeometry();
  h.setAttribute("position", g.getAttribute("position"));
  const merged = mergeVertices(h, 1e-4); // shared corners -> smooth normals -> closed shell
  merged.computeVertexNormals();
  return merged;
}

interface Batch { geometry: THREE.BufferGeometry; hull: THREE.BufferGeometry | null; material: THREE.Material; cast: boolean; receive: boolean }

/** `outline`: undefined = never outlined (static scenery); boolean = hover state of an interactive model. */
export function Baked({ children, outline }: { children: ReactNode; outline?: boolean }) {
  const outlinable = outline !== undefined;
  const src = useRef<THREE.Group>(null);
  const [batches, setBatches] = useState<Batch[] | null>(null);
  useLayoutEffect(() => {
    const root = src.current;
    if (!root) return;
    root.updateMatrixWorld(true);
    const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
    const groups = new Map<string, { material: THREE.Material; cast: boolean; receive: boolean; geos: THREE.BufferGeometry[] }>();
    root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh || Array.isArray(m.material)) return;
      const key = `${m.material.uuid}|${m.castShadow}|${m.receiveShadow}`;
      let g = groups.get(key);
      if (!g) groups.set(key, (g = { material: m.material, cast: m.castShadow, receive: m.receiveShadow, geos: [] }));
      const geo = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
      for (const name of Object.keys(geo.attributes)) if (!["position", "normal", "uv"].includes(name)) geo.deleteAttribute(name);
      geo.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, m.matrixWorld));
      g.geos.push(geo);
    });
    const out: Batch[] = [];
    for (const g of groups.values()) {
      const merged = mergeGeometries(g.geos, false);
      g.geos.forEach((x) => x.dispose());
      if (merged) out.push({ geometry: merged, hull: outlinable ? hullGeometry(merged) : null, material: g.material, cast: g.cast, receive: g.receive });
    }
    setBatches(out);
    return () => out.forEach((b) => { b.geometry.dispose(); b.hull?.dispose(); });
  }, [outlinable]);
  return (
    <>
      {!batches && (
        <group ref={src} visible={false}>
          {/* no hover outlines while baking; the merged meshes get their own */}
          <OutlineContext.Provider value={false}>{children}</OutlineContext.Provider>
        </group>
      )}
      {batches?.map((b, i) => (
        <group key={i}>
          <mesh geometry={b.geometry} material={b.material} castShadow={b.cast} receiveShadow={b.receive} />
          {/* hover outline: inverted hull, a slightly larger back-face copy (works with the ortho camera) */}
          {outline && b.hull && <mesh geometry={b.hull} material={hullMat} />}
        </group>
      ))}
    </>
  );
}
