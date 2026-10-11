// Breadboard-view layout, computed from wiring.json. Units are SVG px; the board is drawn at
// 10 px per mm so its outline keeps the real 30.4 × 55.0 mm proportions from UG581.
import { pinGroup, splitRef, type Connection, type Part, type Pin, type WiringIndex } from "./model";

export const PX_PER_MM = 10;
export const CANVAS = { w: 1340, h: 780 };
const BOARD_ORIGIN = { x: 680, y: 120 };
/** External modules stack in a column left of the board (the Qwiic connector is on the left edge). */
const MODULE_COL_X = 430;
const MODULE = { w: 210, h: 120 };
const TRANSDUCER = { w: 270, h: 92 };
const ROW_GAP = 214;
const CALLOUT_X = 1070;

export interface Box { x: number; y: number; w: number; h: number }
type Side = "left" | "right" | "top" | "bottom";
const NORMAL: Record<Side, [number, number]> = { left: [-1, 0], right: [1, 0], top: [0, -1], bottom: [0, 1] };

export interface PinPos {
  ref: string;
  part: Part;
  pin: Pin;
  x: number;
  y: number;
  side: Side;
}

export interface PlacedPart {
  part: Part;
  box: Box;
  onBoard: boolean;
  /** On-board position comes from UG581 Figure 1.1, not from a measurement on the photo. */
  approx: boolean;
  /** Pin groups drawn as connectors on external modules ("qwiic_in" -> its pins' bounding box). */
  connectors: { name: string; box: Box; side: Side }[];
}

export interface Wire { conn: Connection; d: string; a: PinPos; b: PinPos }
export interface Trace { conn: Connection; d: string; partId: string }
export interface Pad { number: number; net: string; fn?: string; x: number; y: number; used: boolean }
export interface Callout { partId: string; x: number; y: number; anchor: [number, number] }

export interface Geometry {
  board: Box;
  parts: Map<string, PlacedPart>;
  pins: Map<string, PinPos>;
  wires: Wire[];
  traces: Trace[];
  pads: Pad[];
  callouts: Callout[];
}

