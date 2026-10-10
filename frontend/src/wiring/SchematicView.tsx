// Schematic view: a block schematic of the same data. The SoC on the left, one bar per digital bus,
// each part hanging off its bus with its address; analog parts hang off the part they connect to.
import { useMemo, useRef, useState } from "react";
import { color } from "../theme";
import { splitRef, statusHelp, statusLabel, type Bus, type Part, type WiringIndex } from "./model";
import { FONT, relPos, Tooltip, usePanZoom, ZoomControls, type HoverInfo } from "./ui";

const CANVAS = { w: 1340, h: 880 };
const SOC = { x: 40, y: 90, w: 250, h: 760 };
const SLOT = { x0: 350, w: 170, gap: 22, h: 112 };
const STUB = 44;

interface Row { bus: Bus; y: number; parts: { part: Part; x: number; y: number }[]; children: { part: Part; parent: string; x: number; y: number }[] }

function layout(ix: WiringIndex): { rows: Row[]; power: Bus[] } {
  const digital = ix.w.buses.filter((b) => b.kind === "i2c" || b.kind === "spi");
  const order = (p: Part) => (p.location === "on-board" ? (p.kind === "connector" ? 1 : 0) : 2);
  const placed = new Set<string>();
  const rows: Row[] = [];
  let y = 220;
  for (const bus of digital) {
    const members = ix.w.parts.filter((p) => p.bus === bus.id && p.kind !== "soc").sort((a, b) => order(a) - order(b));
    const parts = members.map((part, i) => ({ part, x: SLOT.x0 + i * (SLOT.w + SLOT.gap), y: y + STUB }));
    members.forEach((p) => placed.add(p.id));
    const children: Row["children"] = [];
    for (const { part, x } of parts) {
      for (const c of ix.connectionsOf(part.id)) {
        const other = ix.otherEnd(c, part.id);
        const o = ix.part(other);
        if (!o || placed.has(other) || o.kind === "soc" || o.bus === bus.id) continue;
        placed.add(other);
        children.push({ part: o, parent: part.id, x, y: y + STUB + SLOT.h + 60 });
      }
    }
    rows.push({ bus, y, parts, children });
    y += STUB + SLOT.h + (children.length ? SLOT.h + 60 : 0) + 90;
  }
  return { rows, power: ix.w.buses.filter((b) => b.kind === "power") };
}

interface Props {
  ix: WiringIndex;
  selected: string | null;
  onSelect: (id: string | null) => void;
  svgRef: (el: SVGSVGElement | null) => void;
}

