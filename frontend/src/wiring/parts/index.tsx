// The part library: one drawing function per family, dispatched from a part's `drawing` in the kit JSON.
// Everything is drawn at true size (mm × px-per-mm), so relative sizes on the breadboard view are real.
import { Antenna, Button, Chip, Crystal, Led, Passive, Pcb } from "./board";
import { Connector } from "./connectors";
import { Buzzer, CoinCellHolder, CurrentClamp, DinMeter, Enclosure, LiPo, LoadCell, Magnet, PirDome, Probe, ReedSwitch, Relay, SensorWindow, TerminalBlock } from "./modules";
import { PX_PER_MM } from "./palette";
import type { DrawingFeature, Family, PartDrawing, Spec } from "./types";

export { PX_PER_MM };
export type { PartDrawing };

const FAMILIES: Record<Family, (s: Spec) => React.JSX.Element> = {
  pcb: Pcb, chip: Chip, connector: Connector, passive: Passive, crystal: Crystal, antenna: Antenna, led: Led, button: Button,
  coin_cell_holder: CoinCellHolder, lipo: LiPo, sensor_window: SensorWindow, relay: Relay, terminal_block: TerminalBlock,
  current_clamp: CurrentClamp, load_cell: LoadCell, reed_switch: ReedSwitch, pir_dome: PirDome, buzzer: Buzzer,
  magnet: Magnet, probe: Probe, din_meter: DinMeter, enclosure: Enclosure,
};

/** Every family the library can draw, for the gallery and its test. */
export const ALL_FAMILIES = Object.keys(FAMILIES) as Family[];

type Placeable = Pick<DrawingFeature, "family" | "variant" | "label" | "color"> & { w_mm: number; h_mm: number; rot?: 0 | 90 | 180 | 270 };

function Art({ f, s, pcb }: { f: Placeable; s: number; pcb?: string }) {
  const Draw = FAMILIES[f.family];
  const rot = f.rot ?? 0;
  const swap = rot === 90 || rot === 270;
  const w = (swap ? f.h_mm : f.w_mm) * s;
  const h = (swap ? f.w_mm : f.h_mm) * s;
  const spec: Spec = { family: f.family, variant: f.variant, label: f.label, color: f.color, w, h, s, pcb };
  if (!rot) return <Draw {...spec} />;
  const cx = (f.w_mm * s) / 2;
  const cy = (f.h_mm * s) / 2;
  return <g transform={`translate(${cx} ${cy}) rotate(${rot}) translate(${-w / 2} ${-h / 2})`}><Draw {...spec} /></g>;
}

/** A whole part: its body, then its features (chips, connectors, holes...) on top, in mm from the top-left. */
export function PartArt({ drawing, s = PX_PER_MM }: { drawing: PartDrawing; s?: number }) {
  return (
    <g pointerEvents="none">
      <Art f={{ family: drawing.family, variant: drawing.variant, label: drawing.label, w_mm: drawing.w_mm, h_mm: drawing.h_mm }} s={s} pcb={drawing.pcb_color} />
      {(drawing.features ?? []).map((f, i) => (
        <g key={i} transform={`translate(${f.x_mm * s} ${f.y_mm * s})`}><Art f={f} s={s} pcb={drawing.pcb_color} /></g>
      ))}
    </g>
  );
}

/** One feature on its own, for the gallery. */
export function FeatureArt({ f, s = PX_PER_MM }: { f: Placeable; s?: number }) {
  return <g pointerEvents="none"><Art f={f} s={s} /></g>;
}
