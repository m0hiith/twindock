// Moving and stateful units. Each subscribes only to the fields that change its look; position is
// read per frame (useInterpolatedPose), so 20 Hz updates don't re-render React.
import type { ThreeEvent } from "@react-three/fiber";
import { useRef, type ReactNode } from "react";
import type * as THREE from "three";
import { useShallow } from "zustand/react/shallow";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { BoxTruckModel } from "./BoxTruck";
import { dragState } from "./dragState";
import { ForkliftModel } from "./Forklift";
import { useInterpolatedPose } from "./interpolation";
import { OutlineContext } from "./parts";

export function pickHandlers(id: string) {
  return {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      useView.getState().setHovered(id);
      document.body.style.cursor = "pointer";
    },
    onPointerOut: () => {
      if (useView.getState().hovered === id) useView.getState().setHovered(null);
      document.body.style.cursor = "";
    },
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      if (!dragState.moved) send({ type: "select_unit", unit_id: id });
    },
  };
}

function Mover({ id, children }: { id: string; children: (hovered: boolean) => ReactNode }) {
  const ref = useRef<THREE.Group>(null);
  useInterpolatedPose(id, ref);
  const hovered = useView((s) => s.hovered === id);
  return (
    <group ref={ref} {...pickHandlers(id)}>
      <OutlineContext.Provider value={hovered}>{children(hovered)}</OutlineContext.Provider>
    </group>
  );
}

function Forklift({ id }: { id: string }) {
  const [state, carrying] = useWorld(useShallow((s) => [s.units[id]?.state, Boolean(s.units[id]?.carrying)]));
  const beacon = useWorld((s) => s.units[id]?.meta?.pedestrian_warning === true);
  return <Mover id={id}>{(h) => <ForkliftModel id={id} state={state} carrying={carrying} hovered={h} beacon={beacon} />}</Mover>;
}

function Truck({ id }: { id: string }) {
  const gone = useWorld((s) => s.units[id]?.state === "gone");
  if (gone) return null; // off site
  return <Mover id={id}>{(h) => <BoxTruckModel hovered={h} />}</Mover>;
}

export function Units() {
  const ids = useWorld(useShallow((s) => Object.values(s.units).filter((u) => u.kind === "forklift" || u.kind === "truck").map((u) => `${u.kind}:${u.id}`)));
  return (
    <group>
      {ids.map((k) => {
        const [kind, id] = k.split(":") as [string, string];
        return kind === "forklift" ? <Forklift key={id} id={id} /> : <Truck key={id} id={id} />;
      })}
    </group>
  );
}

/** Invisible hit boxes so static units (docks, racks, chargers, gateway) can be hovered and selected. */
export function StaticHitAreas() {
  const layout = useWorld((s) => s.layout);
  if (!layout) return null;
  const areas: { id: string; x: number; z: number; w: number; d: number; h: number; y0: number }[] = [
    ...layout.docks.map((d) => {
      const n = layout.nodes.find((q) => q.id === d.node)!;
      return { id: d.id, x: n.x, z: 28, w: 4.4, d: 1.2, h: 4, y0: 0 };
    }),
    ...layout.racks.map((r) => ({ id: r.id, x: r.x + r.w / 2, z: r.z + r.d / 2, w: r.w, d: r.d, h: 2.6, y0: 1.65 })),
    ...layout.chargers.map((c) => {
      const n = layout.nodes.find((q) => q.id === c.node)!;
      return { id: c.id, x: 0.45, z: n.z, w: 0.6, d: 0.8, h: 1.6, y0: 0 };
    }),
    { id: layout.gateway.id, x: layout.gateway.x, z: layout.gateway.z, w: 0.8, d: 0.8, h: 3.6, y0: 0 },
  ];
  return (
    <group>
      {areas.map((a) => (
        <mesh key={a.id} position={[a.x, a.y0 + a.h / 2, a.z]} {...pickHandlers(a.id)}>
          <boxGeometry args={[a.w, a.h, a.d]} />
          <meshBasicMaterial colorWrite={false} depthWrite={false} />
        </mesh>
      ))}
    </group>
  );
}
