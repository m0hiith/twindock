// Site-twin device markers: small low-poly sensor pucks with a status ring. Hidden by default; the "Devices" map control shows
// them, and only when the camera is closer than the campus overview. GW-01 already has its pole (GatewayPole), so it gets no puck.
// Fixed devices are drawn as four instanced meshes (a draw call each) instead of ~4 meshes per device; badges move, so each
// of those is its own small group. Markers stand at their real mounting height on a thin stem over a floor ring.
import { useFrame } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useShallow } from "zustand/react/shallow";
import type { Device } from "../contract";
import { deviceTone, type Tone } from "../status";
import { useView, useWorld } from "../store/world";
import { color } from "../theme";
import { MOUNT_HEIGHT } from "./campus/shared";
import { pickHandlers } from "./Units";
import { Cyl, mat } from "./parts";

const TONE_HEX: Record<Tone, string> = {
  ok: color.ok, info: color.info, warn: color.warn, crit: color.crit, idle: color.idle, live: color.live,
};
const ringGeo = new THREE.RingGeometry(0.62, 0.8, 32).rotateX(-Math.PI / 2);
const selGeo = new THREE.RingGeometry(1.05, 1.2, 40).rotateX(-Math.PI / 2);
const puckGeo = new THREE.CylinderGeometry(0.5, 0.5, 1, 14);
const stemGeo = new THREE.BoxGeometry(1, 1, 1);
const ringMats = new Map<string, THREE.MeshBasicMaterial>();
function ringMat(hex: string): THREE.MeshBasicMaterial {
  let m = ringMats.get(hex);
  if (!m) {
    m = new THREE.MeshBasicMaterial({ color: hex, depthWrite: false });
    ringMats.set(hex, m);
  }
  return m;
}
const white = new THREE.MeshBasicMaterial({ color: "#FFFFFF" });
const baseMat = new THREE.MeshStandardMaterial({ color: "#FFFFFF", roughness: 0.85 });
const stemMat = new THREE.MeshStandardMaterial({ color: "#BDBDBD", roughness: 0.9 });
const tmpColor = new THREE.Color();

/** A badge: moves, so it keeps its own group and eases towards each reported position. */
function Puck({ d, selected }: { d: Device; selected: boolean }) {
  const g = useRef<THREE.Group>(null);
  const goal = useMemo(() => new THREE.Vector3(), []);
  useFrame((_, dt) => {
    if (!g.current) return;
    goal.set(d.x, 0, d.z);
    g.current.position.lerp(goal, 1 - Math.exp(-4 * dt));
  });
  const tone = TONE_HEX[deviceTone(d)];
  return (
    <group ref={g} position={[d.x, 0, d.z]} {...pickHandlers(d.id)}>
      <mesh geometry={ringGeo} position={[0, 0.06, 0]} material={ringMat(tone)} />
      {selected && <mesh geometry={selGeo} position={[0, 0.07, 0]} material={ringMat(color.accent)} />}
      <Cyl size={[0.5, 0.22, 0.5]} at={[0, 0.06, 0]} color="#FFFFFF" shadow={false} />
      <Cyl size={[0.2, 0.04, 0.2]} at={[0, 0.28, 0]} shadow={false} material={mat(d.status === "online" ? tone : color.idle)} />
    </group>
  );
}

