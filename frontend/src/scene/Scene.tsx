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
import { ProductionLine } from "./ProductionLine";
import { Workers } from "./Workers";
import { AlertPulses } from "./AlertPulses";

function DrawCalls() {
  // Perf check hooks (?stats only): renderer stats, plus advance() to step whole frames (every
  // useFrame callback + render) by hand, so frame cost can be measured even when the window is
  // hidden and requestAnimationFrame is throttled. See RUN_REPORT.md.
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const advance = useThree((s) => s.advance);
  useEffect(() => {
    const w = window as unknown as { __twindockGl: unknown; __twindockScene: unknown; __twindockBench: unknown };
    w.__twindockGl = gl.info;
    w.__twindockScene = scene;
    w.__twindockBench = (frames: number): { avgMs: number; p95Ms: number; maxMs: number } => {
      const ctx = gl.getContext();
      const px = new Uint8Array(4);
      const times: number[] = [];
      for (let i = 0; i < frames; i++) {
        const t0 = performance.now();
        advance(t0);
        ctx.readPixels(0, 0, 1, 1, ctx.RGBA, ctx.UNSIGNED_BYTE, px); // waits for the GPU to finish the frame
        times.push(performance.now() - t0);
      }
      times.sort((a, b) => a - b);
      const avg = times.reduce((a, b) => a + b, 0) / frames;
      return { avgMs: Math.round(avg * 100) / 100, p95Ms: Math.round(times[Math.floor(frames * 0.95)]! * 100) / 100,
        maxMs: Math.round(times.at(-1)! * 100) / 100 };
    };
  }, [gl, scene, advance]);
  return null;
}

const showStats = new URLSearchParams(location.search).has("stats");

export function Scene({ alertPulses = false }: { alertPulses?: boolean }) {
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
      <ProductionLine layout={layout} />
      <GroundLabels layout={layout} />
      <Chargers layout={layout} />
      <GateBarrier layout={layout} />
      <GatewayPole layout={layout} />
      <StaticHitAreas />
      <Units />
      <DevicePucks />
      <Workers />
      <Pallets />
      <SelectionOverlay />
      {alertPulses && <AlertPulses />}
      {showStats && <><Stats /><DrawCalls /></>}
    </Canvas>
  );
}
