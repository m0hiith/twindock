import { Stats } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useEffect } from "react";
import * as THREE from "three";
import { send } from "../store/ws";
import { useWorld } from "../store/world";
import { CameraRig } from "./CameraRig";
import { dragState } from "./dragState";
import { GatewayPole } from "./GatewayPole";
import { Lights } from "./Lights";
import { Pallets } from "./Pallets";
import { SelectionOverlay } from "./Selection";
import { Baked } from "./Baked";
import { Chargers, Containers, FenceStatic, GateBarrier, Ground, GroundLabels, Markings, Racks, Roads, Trees } from "./Site";
import { StaticHitAreas, Units } from "./Units";
import { Office, Warehouse } from "./Warehouse";
import { Factory } from "./Factory";
import { DevicePucks } from "./DevicePucks";

function DrawCalls() {
  // Exposes renderer stats for the perf check (?stats): window.__twindockGl.
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    const w = window as unknown as { __twindockGl: unknown; __twindockScene: unknown };
    w.__twindockGl = gl.info;
    w.__twindockScene = scene;
  }, [gl, scene]);
  return null;
}

const showStats = new URLSearchParams(location.search).has("stats");

export function Scene() {
  const layout = useWorld((s) => s.layout);
  const selected = useWorld((s) => s.selected);
  if (!layout) return null;
  return (
    <Canvas orthographic flat dpr={[1, 2]} shadows={{ type: THREE.PCFShadowMap }}
      camera={{ position: [100, 100, 100], zoom: 10, near: 1, far: 600 }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      onPointerMissed={() => { if (!dragState.moved && selected) send({ type: "select_unit", unit_id: null }); }}
      style={{ position: "absolute", inset: 0 }}>
      <color attach="background" args={["#EDEDED"]} />
      <CameraRig layout={layout} />
      <Lights layout={layout} />
      <Ground layout={layout} />
      <Baked>
        <Roads layout={layout} />
        <Markings layout={layout} />
        <FenceStatic layout={layout} />
        <Trees layout={layout} />
        <Containers layout={layout} />
        <Racks layout={layout} />
        <Office layout={layout} />
      </Baked>
      <Warehouse layout={layout} />
      <Factory layout={layout} />
      <GroundLabels layout={layout} />
      <Chargers layout={layout} />
      <GateBarrier layout={layout} />
      <GatewayPole layout={layout} />
      <StaticHitAreas />
      <Units />
      <DevicePucks />
      <Pallets />
      <SelectionOverlay />
      {showStats && <><Stats /><DrawCalls /></>}
    </Canvas>
  );
}
