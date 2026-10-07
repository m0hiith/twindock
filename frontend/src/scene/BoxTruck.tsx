// Box truck, built facing +x. 10 m long (cab 2 m + box 7.8 m), matching the backend's bay geometry:
// the unit position is the truck centre, so a docked truck's rear sits at the dock door.
import { model } from "../theme";
import { Baked } from "./Baked";
import { Box, Cyl, Label, mat } from "./parts";
import { color } from "../theme";

const W = 2.5;

function Wheel({ x, z }: { x: number; z: number }) {
  return <Cyl size={[1.0, 0.36, 1.0]} at={[x, 0.5, z]} color={model.tyre} axis="z" />;
}

export function BoxTruckModel({ hovered = false }: { hovered?: boolean }) {
  return (
    <Baked outline={hovered}>
      <Box size={[9.8, 0.4, 2.2]} at={[0, 0.5, 0]} color={model.tyre} />
      {[3.9, -2.9, -4.0].flatMap((x) => [W / 2 - 0.2, -(W / 2 - 0.2)].map((z) => <Wheel key={`${x}${z}`} x={x} z={z} />))}
      {/* cab */}
      <Box size={[2.0, 2.3, W - 0.1]} at={[4.0, 0.75, 0]} color={color.structure} />
      <Box size={[0.9, 0.5, W - 0.1]} at={[4.55, 3.05, 0]} color={color.structureDark} />
      <Box size={[0.05, 0.85, W - 0.4]} at={[5.0, 1.85, 0]} color={model.cabGlass} />
      <Box size={[0.9, 0.7, 0.04]} at={[4.35, 1.95, W / 2 - 0.04]} color={model.cabGlass} />
      <Box size={[0.9, 0.7, 0.04]} at={[4.35, 1.95, -(W / 2 - 0.04)]} color={model.cabGlass} />
      <Box size={[0.12, 0.35, W - 0.2]} at={[5.04, 0.75, 0]} color={model.metal} />
      {/* box body */}
      <Box size={[7.8, 3.0, W]} at={[-1.05, 0.8, 0]} color={model.trailer} />
      <Box size={[7.82, 0.12, W + 0.02]} at={[-1.05, 3.8, 0]} color={model.trailerTrim} />
      <Box size={[7.82, 0.14, W + 0.02]} at={[-1.05, 0.8, 0]} color={model.trailerTrim} />
      <mesh position={[-4.96, 2.3, 0]} rotation={[0, -Math.PI / 2, 0]} material={mat(model.trailerTrim)}>
        <planeGeometry args={[W - 0.2, 2.8]} />
      </mesh>
      <Label text="TwinDock" at={[-1.05, 2.35, W / 2 + 0.01]} width={5.2} color={color.structure} weight={700} />
      <Label text="TwinDock" at={[-1.05, 2.35, -(W / 2 + 0.01)]} rotY={Math.PI} width={5.2} color={color.structure} weight={700} />
    </Baked>
  );
}