/** Every fixed device in four instanced meshes. Instance ids map back to device ids for picking. */
function FixedMarkers({ devices, selected }: { devices: Device[]; selected: string | null }) {
  const rings = useRef<THREE.InstancedMesh>(null);
  const pucks = useRef<THREE.InstancedMesh>(null);
  const tops = useRef<THREE.InstancedMesh>(null);
  const stems = useRef<THREE.InstancedMesh>(null);
  const sel = useRef<THREE.Mesh>(null);
  const geomKey = devices.map((d) => `${d.id}@${d.x},${d.z}`).join("|"); // placement only depends on where devices are
  const ids = useMemo(() => devices.map((d) => d.id), [geomKey]); // eslint-disable-line react-hooks/exhaustive-deps
  // Static placement (devices don't move): only when the set of devices changes.
  useLayoutEffect(() => {
    const o = new THREE.Object3D();
    const put = (m: THREE.InstancedMesh | null, f: (d: Device, mount: number) => void) => {
      if (!m) return;
      devices.forEach((d, i) => { o.rotation.set(0, 0, 0); o.scale.set(1, 1, 1); f(d, MOUNT_HEIGHT[d.type] ?? 0); o.updateMatrix(); m.setMatrixAt(i, o.matrix); });
      m.instanceMatrix.needsUpdate = true;
    };
    put(rings.current, (d) => { o.position.set(d.x, 0.06, d.z); });
    put(pucks.current, (d, mt) => { o.position.set(d.x, 0.17 + mt, d.z); o.scale.set(0.5, 0.22, 0.5); });
    put(tops.current, (d, mt) => { o.position.set(d.x, 0.3 + mt, d.z); o.scale.set(0.2, 0.04, 0.2); });
    put(stems.current, (d, mt) => { if (mt > 0.3) { o.position.set(d.x, 0.06 + mt / 2, d.z); o.scale.set(0.04, mt, 0.04); } else o.scale.set(0, 0, 0); });
  }, [geomKey]); // eslint-disable-line react-hooks/exhaustive-deps
  // Colours follow the status (changes now and then, not every frame).
  const key = devices.map((d) => `${d.status}:${d.source}`).join("|");
  useEffect(() => {
    devices.forEach((d, i) => {
      const hex = TONE_HEX[deviceTone(d)];
      rings.current?.setColorAt(i, tmpColor.set(hex));
      tops.current?.setColorAt(i, tmpColor.set(d.status === "online" ? hex : color.idle));
    });
    if (rings.current?.instanceColor) rings.current.instanceColor.needsUpdate = true;
    if (tops.current?.instanceColor) tops.current.instanceColor.needsUpdate = true;
  }, [key, devices]);
  const d = devices.find((x) => x.id === selected);
  useEffect(() => { if (sel.current && d) sel.current.position.set(d.x, 0.07, d.z); }, [d]);
  const pick = (name: "onClick" | "onPointerOver" | "onPointerOut") => (e: { instanceId?: number } & Record<string, unknown>) => {
    const id = e.instanceId === undefined ? undefined : ids[e.instanceId];
    if (id) (pickHandlers(id)[name] as (e: unknown) => void)(e);
    else if (name === "onPointerOut") document.body.style.cursor = "";
  };
  const n = devices.length;
  if (n === 0) return null;
  return (
    <group>
      <instancedMesh ref={rings} args={[ringGeo, white, n]} frustumCulled={false} />
      <instancedMesh ref={pucks} args={[puckGeo, baseMat, n]} frustumCulled={false}
        onClick={pick("onClick") as never} onPointerOver={pick("onPointerOver") as never} onPointerOut={pick("onPointerOut") as never} />
      <instancedMesh ref={tops} args={[puckGeo, white, n]} frustumCulled={false} />
      <instancedMesh ref={stems} args={[stemGeo, stemMat, n]} frustumCulled={false} />
      {d && <mesh ref={sel} geometry={selGeo} material={ringMat(color.accent)} position={[d.x, 0.07, d.z]} />}
    </group>
  );
}

export function DevicePucks() {
  const show = useView((s) => s.showDevices);
  const far = useView((s) => s.lod === "far");
  const devices = useWorld(useShallow((s) => Object.values(s.devices).filter((d) => d.type !== "gateway")));
  const selected = useWorld((s) => s.selected);
  const fixed = useMemo(() => devices.filter((d) => d.type !== "badge"), [devices]);
  const badges = useMemo(() => devices.filter((d) => d.type === "badge"), [devices]);
  if (!show || far) return null; // devices only load when you are zoomed in
  return (
    <group>
      <FixedMarkers devices={fixed} selected={selected} />
      {badges.map((d) => <Puck key={d.id} d={d} selected={selected === d.id} />)}
    </group>
  );
}

