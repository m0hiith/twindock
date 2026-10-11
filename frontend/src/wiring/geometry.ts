// Breadboard-view layout, computed from the kit file. Units are SVG px at PX_PER_MM (10 px per mm), so
// the dev board keeps its real 30.4 × 55.0 mm proportions and every external part is drawn at the size
// of its `drawing`: relative sizes on the page are real.
import { pinGroup, splitRef, type Connection, type Part, type Pin, type WiringIndex } from "./model";
import { PX_PER_MM } from "./parts";

export { PX_PER_MM };
const BOARD_ORIGIN = { x: 680, y: 120 };
/** Right edge of the external-module column when the kit has a dev board (its connector is on the board's left edge). */
const MODULE_COL_RIGHT = 600;
/** Fallback box for a part with no drawing. */
const MODULE = { w: 210, h: 120 };
const TRANSDUCER = { w: 270, h: 92 };
const ROW_GAP = 130; // clear space between rows: room for captions and cables
const CAPTION = 64; // caption block under every external part
const COL_GAP = 90;
const CALLOUT_X = 1070;
const MARGIN = 70;

export interface Box { x: number; y: number; w: number; h: number }
export type Side = "left" | "right" | "top" | "bottom";
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
  /** Pin groups drawn as connectors on parts without a drawing ("qwiic_in" -> its pins' bounding box). */
  connectors: { name: string; box: Box; side: Side }[];
  /** True when the part is drawn from its `drawing` (true size) instead of a generic module box. */
  drawn: boolean;
}

export interface Wire { conn: Connection; d: string; a: PinPos; b: PinPos }
/** A pre-made cable (Qwiic, M12...) between two connectors: drawn once, as a cable, not as separate wires. */
export interface Cable { id: string; medium: Connection["medium"]; a: End; b: End; d: string; conns: Connection[] }
export interface End { x: number; y: number; side: Side; box: Box }
export interface Trace { conn: Connection; d: string; partId: string }
export interface Pad { number: number; net: string; fn?: string; x: number; y: number; used: boolean }
export interface Callout { partId: string; x: number; y: number; anchor: [number, number] }

export interface Geometry {
  board: Box | null;
  parts: Map<string, PlacedPart>;
  pins: Map<string, PinPos>;
  wires: Wire[];
  cables: Cable[];
  traces: Trace[];
  pads: Pad[];
  callouts: Callout[];
  /** Everything drawn fits in this rectangle (it can start left of 0 for wide parts). */
  canvas: { x: number; y: number; w: number; h: number };
}

const sizeOf = (p: Part): { w: number; h: number; drawn: boolean } =>
  p.drawing
    ? { w: p.drawing.w_mm * PX_PER_MM, h: p.drawing.h_mm * PX_PER_MM, drawn: true }
    : { ...(p.kind === "transducer" ? TRANSDUCER : MODULE), drawn: false };

/** Which edge of a w×h box a point is closest to. */
function nearestSide(x: number, y: number, w: number, h: number): Side {
  const d: [Side, number][] = [["left", x], ["right", w - x], ["top", y], ["bottom", h - y]];
  return d.reduce((a, b) => (b[1] < a[1] ? b : a))[0];
}