export function layoutBreadboard(ix: WiringIndex, photo: boolean): Geometry {
  const bd = ix.w.board_drawing;
  // Kits without a photographed dev board have no board outline: the processor is an ordinary module
  // at the top of a tree and every other part hangs below what it connects to.
  const tree = !bd;
  const board: Box = { ...BOARD_ORIGIN, w: (bd?.width_mm ?? 0) * PX_PER_MM, h: (bd?.height_mm ?? 0) * PX_PER_MM };
  const onBoardBox = (pct: { x: number; y: number; w: number; h: number }): Box => ({
    x: board.x + (pct.x / 100) * board.w, y: board.y + (pct.y / 100) * board.h,
    w: (pct.w / 100) * board.w, h: (pct.h / 100) * board.h,
  });

  const parts = new Map<string, PlacedPart>();
  const pins = new Map<string, PinPos>();

  // On-board parts: measured photo outline when we have the photo and the outline, else UG581 figure.
  for (const p of ix.w.parts.filter((q) => q.location === "on-board")) {
    const f = ix.feature(p.id);
    const measured = photo && p.outline_pct ? p.outline_pct : null;
    const pct = measured ?? f;
    if (!pct) continue;
    parts.set(p.id, { part: p, box: onBoardBox(pct), onBoard: true, approx: !measured, connectors: [] });
  }

  // External parts: one row per distance from the board, spread sideways when a row has several.
  const external = ix.w.parts.filter((p) => p.location === "external");
  const rows = new Map<number, Part[]>();
  for (const p of external) {
    const d = ix.depth.get(p.id) ?? 1;
    rows.set(d, [...(rows.get(d) ?? []), p]);
  }
  for (const [d, row] of rows) {
    row.forEach((p, i) => {
      const size = p.kind === "transducer" ? TRANSDUCER : MODULE;
      const cx = (tree ? CANVAS.w / 2 : MODULE_COL_X) + (i - (row.length - 1) / 2) * (MODULE.w + 40);
      parts.set(p.id, {
        part: p, box: { x: cx - size.w / 2, y: 60 + (tree ? d : d - 1) * ROW_GAP, ...size }, onBoard: false, approx: false, connectors: [],
      });
    });
  }

  // Pins of external parts: each pin group sits on the side facing whatever it connects to.
  for (const placed of parts.values()) {
    if (placed.onBoard) continue;
    const p = placed.part;
    const depth = ix.depth.get(p.id) ?? 1;
    const bySide = new Map<Side, Map<string, Pin[]>>();
    for (const pin of p.pins) {
      const group = pinGroup(pin.name);
      const conns = ix.w.connections.filter((c) => c.from === `${p.id}.${pin.name}` || c.to === `${p.id}.${pin.name}`);
      const towardsBoard = conns.some((c) => (ix.depth.get(ix.otherEnd(c, p.id)) ?? 99) < depth);
      const side: Side = towardsBoard ? (depth === 1 && !tree ? "right" : "top") : "bottom";
      const groups = bySide.get(side) ?? new Map<string, Pin[]>();
      groups.set(group, [...(groups.get(group) ?? []), pin]);
      bySide.set(side, groups);
    }
    for (const [side, groups] of bySide) {
      const vertical = side === "left" || side === "right";
      const step = vertical ? 20 : 30;
      const all = [...groups.values()].flat();
      const gap = step * 0.6;
      const span = (all.length - 1) * step + (groups.size - 1) * gap;
      const b = placed.box;
      let along = (vertical ? b.y + b.h / 2 : b.x + b.w / 2) - span / 2;
      for (const [name, list] of groups) {
        const first = along;
        for (const pin of list) {
          const x = side === "left" ? b.x : side === "right" ? b.x + b.w : along;
          const y = side === "top" ? b.y : side === "bottom" ? b.y + b.h : along;
          pins.set(`${p.id}.${pin.name}`, { ref: `${p.id}.${pin.name}`, part: p, pin, x, y, side });
          along += step;
        }
        const last = along - step;
        if (name) {
          const pad = 9;
          placed.connectors.push({
            name, side,
            box: vertical
              ? { x: side === "right" ? b.x + b.w - 44 : b.x, y: first - pad, w: 44, h: last - first + pad * 2 }
              : { x: first - pad * 1.6, y: side === "bottom" ? b.y + b.h - 19 : b.y, w: last - first + pad * 3.2, h: 19 },
          });
        }
        along += gap;
      }
    }
  }

  // Pins of on-board parts that are wired to external parts: along the edge facing them (left).
  for (const placed of parts.values()) {
    if (!placed.onBoard) continue;
    const p = placed.part;
    const external = p.pins.filter((pin) =>
      ix.w.connections.some((c) => {
        const ref = `${p.id}.${pin.name}`;
        if (c.from !== ref && c.to !== ref) return false;
        return ix.part(ix.otherEnd(c, p.id))?.location === "external";
      }));
    external.forEach((pin, i) => {
      const b = placed.box;
      const y = b.y + ((i + 1) / (external.length + 1)) * b.h;
      pins.set(`${p.id}.${pin.name}`, { ref: `${p.id}.${pin.name}`, part: p, pin, x: b.x, y, side: "left" });
    });
  }

  const wires: Wire[] = [];
  const traces: Trace[] = [];
  const traceCount = new Map<string, number>();
  for (const c of ix.w.connections) {
    if (c.medium === "pcb") {
      const a = splitRef(c.from).part;
      const b = splitRef(c.to).part;
      const soc = parts.get(a)?.part.kind === "soc" ? a : b;
      const target = soc === a ? b : a;
      const from = parts.get(soc)?.box;
      const to = parts.get(target)?.box;
      if (!from || !to) continue;
      const n = traceCount.get(target) ?? 0;
      traceCount.set(target, n + 1);
      traces.push({ conn: c, d: tracePath(from, to, n), partId: target });
      continue;
    }
    const a = pins.get(c.from);
    const b = pins.get(c.to);
    if (!a || !b) continue;
    wires.push({ conn: c, a, b, d: wirePath(a, b) });
  }

  const usedNets = new Set<string>();
  for (const c of ix.w.connections) {
    for (const ref of [c.from, c.to]) {
      const gpio = ix.pin(ref)?.pin.gpio;
      if (gpio) usedNets.add(gpio);
    }
  }
  const pads: Pad[] = (bd?.pad_columns ?? []).flatMap((col) =>
    col.pads.map((pad, i) => ({
      number: pad.number, net: pad.net, fn: pad.function,
      x: board.x + (col.x / 100) * board.w,
      y: board.y + ((col.y_first + (i * (col.y_last - col.y_first)) / Math.max(1, col.pads.length - 1)) / 100) * board.h,
      used: usedNets.has(pad.net),
    })));

  // Callouts for on-board parts, right of the board, in the order the parts appear top to bottom.
  const callouts: Callout[] = [];
  const onBoard = [...parts.values()].filter((p) => p.onBoard).sort((a, b) => a.box.y - b.box.y);
  let nextY = board.y - 10;
  for (const p of onBoard) {
    const cy = p.box.y + p.box.h / 2;
    const y = Math.max(nextY, cy - 26);
    callouts.push({ partId: p.part.id, x: CALLOUT_X, y, anchor: [p.box.x + p.box.w, cy] });
    nextY = y + 80;
  }

  return { board, parts, pins, wires, traces, pads, callouts };
}

function wirePath(a: PinPos, b: PinPos): string {
  const [ax, ay] = NORMAL[a.side];
  const [bx, by] = NORMAL[b.side];
  const k = Math.max(36, Math.hypot(b.x - a.x, b.y - a.y) * 0.45);
  return `M${a.x},${a.y} C${a.x + ax * k},${a.y + ay * k} ${b.x + bx * k},${b.y + by * k} ${b.x},${b.y}`;
}

/** PCB trace from the SoC to an on-board part: leave the SoC vertically, turn, enter the part. */
function tracePath(from: Box, to: Box, n: number): string {
  const off = (n - 1) * 4;
  const sx = from.x + from.w / 2 + off;
  const below = to.y > from.y + from.h;
  const sy = below ? from.y + from.h : from.y;
  const ty = to.y + to.h / 2 + off * 0.5;
  const tx = to.x + to.w / 2 < sx ? to.x + to.w : to.x;
  const inside = to.x <= sx && sx <= to.x + to.w;
  if (inside) return `M${sx},${sy} V${below ? to.y : to.y + to.h}`;
  return `M${sx},${sy} V${ty} H${tx}`;
}