export function SchematicView({ ix, selected, onSelect, svgRef }: Props) {
  const { rows, power } = useMemo(() => layout(ix), [ix]);
  const pz = usePanZoom(CANVAS);
  const container = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const [hoverPart, setHoverPart] = useState<string | null>(null);
  const soc = ix.w.parts.find((p) => p.kind === "soc");

  const select = (id: string | null) => (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!pz.dragged()) onSelect(id);
  };
  const partHover = (p: Part) => ({
    onPointerEnter: (e: React.PointerEvent) => {
      setHoverPart(p.id);
      setHover({
        ...relPos(e, container.current), title: `${p.part_number} · ${p.name}`,
        rows: [["Status", `${statusLabel[p.status]} · ${statusHelp[p.status].toLowerCase()}`], ["Bus", ix.busName(p.bus)],
          ...(p.address ? [["Address", ix.address(p)]] : []), ["Power", ix.busName(p.supplied_from)]] as [string, string][],
      });
    },
    onPointerMove: (e: React.PointerEvent) => setHover((h) => (h ? { ...h, ...relPos(e, container.current) } : h)),
    onPointerLeave: () => { setHover(null); setHoverPart(null); },
  });

  // SoC pins on each bus, e.g. "ULP_GPIO_6 · I2C2_SDA".
  const socPinsOn = (busId: string | null) => {
    if (!soc) return [];
    const refs = new Set(ix.w.connections.filter((c) => c.bus === busId).flatMap((c) => [c.from, c.to]).filter((r) => splitRef(r).part === soc.id));
    return soc.pins.filter((p) => refs.has(`${soc.id}.${p.name}`));
  };
  const controlLines = soc
    ? [
      ...ix.w.connections.filter((c) => c.bus === null && (splitRef(c.from).part === soc.id || splitRef(c.to).part === soc.id))
        .reduce((m, c) => {
          const socRef = splitRef(c.from).part === soc.id ? c.from : c.to;
          const other = ix.part(ix.otherEnd(c, soc.id));
          m.set(socRef, [...(m.get(socRef) ?? []), `${other?.part_number ?? "?"} ${c.signal}`]);
          return m;
        }, new Map<string, string[]>())
        .entries(),
    ].map(([ref, from]): [string, string] => [splitRef(ref).pin, `← ${from.join(", ")}`])
    : [];
  const enables = [...new Set(ix.w.parts.map((p) => p.enable_pin).filter((e): e is string => !!e))].map((ref) => {
    const fed = ix.w.parts.filter((p) => p.enable_pin === ref).map((p) => p.part_number);
    return [`${splitRef(ref).pin} → ${ix.pin(ref)?.pin.signal ?? "EN"}`, `powers ${fed.join(", ")}`] as [string, string];
  });

  return (
    <div ref={container} className="relative h-full w-full overflow-hidden rounded-[14px]">
      <svg ref={pz.attach(svgRef)} viewBox={pz.viewBox} preserveAspectRatio="xMidYMid meet"
        fontFamily={FONT} data-full-w={CANVAS.w} data-full-h={CANVAS.h}
        className="h-full w-full cursor-grab touch-none select-none active:cursor-grabbing" {...pz.handlers} onClick={select(null)}>
        <rect x={-CANVAS.w} y={-CANVAS.h} width={CANVAS.w * 3} height={CANVAS.h * 3} fill="#FFFFFF" />

        {soc && (
          <g onClick={select(soc.id)} className="cursor-pointer" {...partHover(soc)}>
            <rect x={SOC.x} y={SOC.y} width={SOC.w} height={SOC.h} rx={12} fill="#FFFFFF" stroke={selected === soc.id || hoverPart === soc.id ? color.accent : color.ink} strokeWidth={2} />
            <text x={SOC.x + 18} y={SOC.y + 32} fontSize={18} fontWeight={700} fill={color.ink}>{soc.part_number}</text>
            <text x={SOC.x + 18} y={SOC.y + 52} fontSize={13} fill={color.ink2}>{soc.name} · {ix.w.board}</text>
            {rows.map((r) => {
              const pins = socPinsOn(r.bus.id);
              return pins.map((p, i) => (
                <text key={`${r.bus.id}-${p.name}`} x={SOC.x + SOC.w - 14} y={r.y - ((pins.length - 1) / 2 - i) * 15 + 4} textAnchor="end" fontSize={11.5} fill={color.ink}>
                  {p.gpio ?? p.name} · {p.signal}
                </text>
              ));
            })}
            <text x={SOC.x + 18} y={SOC.y + SOC.h - 118} fontSize={12} fontWeight={600} fill={color.ink}>Control lines</text>
            {[...controlLines, ...enables].map(([head, rest], i) => (
              <text key={head} x={SOC.x + 18} y={SOC.y + SOC.h - 98 + i * 34} fontSize={11} fill={color.ink2}>
                <tspan fill={color.ink}>{head}</tspan>
                <tspan x={SOC.x + 26} dy={14}>{clip(rest, 40)}</tspan>
              </text>
            ))}
          </g>
        )}

        {rows.map((r) => {
          const last = r.parts.at(-1);
          const lastWired = [...r.parts].reverse().find((p) => p.part.status !== "planned");
          const solidEnd = lastWired ? lastWired.x + SLOT.w / 2 : SOC.x + SOC.w;
          const end = last ? last.x + SLOT.w / 2 : SOC.x + SOC.w + 40;
          const firstExternal = r.parts.find((p) => p.part.location === "external");
          return (
            <g key={r.bus.id}>
              <line x1={SOC.x + SOC.w} y1={r.y} x2={solidEnd} y2={r.y} stroke={color.ink} strokeWidth={4} />
              {end > solidEnd && <line x1={solidEnd} y1={r.y} x2={end} y2={r.y} stroke={color.idle} strokeWidth={4} strokeDasharray="10 7" />}
              <text x={SOC.x + SOC.w + 14} y={r.y - 12} fontSize={13} fontWeight={600} fill={color.ink}>{r.bus.name}</text>
              <text x={SOC.x + SOC.w + 14} y={r.y + 22} fontSize={11.5} fill={color.ink2}>{r.bus.controller ?? r.bus.kind.toUpperCase()}</text>
              {firstExternal && (
                <g>
                  <line x1={firstExternal.x - SLOT.gap / 2} y1={r.y - 50} x2={firstExternal.x - SLOT.gap / 2} y2={r.y + STUB + SLOT.h + 10}
                    stroke={color.idle} strokeDasharray="4 4" />
                  <text x={firstExternal.x + 2} y={r.y - 38} fontSize={11.5} fill={color.ink2}>External, over the Qwiic cable →</text>
                </g>
              )}
              {r.parts.map(({ part, x, y }) => {
                const sig = [...new Set(ix.connectionsOf(part.id).filter((c) => c.bus === r.bus.id && c.signal !== "GND" && c.signal !== "3V3").map((c) => c.signal))];
                const planned = part.status === "planned";
                return (
                  <g key={part.id}>
                    <line x1={x + SLOT.w / 2} y1={r.y} x2={x + SLOT.w / 2} y2={y} stroke={planned ? color.idle : color.ink} strokeWidth={2}
                      strokeDasharray={planned ? "6 4" : undefined} />
                    <circle cx={x + SLOT.w / 2} cy={r.y} r={4.5} fill={planned ? color.idle : color.ink} />
                    <text x={x + SLOT.w / 2 + 7} y={r.y + 26} fontSize={10.5} fill={color.ink2}>{sig.join(" ")}</text>
                    <PartBox part={part} x={x} y={y} ix={ix} active={selected === part.id || hoverPart === part.id}
                      onClick={select(part.id)} hover={partHover(part)} />
                  </g>
                );
              })}
              {r.children.map(({ part, parent, x, y }) => {
                const p = r.parts.find((q) => q.part.id === parent)!;
                const sigs = ix.connectionsOf(part.id).filter((c) => ix.otherEnd(c, part.id) === parent).map((c) => c.signal);
                const planned = part.status === "planned";
                return (
                  <g key={part.id}>
                    <line x1={x + SLOT.w / 2} y1={p.y + SLOT.h} x2={x + SLOT.w / 2} y2={y} stroke={planned ? color.idle : color.ink} strokeWidth={2}
                      strokeDasharray={planned ? "6 4" : undefined} />
                    <text x={x + SLOT.w / 2 + 8} y={p.y + SLOT.h + 34} fontSize={10.5} fill={color.ink2}>{sigs.length} wires: {sigs.join(" ")}</text>
                    <PartBox part={part} x={x} y={y} ix={ix} active={selected === part.id || hoverPart === part.id}
                      onClick={select(part.id)} hover={partHover(part)} />
                  </g>
                );
              })}
            </g>
          );
        })}

        <PowerBoxes power={power} ix={ix} />
      </svg>
      <ZoomControls onIn={() => pz.zoomBy(1.25)} onOut={() => pz.zoomBy(0.8)} onFit={pz.fit} />
      <Tooltip info={hover} />
    </div>
  );
}