export function layoutBreadboard(ix: WiringIndex, photo: boolean): Geometry {
  const bd = ix.w.board_drawing;
  // Kits without a photographed dev board have no board outline: the processor is an ordinary module
  // at the top of a tree and every other part hangs below what it connects to.
  const tree = !bd;
  const board: Box | null = bd ? { ...BOARD_ORIGIN, w: bd.width_mm * PX_PER_MM, h: bd.height_mm * PX_PER_MM } : null;
  const onBoardBox = (pct: { x: number; y: number; w: number; h: number }): Box => ({
    x: board!.x + (pct.x / 100) * board!.w, y: board!.y + (pct.y / 100) * board!.h,
    w: (pct.w / 100) * board!.w, h: (pct.h / 100) * board!.h,
  });

  const parts = new Map<string, PlacedPart>();
  const pins = new Map<string, PinPos>();

  // On-board parts: measured photo outline when we have the photo and the outline, else UG581 figure.
  if (board) {
    for (const p of ix.w.parts.filter((q) => q.location === "on-board")) {
      const f = ix.feature(p.id);
      const measured = photo && p.outline_pct ? p.outline_pct : null;
      const pct = measured ?? f;
      if (!pct) continue;
      parts.set(p.id, { part: p, box: onBoardBox(pct), onBoard: true, approx: !measured, connectors: [], drawn: false });
    }
  }

  // External parts: one row per distance from the board, each row as tall as its tallest part.
  const external = ix.w.parts.filter((p) => p.location === "external");
  const rows = new Map<number, Part[]>();
  for (const p of external) {
    const d = ix.depth.get(p.id) ?? 1;
    rows.set(d, [...(rows.get(d) ?? []), p]);
  }
  // Where a part's pin sits once the part is placed (drawing position when known, else the box centre).
  const pinAt = (ref: string): { x: number; y: number } | null => {
    const { part, pin } = splitRef(ref);
    const placed = parts.get(part);
    if (!placed) return null;
    const q = placed.part.pins.find((x) => x.name === pin);
    if (placed.drawn && q?.x_mm != null && q.y_mm != null) return { x: placed.box.x + q.x_mm * PX_PER_MM, y: placed.box.y + q.y_mm * PX_PER_MM };
    return { x: placed.box.x + placed.box.w / 2, y: placed.box.y + placed.box.h / 2 };
  };
  let y = 60;
  for (const d of [...rows.keys()].sort((a, b) => a - b)) {
    const row = rows.get(d)!;
    const sizes = new Map(row.map((p) => [p.id, sizeOf(p)]));
    const total = row.reduce((a, p) => a + sizes.get(p.id)!.w, 0) + (row.length - 1) * COL_GAP;
    if (!tree) {
      // With a dev board, rows end at its left, where its Qwiic connector is.
      let x = MODULE_COL_RIGHT - total;
      for (const p of row) {
        const sz = sizes.get(p.id)!;
        parts.set(p.id, { part: p, box: { x, y, w: sz.w, h: sz.h }, onBoard: false, approx: false, connectors: [], drawn: sz.drawn });
        x += sz.w + COL_GAP;
      }
    } else {
      // In a tree each part goes under the pins it connects to on the rows above, so wires stay short and
      // rarely cross: sort by that target, place left to right without overlap, then centre the row on its targets.
      const target = new Map<string, number>();
      for (const p of row) {
        const xs = ix.connectionsOf(p.id).flatMap((c) => {
          const other = splitRef(c.from).part === p.id ? c.to : c.from;
          const at = pinAt(other);
          return at ? [at.x] : [];
        });
        target.set(p.id, xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 700);
      }
      const order = [...row].sort((a, b) => target.get(a.id)! - target.get(b.id)!);
      const xs: number[] = [];
      let right = -Infinity;
      for (const p of order) {
        const w = sizes.get(p.id)!.w;
        const x = Math.max(target.get(p.id)! - w / 2, right + COL_GAP);
        xs.push(x);
        right = x + w;
      }
      const placedMid = (xs[0]! + right) / 2;
      const wantMid = order.reduce((a, p) => a + target.get(p.id)!, 0) / order.length;
      const shift = wantMid - placedMid;
      order.forEach((p, i) => {
        const sz = sizes.get(p.id)!;
        parts.set(p.id, { part: p, box: { x: xs[i]! + shift, y, w: sz.w, h: sz.h }, onBoard: false, approx: false, connectors: [], drawn: sz.drawn });
      });
    }
    y += Math.max(...row.map((p) => sizes.get(p.id)!.h)) + CAPTION + ROW_GAP;
  }

  // Pins of external parts. With a drawing the pad sits where the datasheet puts it; without one each
  // pin group is spread along the side facing whatever it connects to.
  for (const placed of parts.values()) {
    if (placed.onBoard) continue;
    const p = placed.part;
    const b = placed.box;
    const depth = ix.depth.get(p.id) ?? 1;
    const loose: Pin[] = [];
    for (const pin of p.pins) {
      if (placed.drawn && pin.x_mm != null && pin.y_mm != null) {
        const lx = pin.x_mm * PX_PER_MM;
        const ly = pin.y_mm * PX_PER_MM;
        pins.set(`${p.id}.${pin.name}`, {
          ref: `${p.id}.${pin.name}`, part: p, pin, x: b.x + lx, y: b.y + ly, side: pin.side ?? nearestSide(lx, ly, b.w, b.h),
        });
      } else loose.push(pin);
    }
    const bySide = new Map<Side, Map<string, Pin[]>>();
    for (const pin of loose) {
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
      let along = (vertical ? b.y + b.h / 2 : b.x + b.w / 2) - span / 2;
      for (const [name, list] of groups) {
        const first = along;
        for (const pin of list) {
          const x = side === "left" ? b.x : side === "right" ? b.x + b.w : along;
          const yy = side === "top" ? b.y : side === "bottom" ? b.y + b.h : along;
          pins.set(`${p.id}.${pin.name}`, { ref: `${p.id}.${pin.name}`, part: p, pin, x, y: yy, side });
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
    const ext = p.pins.filter((pin) =>
      ix.w.connections.some((c) => {
        const ref = `${p.id}.${pin.name}`;
        if (c.from !== ref && c.to !== ref) return false;
        return ix.part(ix.otherEnd(c, p.id))?.location === "external";
      }));
    ext.forEach((pin, i) => {
      const b = placed.box;
      const yy = b.y + ((i + 1) / (ext.length + 1)) * b.h;
      pins.set(`${p.id}.${pin.name}`, { ref: `${p.id}.${pin.name}`, part: p, pin, x: b.x, y: yy, side: "left" });
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

  // Pre-made cables: every connection of one cable medium between the same two connector groups is one cable.
  const cables: Cable[] = [];
  const byCable = new Map<string, Wire[]>();
  for (const w of wires) {
    if (!w.conn.medium.endsWith("_cable")) continue;
    const key = [w.conn.medium, ...[w.conn.from, w.conn.to].map((r) => `${splitRef(r).part}.${pinGroup(splitRef(r).pin)}`).sort()].join("|");
    byCable.set(key, [...(byCable.get(key) ?? []), w]);
  }
  for (const [key, ws] of byCable) {
    const end = (pick: (w: Wire) => PinPos): End => {
      const ps = ws.map(pick);
      const x = ps.reduce((a, p) => a + p.x, 0) / ps.length;
      const yy = ps.reduce((a, p) => a + p.y, 0) / ps.length;
      const pad = 36;
      return { x, y: yy, side: ps[0]!.side, box: { x: x - pad, y: yy - pad, w: pad * 2, h: pad * 2 } };
    };
    const a = end((w) => w.a);
    const b = end((w) => w.b);
    cables.push({ id: key, medium: ws[0]!.conn.medium, a, b, d: wirePath(a, b), conns: ws.map((w) => w.conn) });
  }

  const usedNets = new Set<string>();
  for (const c of ix.w.connections) {
    for (const ref of [c.from, c.to]) {
      const gpio = ix.pin(ref)?.pin.gpio;
      if (gpio) usedNets.add(gpio);
    }
  }
  const pads: Pad[] = !board || !bd ? [] : bd.pad_columns.flatMap((col) =>
    col.pads.map((pad, i) => ({
      number: pad.number, net: pad.net, fn: pad.function,
      x: board.x + (col.x / 100) * board.w,
      y: board.y + ((col.y_first + (i * (col.y_last - col.y_first)) / Math.max(1, col.pads.length - 1)) / 100) * board.h,
      used: usedNets.has(pad.net),
    })));

  // Callouts for on-board parts, right of the board, in the order the parts appear top to bottom.
  const callouts: Callout[] = [];
  const onBoard = [...parts.values()].filter((p) => p.onBoard).sort((a, b) => a.box.y - b.box.y);
  let nextY = (board?.y ?? 0) - 10;
  for (const p of onBoard) {
    const cy = p.box.y + p.box.h / 2;
    const yy = Math.max(nextY, cy - 26);
    callouts.push({ partId: p.part.id, x: CALLOUT_X, y: yy, anchor: [p.box.x + p.box.w, cy] });
    nextY = yy + 80;
  }

  // Canvas = bounding box of everything, plus room for dimension lines, captions and the scale bar.
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const grow = (b: Box) => { x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y); x1 = Math.max(x1, b.x + b.w); y1 = Math.max(y1, b.y + b.h); };
  for (const p of parts.values()) grow(p.box.h ? { ...p.box, h: p.box.h + (p.onBoard ? 0 : CAPTION) } : p.box);
  if (board) grow({ x: board.x - 20, y: board.y - 60, w: board.w + 80, h: board.h + 90 });
  for (const c of callouts) grow({ x: c.x, y: c.y, w: 250, h: 66 });
  const canvas = { x: x0 - MARGIN, y: y0 - MARGIN, w: x1 - x0 + MARGIN * 2, h: y1 - y0 + MARGIN * 2 + 40 };

  return { board, parts, pins, wires, cables, traces, pads, callouts, canvas };
}

function wirePath(a: { x: number; y: number; side: Side }, b: { x: number; y: number; side: Side }): string {
  const [ax, ay] = NORMAL[a.side];
  const [bx, by] = NORMAL[b.side];
  const k = Math.max(36, Math.hypot(b.x - a.x, b.y - a.y) * 0.45);
  return `M${a.x},${a.y} C${a.x + ax * k},${a.y + ay * k} ${b.x + bx * k},${b.y + by * k} ${b.x},${b.y}`;
}

/** The same curve as `wirePath`, shifted sideways by `off` px at both ends (used to lay conductors side by side in a cable). */
export function offsetPath(a: End, b: End, offA: number, offB: number): string {
  const perp = (s: Side): [number, number] => (s === "left" || s === "right" ? [0, 1] : [1, 0]);
  const [pax, pay] = perp(a.side);
  const [pbx, pby] = perp(b.side);
  const ax = a.x + pax * offA, ay = a.y + pay * offA;
  const bx = b.x + pbx * offB, by = b.y + pby * offB;
  return wirePath({ x: ax, y: ay, side: a.side }, { x: bx, y: by, side: b.side });
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
