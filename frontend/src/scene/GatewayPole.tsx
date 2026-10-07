// The SiWx917 gateway on its pole near the docks. Violet is reserved for device data: the ring is
// bright only while the board is actually online (status within 15 s), faint otherwise.
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { Layout } from "../layout";
import { useWorld } from "../store/world";
import { color, model } from "../theme";
import { Box, Cyl, mat } from "./parts";

const ringMat = new THREE.MeshBasicMaterial({ color: color.live, transparent: true, opacity: 0.5, depthWrite: false });
const discMat = new THREE.MeshBasicMaterial({ color: color.live, transparent: true, opacity: 0.05, depthWrite: false });

export function GatewayPole({ layout }: { layout: Layout }) {
  const g = layout.gateway;
  const online = useWorld((s) => s.gateway?.online ?? false);
  const ring = useRef<THREE.Mesh>(null);
  useFrame(() => {
    const target = online ? 0.32 : 0.1;
    ringMat.opacity += (target - ringMat.opacity) * 0.1;
    discMat.opacity += ((online ? 0.025 : 0.01) - discMat.opacity) * 0.1;
  });
  return (
    <group position={[g.x, 0, g.z]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.04, 0]} material={discMat}>
        <circleGeometry args={[g.ble_range_m, 64]} />
      </mesh>
      <mesh ref={ring} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.045, 0]} material={ringMat}>
        <ringGeometry args={[g.ble_range_m - 0.12, g.ble_range_m, 96]} />
      </mesh>
      <Cyl size={[0.6, 0.2, 0.6]} at={[0, 0.1, 0]} color={model.metal} />
      <Cyl size={[0.12, 3.4, 0.12]} at={[0, 1.8, 0]} color={model.pole} />
      <Box size={[0.42, 0.3, 0.16]} at={[0, 3.3, 0.1]} color="#FFFFFF" />
      <Box size={[0.08, 0.08, 0.02]} at={[0.12, 3.42, 0.19]} shadow={false}
        material={mat(online ? color.live : color.idle, online ? { emissive: color.live } : {})} />
    </group>
  );
}