function PartBox({ part, x, y, ix, active, onClick, hover }: {
  part: Part; x: number; y: number; ix: WiringIndex; active: boolean; onClick: (e: React.MouseEvent) => void; hover: Record<string, unknown>;
}) {
  const planned = part.status === "planned";
  const ink = planned ? color.ink2 : color.ink;
  const addr = part.address ? ix.address(part) : part.bus && ix.buses.get(part.bus)?.kind === "spi"
    ? `SPI · CS ${part.pins.find((p) => p.signal === "CS")?.gpio ?? "?"}` : null;
  const title = part.part_number.length > 18 ? part.name : part.part_number;
  return (
    <g onClick={onClick} className="cursor-pointer" {...hover}>
      <rect x={x} y={y} width={SLOT.w} height={SLOT.h} rx={10} fill={planned ? "#F6F6F6" : "#FFFFFF"}
        stroke={active ? color.accent : planned ? color.idle : color.ink} strokeWidth={active ? 2.5 : 1.5} strokeDasharray={planned ? "6 4" : undefined} />
      <text x={x + 12} y={y + 24} fontSize={14} fontWeight={700} fill={ink}>{title}</text>
      <text x={x + 12} y={y + 41} fontSize={11.5} fill={color.ink2}>{clip(title === part.name ? part.part_number : part.name, 24)}</text>
      {addr && <text x={x + 12} y={y + 62} fontSize={12} fontWeight={600} fill={ink}>{addr}</text>}
      <text x={x + 12} y={y + (addr ? 82 : 66)} fontSize={11} fill={color.ink2}>{part.location === "on-board" ? "On board" : "External"} · {statusLabel[part.status]}</text>
      {planned && <text x={x + 12} y={y + 100} fontSize={11} fontWeight={600} fill={color.ink2}>Not connected yet</text>}
    </g>
  );
}

function PowerBoxes({ power, ix }: { power: Bus[]; ix: WiringIndex }) {
  const w = 360;
  const x0 = CANVAS.w - power.length * (w + 20) - 20;
  const y = 680;
  return (
    <g>
      {power.map((b, i) => {
        const fed = ix.w.parts.filter((p) => p.supplied_from === b.id);
        const x = x0 + i * (w + 20);
        return (
          <g key={b.id}>
            <rect x={x} y={y} width={w} height={150} rx={10} fill="#FAFAFA" stroke={color.cardBorder} />
            <text x={x + 14} y={y + 24} fontSize={13} fontWeight={600} fill={color.ink}>{b.name}{b.voltage_v ? ` · ${b.voltage_v} V` : ""}</text>
            <text x={x + 14} y={y + 44} fontSize={11.5} fill={color.ink2}>Feeds:</text>
            {fed.map((p, j) => (
              <text key={p.id} x={x + 24} y={y + 64 + j * 18} fontSize={12} fill={p.status === "planned" ? color.ink2 : color.ink}>
                {p.part_number}{p.status === "planned" ? " (planned)" : ""}
              </text>
            ))}
          </g>
        );
      })}
    </g>
  );
}

const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);
