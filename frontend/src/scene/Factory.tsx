// FAC-01 "Riverside Assembly": the factory hall and its cold room, in the same cutaway style as
// the warehouse (walls facing the camera drop to a kerb). The production line itself
// (conveyor, machines, QC) is drawn by ProductionLine.tsx.
import { useMemo } from "react";
import * as THREE from "three";
import type { Layout } from "../layout";
import { color, model } from "../theme";
import { Box, Decal, Label } from "./parts";
import { Wall, wallSegs } from "./Warehouse";

const T = 0.3;
const panel = new THREE.MeshStandardMaterial({ color: model.trailer, roughness: 0.6 }); // insulated white panels

type Building = Layout["buildings"][number];

function Shell({ b, tall, material }: { b: Building; tall: number; material?: THREE.Material }) {
  const gaps = (wall: string) => [...(b.openings ?? []), ...(b.door ? [b.door] : [])].filter((o) => o.wall === wall);
  const { x, z, w, d } = b;
  return (
    <group>
      <Wall along="x" fixed={z} segs={wallSegs(x - T / 2, x + w + T / 2, gaps("north"))} normal={[0, -1]} material={material} tall={tall} />
      <Wall along="x" fixed={z + d} segs={wallSegs(x - T / 2, x + w + T / 2, gaps("south"))} normal={[0, 1]} material={material} tall={tall} />
      <Wall along="z" fixed={x} segs={wallSegs(z, z + d, gaps("west"))} normal={[-1, 0]} material={material} tall={tall} />
      <Wall along="z" fixed={x + w} segs={wallSegs(z, z + d, gaps("east"))} normal={[1, 0]} material={material} tall={tall} />
    </group>
  );
}

export function Factory({ layout }: { layout: Layout }) {
  const hall = layout.buildings.find((b) => b.kind === "factory");
  const cold = layout.buildings.find((b) => b.kind === "cold_room");
  const aisle = useMemo(() => {
    // Yellow walkway lines along the forklift aisle (z = 14) and the link to the west door.
    if (!hall) return [];
    return [
      { x: hall.x + hall.w / 2 - 6, z: 12.6, w: hall.w - 14, d: 0.12 },
      { x: hall.x + hall.w / 2 - 6, z: 16.6, w: hall.w - 14, d: 0.12 },
    ];
  }, [hall]);
  if (!hall) return null;
  return (
    <group>
      <Decal x={hall.x + hall.w / 2} z={hall.z + hall.d / 2} w={hall.w} d={hall.d} c={model.floor} y={0.012} />
      {aisle.map((l, i) => <Decal key={i} x={l.x} z={l.z} w={l.w} d={l.d} c={color.marking} y={0.03} />)}
      <Shell b={hall} tall={6.2} />
      {hall.label && (
        <Label text={hall.label} at={[hall.x + hall.w / 2, 0.04, hall.z - 2.2]} width={16} flat color={color.structure} weight={800} />
      )}
      {cold && (
        <group>
          <Decal x={cold.x + cold.w / 2} z={cold.z + cold.d / 2} w={cold.w} d={cold.d} c="#F7F7F7" y={0.02} />
          <Shell b={cold} tall={cold.h} material={panel} />
          {cold.door && (
            // Insulated sliding door, drawn open beside its opening (the twin shows the door
            // sensor's state as a ring on the device marker, not by moving this panel).
            <Box size={[T + 0.1, 2.6, cold.door.w]} at={[cold.x - 0.2, 0, cold.door.at + cold.door.w + 0.1]} color={model.doorSlat} />
          )}
          <Label text="Cold room" at={[cold.x + cold.w / 2, 0.04, cold.z + cold.d / 2]} width={5.5} flat color={color.ink2} weight={700} />
        </group>
      )}
    </group>
  );
}
