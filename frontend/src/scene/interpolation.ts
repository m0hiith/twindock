// Smooths units between 20 Hz server updates. Units only ever move towards the latest server
// position (critically damped, no extrapolation), so nothing moves without a server update.
import { useFrame } from "@react-three/fiber";
import type { RefObject } from "react";
import type * as THREE from "three";
import { useWorld } from "../store/world";
import { headingToRotY } from "./parts";

export interface Pose { x: number; z: number; h: number }

/** Latest displayed pose per unit, shared so attached things (carried pallets) follow the model. */
export const displayed = new Map<string, Pose>();

/** Displayed fork height per forklift (written by ForkliftModel, read by Pallets). */
export const forkHeight = new Map<string, number>();

const RATE = 14; // 1/s. ~70 ms lag: smooth at 60 fps, visually locked to 20 Hz updates
const SNAP_M = 6; // bigger jumps (reset, truck returning on site) snap instead of sliding

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

export function step(p: Pose, tx: number, tz: number, th: number, dt: number): Pose {
  if (Math.hypot(tx - p.x, tz - p.z) > SNAP_M) return { x: tx, z: tz, h: th };
  const k = 1 - Math.exp(-RATE * dt);
  return { x: p.x + (tx - p.x) * k, z: p.z + (tz - p.z) * k, h: p.h + wrap(th - p.h) * k };
}

/** Drive a group's transform from the unit's server pose. */
export function useInterpolatedPose(id: string, ref: RefObject<THREE.Group | null>): void {
  useFrame((_, dt) => {
    const u = useWorld.getState().units[id];
    const g = ref.current;
    if (!u || !g) return;
    const prev = displayed.get(id) ?? { x: u.x, z: u.z, h: u.heading_rad };
    const p = step(prev, u.x, u.z, u.heading_rad, Math.min(dt, 0.1));
    displayed.set(id, p);
    g.position.set(p.x, 0, p.z);
    g.rotation.y = headingToRotY(p.h);
  });
}
