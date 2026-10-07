// All pallets in two instanced meshes (bases + cardboard boxes), per CLAUDE.md's instancing rule.
// Stored pallets use the server position; carried pallets ride on their forklift's displayed pose
// and fork height so they stay glued to the forks; pallets loaded on a truck are hidden inside it.
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { color } from "../theme";
import { FORK_BASE_Y } from "./Forklift";
import { displayed, forkHeight, step, type Pose } from "./interpolation";
import { dragState } from "./dragState";
import { mat, unitBox } from "./parts";

const MAX = 64;
const BOXES = 8; // 2 x 2 x 2 cartons per pallet
const FORK_OFFSET_M = 1.1; // same as the backend: pallet centre ahead of the forklift centre


const tmp = new THREE.Object3D();
const hidden = new THREE.Matrix4().makeScale(0, 0, 0);

export function Pallets() {
  const bases = useRef<THREE.InstancedMesh>(null);
  const boxes = useRef<THREE.InstancedMesh>(null);
  const ids = useRef<string[]>([]);
  const poses = useRef(new Map<string, Pose>());

  const boxMat = useMemo(() => new THREE.MeshStandardMaterial({ roughness: 0.9 }), []);
  useLayoutEffect(() => {
    const m = boxes.current;
    if (!m) return;
    const c = new THREE.Color();
    for (let i = 0; i < MAX * BOXES; i++) m.setColorAt(i, c.set((i * 7 + (i >> 3)) % 3 === 0 ? color.boxDark : color.box));
    m.instanceColor!.needsUpdate = true;
  }, []);

  useFrame((_, dt) => {
    const b = bases.current, x = boxes.current;
    if (!b || !x) return;
    const units = useWorld.getState().units;
    const list = Object.values(units).filter((u) => u.kind === "pallet");
    ids.current = list.map((u) => u.id);
    for (let i = 0; i < MAX; i++) {
      const p = list[i];
      const holder = p?.holder ? units[p.holder] : undefined;
      if (!p || (holder && holder.kind === "truck")) {
        b.setMatrixAt(i, hidden);
        for (let k = 0; k < BOXES; k++) x.setMatrixAt(i * BOXES + k, hidden);
        continue;
      }
      let pose: Pose, y = 0;
      const fl = holder ? displayed.get(holder.id) : undefined;
      if (holder && fl) {
        pose = { x: fl.x + Math.cos(fl.h) * FORK_OFFSET_M, z: fl.z + Math.sin(fl.h) * FORK_OFFSET_M, h: fl.h };
        y = FORK_BASE_Y + (forkHeight.get(holder.id) ?? 0.3) - 0.025;
      } else {
        const prev = poses.current.get(p.id) ?? { x: p.x, z: p.z, h: p.heading_rad };
        pose = step(prev, p.x, p.z, p.heading_rad, Math.min(dt, 0.1));
      }
      poses.current.set(p.id, pose);
      tmp.position.set(pose.x, y + 0.07, pose.z);
      tmp.rotation.set(0, -pose.h, 0);
      tmp.scale.set(1.0, 0.14, 1.2);
      tmp.updateMatrix();
      b.setMatrixAt(i, tmp.matrix);
      for (let k = 0; k < BOXES; k++) {
        const lx = (k & 1 ? 0.24 : -0.24), lz = (k & 2 ? 0.29 : -0.29), layer = k >> 2;
        const c = Math.cos(-pose.h), s = Math.sin(-pose.h);
        tmp.position.set(pose.x + lx * c + lz * s, y + 0.14 + 0.21 + layer * 0.43, pose.z - lx * s + lz * c);
        tmp.scale.set(0.46, 0.42, 0.56);
        tmp.updateMatrix();
        x.setMatrixAt(i * BOXES + k, tmp.matrix);
      }
    }
    b.instanceMatrix.needsUpdate = true;
    x.instanceMatrix.needsUpdate = true;
    b.computeBoundingSphere();
    x.computeBoundingSphere();
  });

  const idAt = (e: ThreeEvent<PointerEvent | MouseEvent>, perPallet: number) =>
    e.instanceId === undefined ? undefined : ids.current[Math.floor(e.instanceId / perPallet)];
  const handlers = (perPallet: number) => ({
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      useView.getState().setHovered(idAt(e, perPallet) ?? null);
      document.body.style.cursor = "pointer";
    },
    onPointerOut: () => {
      useView.getState().setHovered(null);
      document.body.style.cursor = "";
    },
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      const id = idAt(e, perPallet);
      if (id && !dragState.moved) send({ type: "select_unit", unit_id: id });
    },
  });

  return (
    <>
      <instancedMesh ref={bases} args={[unitBox, mat(color.pallet), MAX]} castShadow receiveShadow frustumCulled={false} {...handlers(1)} />
      <instancedMesh ref={boxes} args={[unitBox, boxMat, MAX * BOXES]} castShadow receiveShadow frustumCulled={false} {...handlers(BOXES)} />
    </>
  );
}
