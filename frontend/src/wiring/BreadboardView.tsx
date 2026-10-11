// Breadboard view: the board at true proportions with its on-board sensors highlighted, the
// external modules as generic flat modules, and every connection from wiring.json as a wire or
// PCB trace. Pulses run along a part's data line when a real reading arrives.
import { useEffect, useMemo, useRef, useState } from "react";
import { color } from "../theme";
import { ago, useTick } from "../hud/ui";
import { layoutBreadboard, CANVAS, type Geometry, type PlacedPart } from "./geometry";
import { pinShort, splitRef, statusHelp, statusLabel, WIRE_HEX, WIRE_SIGNAL, type Connection, type WiringIndex } from "./model";
import { BOARD_PHOTO, type PhotoState } from "./photo";
import { formatReading, WAITING, type PartReadings } from "./readings";
import { FONT, relPos, Tooltip, usePanZoom, ZoomControls, type HoverInfo } from "./ui";

const PCB = "#1E1E1E";
const PAD = "#C9A45C";
const PAD_EDGE = "#9C7A35";
const PLANNED = color.idle;
const statusStroke = { planned: PLANNED, wired: "#FFFFFF", verified: color.ok } as const;

interface Props {
  ix: WiringIndex;
  photo: PhotoState;
  readings: Record<string, PartReadings>;
  online: boolean;
  selected: string | null;
  onSelect: (id: string | null) => void;
  svgRef: (el: SVGSVGElement | null) => void;
}

export function BreadboardView({ ix, photo, readings, online, selected, onSelect, svgRef }: Props) {
  const geo = useMemo(() => layoutBreadboard(ix, photo === "photo"), [ix, photo]);
  const pz = usePanZoom(CANVAS);
  const container = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const [hoverPart, setHoverPart] = useState<string | null>(null);
  const pathEls = useRef(new Map<string, SVGPathElement>());
  const pulses = usePulses(readings);
  useTick(1000); // reading ages

  const hoverable = (build: () => Omit<HoverInfo, "x" | "y">, partId: string | null = null) => ({
    onPointerEnter: (e: React.PointerEvent) => { setHover({ ...build(), ...relPos(e, container.current) }); setHoverPart(partId); },
    onPointerMove: (e: React.PointerEvent) => setHover((h) => (h ? { ...h, ...relPos(e, container.current) } : h)),
    onPointerLeave: () => { setHover(null); setHoverPart(null); },
  });
  const select = (id: string | null) => (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!pz.dragged()) onSelect(id);
  };
  const focus = selected ?? hoverPart;
  const refPath = (id: string) => (el: SVGPathElement | null) => {
    if (el) pathEls.current.set(id, el);
    else pathEls.current.delete(id);
  };

  const connName = (ref: string) => {
    const { part, pin } = splitRef(ref);
    return `${ix.part(part)?.part_number ?? part} ${pinShort(pin)}`;
  };
  const wireInfo = (c: Connection) => ({
    title: `${c.signal} ${c.medium === "pcb" ? "PCB trace" : "wire"}`,
    rows: [
      ["From", connName(c.from)], ["To", connName(c.to)],
      ...(c.wire_color ? [["Colour", `${c.wire_color}${WIRE_SIGNAL[c.wire_color] ? ` · ${WIRE_SIGNAL[c.wire_color]}` : ""}`]] : []),
      ["Medium", c.medium === "pcb" ? "Trace on the dev kit" : c.medium === "qwiic_cable" ? "Qwiic cable" : "Wire"],
      ["Status", `${statusLabel[c.status]} · ${c.medium === "pcb" ? "connected by the board" : statusHelp[c.status].toLowerCase()}`],
    ] as [string, string][],
  });

  return (
    <div ref={container} className="relative h-full w-full overflow-hidden rounded-[14px]">
      <svg
        ref={pz.attach(svgRef)}
        viewBox={pz.viewBox} preserveAspectRatio="xMidYMid meet" fontFamily={FONT}
        data-full-w={CANVAS.w} data-full-h={CANVAS.h}
        className="h-full w-full cursor-grab touch-none select-none active:cursor-grabbing" {...pz.handlers}
        onClick={select(null)}>
        <defs>
          <pattern id="bb-grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M20 0H0V20" fill="none" stroke="#E7E7E7" strokeWidth="1" />
          </pattern>
          <filter id="bb-shadow" x="-10%" y="-10%" width="120%" height="130%">
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#000" floodOpacity="0.12" />
          </filter>
        </defs>
        <rect x={-CANVAS.w} y={-CANVAS.h} width={CANVAS.w * 3} height={CANVAS.h * 3} fill="#F7F7F7" />
        <rect x={-CANVAS.w} y={-CANVAS.h} width={CANVAS.w * 3} height={CANVAS.h * 3} fill="url(#bb-grid)" />

        {/* Wires under the modules, so their ends tuck into the connectors. */}
        <g>
          {geo.wires.map((w) => {
            const planned = w.conn.status === "planned";
            const hex = WIRE_HEX[w.conn.wire_color ?? "black"] ?? "#555";
            const lit = focus !== null && (splitRef(w.conn.from).part === focus || splitRef(w.conn.to).part === focus);
            return (
              <g key={w.conn.id} opacity={planned && !lit ? 0.6 : 1} {...hoverable(() => wireInfo(w.conn))}>
                <path d={w.d} fill="none" stroke={w.conn.wire_color === "black" ? "#6B6B6B" : "#00000055"} strokeWidth={lit ? 7.5 : 6}
                  strokeLinecap="round" strokeDasharray={planned ? "10 7" : undefined} />
                <path ref={refPath(w.conn.id)} d={w.d} fill="none" stroke={hex} strokeWidth={lit ? 5 : 3.6} strokeLinecap="round"
                  strokeDasharray={planned ? "10 7" : undefined} />
                <path d={w.d} fill="none" stroke="transparent" strokeWidth={14} />
              </g>
            );
          })}
        </g>

        {[...geo.parts.values()].filter((p) => !p.onBoard).map((p) => (
          <ExternalPart key={p.part.id} placed={p} geo={geo} ix={ix} readings={readings[p.part.id]} online={online}
            selected={selected === p.part.id} hovered={hoverPart === p.part.id}
            onClick={select(p.part.id)} hoverable={hoverable} />
        ))}

        {ix.w.board_drawing && (
          <Board geo={geo} ix={ix} photo={photo} focus={focus} selected={selected} onSelect={select}
            hoverable={hoverable} wireInfo={wireInfo} refPath={refPath} />
        )}

        {geo.callouts.map((c) => {
          const placed = geo.parts.get(c.partId);
          if (!placed) return null;
          return (
            <Callout key={c.partId} x={c.x} y={c.y} anchor={c.anchor} placed={placed} readings={readings[c.partId]} online={online}
              active={focus === c.partId} onClick={select(c.partId)} />
          );
        })}

        {pulses.list.map((p) => (
          <Pulse key={p.key} steps={ix.dataPath(p.partId)} els={pathEls} onDone={() => pulses.remove(p.key)} />
        ))}
      </svg>
      <ZoomControls onIn={() => pz.zoomBy(1.25)} onOut={() => pz.zoomBy(0.8)} onFit={pz.fit} />
      <Tooltip info={hover} />
    </div>
  );
}

type Hoverable = (build: () => Omit<HoverInfo, "x" | "y">, partId?: string | null) => Record<string, unknown>;

function Board({ geo, ix, photo, focus, selected, onSelect, hoverable, wireInfo, refPath }: {
  geo: Geometry; ix: WiringIndex; photo: PhotoState; focus: string | null; selected: string | null;
  onSelect: (id: string | null) => (e: React.MouseEvent) => void; hoverable: Hoverable;
  wireInfo: (c: Connection) => Omit<HoverInfo, "x" | "y">; refPath: (id: string) => (el: SVGPathElement | null) => void;
}) {
  const b = geo.board;
  const bd = ix.w.board_drawing!; // Board is only rendered for kits that have one
  const usedBy = (net: string) =>
    [...new Set(ix.w.connections.flatMap((c) => [c.from, c.to]).filter((r) => ix.pin(r)?.pin.gpio === net)
      .map((r) => ix.pin(r)!.part).filter((p) => p.kind !== "soc").map((p) => p.part_number))];
  const sx = (pct: number) => b.x + (pct / 100) * b.w;
  const sy = (pct: number) => b.y + (pct / 100) * b.h;
  return (
    <g>
      <g filter="url(#bb-shadow)">
        {photo === "photo"
          ? <image href={BOARD_PHOTO} x={b.x} y={b.y} width={b.w} height={b.h} preserveAspectRatio="none" />
          : <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={14} fill={PCB} stroke="#000" strokeWidth={1.5} />}
      </g>
      {photo !== "photo" && (
        <g pointerEvents="none">
          <text x={sx(58)} y={sy(11)} fill="#FFFFFF" fontSize={15} fontWeight={700} letterSpacing={1}>SiWx917</text>
          <text x={sx(58)} y={sy(14.5)} fill="#BDBDBD" fontSize={11}>BRD2605A</text>
          {bd.features.filter((f) => f.part === null).map((f) => <Landmark key={f.id} f={f} x={sx(f.x)} y={sy(f.y)} w={(f.w / 100) * b.w} h={(f.h / 100) * b.h} />)}
          <text x={sx(6.7) + 12} y={sy(26.5) + 4} fill="#FFFFFF" fontSize={10}>1</text>
          <text x={sx(91) - 12} y={sy(26.5) + 4} fill="#FFFFFF" fontSize={10} textAnchor="end">2</text>
          <text x={sx(6.7) + 12} y={sy(81) + 4} fill="#FFFFFF" fontSize={10}>25</text>
          <text x={sx(91) - 12} y={sy(81) + 4} fill="#FFFFFF" fontSize={10} textAnchor="end">26</text>
        </g>
      )}

      {geo.pads.map((p) => (
        <g key={p.number} {...hoverable(() => ({
          title: `Pad ${p.number} · ${p.net}`,
          rows: [
            ...(p.fn ? [["Function", p.fn]] : []),
            ...(p.used ? [["Shared with", usedBy(p.net).join(", ")]] : []),
            ["Source", bd.pads_source ?? "UG581"],
          ] as [string, string][],
        }))}>
          {photo === "photo"
            ? <circle cx={p.x} cy={p.y} r={8} fill="transparent" stroke={p.used ? color.accent : "transparent"} strokeWidth={2} />
            : (
              <>
                <circle cx={p.x} cy={p.y} r={7.5} fill={PAD} stroke={p.used ? color.accent : PAD_EDGE} strokeWidth={p.used ? 2.5 : 1} />
                <circle cx={p.x} cy={p.y} r={3} fill={PCB} />
              </>
            )}
        </g>
      ))}

      {geo.traces.map((t) => {
        const lit = focus === t.partId;
        return (
          <g key={t.conn.id} {...hoverable(() => wireInfo(t.conn), t.partId)}>
            <path ref={refPath(t.conn.id)} d={t.d} fill="none" stroke={lit ? color.accent : "#FFFFFF"} strokeOpacity={lit ? 1 : 0.32}
              strokeWidth={lit ? 2.2 : 1.4} strokeDasharray={t.conn.status === "planned" ? "4 4" : undefined} />
            <path d={t.d} fill="none" stroke="transparent" strokeWidth={8} />
          </g>
        );
      })}

      {[...geo.parts.values()].filter((p) => p.onBoard).map((p) => (
        <OnBoardPart key={p.part.id} placed={p} photo={photo} geo={geo} selected={selected === p.part.id} hovered={focus === p.part.id}
          onClick={onSelect(p.part.id)} hoverable={hoverable} ix={ix} />
      ))}

      {/* Dimensions from UG581 Figure 1.1. */}
      <g stroke={color.ink2} strokeWidth={1} fontSize={12} fill={color.ink2} pointerEvents="none">
        <path d={`M${b.x},${b.y - 30} H${b.x + b.w} M${b.x},${b.y - 36} V${b.y - 24} M${b.x + b.w},${b.y - 36} V${b.y - 24}`} />
        <text x={b.x + b.w / 2} y={b.y - 38} textAnchor="middle" stroke="none">{bd.width_mm.toFixed(1)} mm</text>
        <path d={`M${b.x + b.w + 30},${b.y} V${b.y + b.h} M${b.x + b.w + 24},${b.y} H${b.x + b.w + 36} M${b.x + b.w + 24},${b.y + b.h} H${b.x + b.w + 36}`} />
        <text x={b.x + b.w + 46} y={b.y + b.h / 2} textAnchor="middle" stroke="none"
          transform={`rotate(90 ${b.x + b.w + 46} ${b.y + b.h / 2})`}>{bd.height_mm.toFixed(1)} mm</text>
      </g>
      <text x={b.x + b.w / 2} y={b.y + b.h + 30} textAnchor="middle" fontSize={13} fontWeight={600} fill={color.ink}>{ix.w.board} dev kit</text>
      <text x={b.x + b.w / 2} y={b.y + b.h + 48} textAnchor="middle" fontSize={12} fill={color.ink2}>
        {photo === "photo" ? "Photo: frontend/public/board/top.jpg" : "Outline from UG581 Fig. 1.1 · board photo not added yet"}
      </text>
    </g>
  );
}

function Landmark({ f, x, y, w, h }: { f: { kind: string; label: string }; x: number; y: number; w: number; h: number }) {
  const label = (dy: number) => <text x={x + w / 2} y={y + dy} textAnchor="middle" fill="#FFFFFF" fontSize={10} fontWeight={600}>{f.label}</text>;
  switch (f.kind) {
    case "button":
      return (
        <g>
          <rect x={x} y={y} width={w} height={h} rx={5} fill="#D6D6D6" stroke="#9E9E9E" />
          <rect x={x + w * 0.2} y={y + h * 0.22} width={w * 0.6} height={h * 0.56} rx={h * 0.28} fill="#2E2E2E" />
          {label(-5)}
        </g>
      );
    case "led":
      return <g><rect x={x} y={y} width={w} height={h} rx={1.5} fill="#F2F2F2" />{label(-6)}</g>;
    case "switch":
      return (
        <g>
          <rect x={x} y={y} width={w} height={h} rx={2} fill="#F2F2F2" />
          <rect x={x + w * 0.42} y={y + h * 0.25} width={w * 0.2} height={h * 0.5} fill="#2E2E2E" />
          {label(-5)}
        </g>
      );
    case "connector":
      return (
        <g>
          <rect x={x} y={y} width={w} height={h} rx={5} fill="#CFCFCF" stroke="#8E8E8E" />
          <rect x={x + w * 0.12} y={y + h * 0.2} width={w * 0.76} height={h * 0.3} rx={3} fill="#9A9A9A" />
          <text x={x + w / 2} y={y + h * 0.78} textAnchor="middle" fill="#3A3A3A" fontSize={11} fontWeight={600}>{f.label}</text>
        </g>
      );
    default:
      return <g><rect x={x} y={y} width={w} height={h} rx={1.5} fill="#EDEDED" /><text x={x + w + 4} y={y + h - 2} fill="#BDBDBD" fontSize={9}>{f.label}</text></g>;
  }
}

function OnBoardPart({ placed, photo, geo, ix, selected, hovered, onClick, hoverable }: {
  placed: PlacedPart; photo: PhotoState; geo: Geometry; ix: WiringIndex; selected: boolean; hovered: boolean;
  onClick: (e: React.MouseEvent) => void; hoverable: Hoverable;
}) {
  const { part: p, box: b } = placed;
  const f = ix.feature(p.id);
  const drawn = photo !== "photo";
  const stroke = selected ? color.accent : hovered ? "#FF6A73" : statusStroke[p.status];
  const pins = [...geo.pins.values()].filter((q) => q.part.id === p.id);
  return (
    <g onClick={onClick} className="cursor-pointer" {...hoverable(() => ({
      title: p.name,
      rows: [
        ["Part", p.part_number], ["Status", `${statusLabel[p.status]} · ${p.status === "wired" ? "connected by the board" : statusHelp[p.status].toLowerCase()}`],
        ...(p.bus ? [["Bus", ix.busName(p.bus)]] : []), ...(p.address ? [["Address", ix.address(p)]] : []),
        ...(placed.approx ? [["Position", "approx., from UG581 Fig. 1.1"]] : []),
      ] as [string, string][],
    }), p.id)}>
      {drawn && f?.kind === "connector" && (
        <g>
          <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={3} fill="#E8DDBF" stroke="#B9A877" />
          {[0.2, 0.4, 0.6, 0.8].map((t) => <rect key={t} x={b.x + b.w * 0.35} y={b.y + b.h * t - 3} width={b.w * 0.45} height={6} rx={1} fill="#B59A55" />)}
        </g>
      )}
      {drawn && f?.kind !== "connector" && (
        <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={2} fill="#101010" stroke="#3C3C3C" />
      )}
      {drawn && f && f.kind !== "connector" && b.w > 50 && (
        <text x={b.x + b.w / 2} y={b.y + b.h / 2 + 4} textAnchor="middle" fill="#9A9A9A" fontSize={11} fontWeight={600}>{f.label}</text>
      )}
      <rect x={b.x - 4} y={b.y - 4} width={b.w + 8} height={b.h + 8} rx={5} fill={selected || hovered ? "#D91E2A22" : "transparent"}
        stroke={stroke} strokeWidth={selected ? 3 : 2} strokeDasharray={p.status === "planned" || (photo === "photo" && placed.approx) ? "5 4" : undefined} />
      {pins.map((q) => (
        <g key={q.ref} {...hoverable(() => ({
          title: `${p.part_number} · ${q.pin.name}`,
          rows: [["Signal", q.pin.signal], ["Bus", ix.busName(p.bus)], ...(q.pin.gpio ? [["SoC pin", q.pin.gpio]] : []),
            ...(p.address ? [["Address", ix.address(p)]] : []), ["Evidence", q.pin.evidence]] as [string, string][],
        }), p.id)}>
          <circle cx={q.x} cy={q.y} r={3.5} fill={PAD} stroke={PAD_EDGE} />
          <circle cx={q.x} cy={q.y} r={8} fill="transparent" />
        </g>
      ))}
    </g>
  );
}

function ExternalPart({ placed, geo, ix, readings, online, selected, hovered, onClick, hoverable }: {
  placed: PlacedPart; geo: Geometry; ix: WiringIndex; readings: PartReadings | undefined; online: boolean;
  selected: boolean; hovered: boolean; onClick: (e: React.MouseEvent) => void; hoverable: Hoverable;
}) {
  const { part: p, box: b } = placed;
  const planned = p.status === "planned";
  const transducer = p.kind === "transducer";
  const fill = planned ? "#F1F1F1" : transducer ? "#D4D4D4" : "#2E2E2E";
  const ink = planned ? color.ink2 : transducer ? color.ink : "#FFFFFF";
  const sub = planned ? color.idle : transducer ? color.ink2 : "#BDBDBD";
  const edge = selected ? color.accent : hovered ? "#FF6A73" : planned ? PLANNED : transducer ? "#9E9E9E" : "#111111";
  const pins = [...geo.pins.values()].filter((q) => q.part.id === p.id);
  const reading = readingLine(readings, online);
  const textX = b.x + 16;
  const titleY = transducer ? b.y + 44 : b.y + 42;
  return (
    <g onClick={onClick} className="cursor-pointer" {...hoverable(() => ({
      title: `${p.part_number} · ${p.name}`,
      rows: [["Status", `${statusLabel[p.status]} · ${statusHelp[p.status].toLowerCase()}`],
        ...(p.bus ? [["Bus", ix.busName(p.bus)]] : []), ...(p.address ? [["Address", ix.address(p)]] : [])] as [string, string][],
    }), p.id)}>
      <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={transducer ? 6 : 10} fill={fill} stroke={edge}
        strokeWidth={selected ? 3 : planned ? 1.6 : 1.2} strokeDasharray={planned ? "7 5" : undefined}
        filter={planned ? undefined : "url(#bb-shadow)"} />
      {!transducer && [[10, 10], [b.w - 10, 10], [10, b.h - 10], [b.w - 10, b.h - 10]].map(([dx, dy]) => (
        <circle key={`${dx},${dy}`} cx={b.x + dx!} cy={b.y + dy!} r={3.5} fill={planned ? "#FFFFFF" : "#1A1A1A"} stroke={planned ? PLANNED : "#555"} />
      ))}
      {transducer && <rect x={b.x + b.w / 2 - 28} y={b.y + 8} width={56} height={14} rx={2} fill={planned ? "#E4E4E4" : "#BDBDBD"} />}
      {placed.connectors.map((c) => (
        <g key={c.name}>
          <rect {...c.box} rx={3} fill={planned ? "#FFFFFF" : "#E8DDBF"} stroke={planned ? PLANNED : "#B9A877"}
            strokeDasharray={planned ? "3 3" : undefined} />
        </g>
      ))}
      <text x={textX} y={titleY} fontSize={16} fontWeight={700} fill={ink}>{p.part_number.length > 26 ? p.name : p.part_number}</text>
      <text x={textX} y={titleY + 17} fontSize={12} fill={sub}>{p.part_number.length > 26 ? p.part_number : p.name}</text>
      {!transducer && (
        <text x={textX} y={titleY + 38} fontSize={12} fontWeight={600} fill={planned ? color.ink2 : reading.fill}>
          {planned ? "Not connected yet" : reading.text}
        </text>
      )}
      {transducer && planned && <text x={textX} y={titleY + 34} fontSize={12} fontWeight={600} fill={color.ink2}>Not connected yet</text>}
      {pins.map((q) => {
        const lx = q.side === "right" ? q.x - 10 : q.x;
        const ly = q.side === "top" ? q.y + 15 : q.side === "bottom" ? q.y - 8 : q.y + 3.5;
        return (
          <g key={q.ref} {...hoverable(() => ({
            title: `${p.part_number} · ${pinShort(q.pin.name)}${q.pin.name.includes(".") ? ` (${q.pin.name.split(".")[0]!.replace("_", " ")})` : ""}`,
            rows: [["Signal", q.pin.signal], ["Bus", ix.busName(p.bus)], ...(p.address ? [["Address", ix.address(p)]] : []),
              ["Evidence", q.pin.evidence]] as [string, string][],
          }), p.id)}>
            <text x={lx} y={ly} fontSize={9.5} fontWeight={600} fill={planned ? color.ink2 : color.ink}
              textAnchor={q.side === "right" ? "end" : "middle"}>{pinShort(q.pin.name)}</text>
            <circle cx={q.x} cy={q.y} r={4.5} fill={PAD} stroke={PAD_EDGE} />
            <circle cx={q.x} cy={q.y} r={9} fill="transparent" />
          </g>
        );
      })}
    </g>
  );
}

function readingLine(r: PartReadings | undefined, online: boolean): { text: string; fill: string; live: boolean } {
  if (!r || r.topics.length === 0) return { text: "No readings of its own", fill: color.ink2, live: false };
  const have = r.topics.filter((t) => t.reading);
  if (have.length === 0) return { text: WAITING, fill: color.ink2, live: false };
  const text = have.map((t) => formatReading(t.reading!)).join(" · ");
  return online
    ? { text, fill: color.live, live: true }
    : { text: `${text} · ${ago(r.latest_ms!)}`, fill: color.idle, live: false };
}

function Callout({ x, y, anchor, placed, readings, online, active, onClick }: {
  x: number; y: number; anchor: [number, number]; placed: PlacedPart; readings: PartReadings | undefined; online: boolean;
  active: boolean; onClick: (e: React.MouseEvent) => void;
}) {
  const p = placed.part;
  const r = readingLine(readings, online);
  const w = 250;
  const h = 66;
  const [ax, ay] = anchor;
  return (
    <g onClick={onClick} className="cursor-pointer">
      <path d={`M${ax + 4},${ay} H${ax + 22} L${x - 12},${y + h / 2} H${x}`} fill="none" stroke={active ? color.accent : "#9E9E9E"} strokeWidth={active ? 1.6 : 1} />
      <circle cx={ax + 4} cy={ay} r={2.5} fill={active ? color.accent : "#9E9E9E"} />
      <rect x={x} y={y} width={w} height={h} rx={10} fill="#FFFFFF" stroke={active ? color.accent : color.cardBorder} strokeWidth={active ? 1.6 : 1} />
      <circle cx={x + 16} cy={y + 20} r={4} fill={p.status === "verified" ? color.ok : p.status === "wired" ? color.ink : PLANNED} />
      <text x={x + 28} y={y + 24} fontSize={14} fontWeight={600} fill={color.ink}>{p.name}</text>
      <text x={x + 28} y={y + 41} fontSize={11.5} fill={color.ink2}>{p.part_number} · {statusLabel[p.status]}</text>
      <text x={x + 28} y={y + 57} fontSize={12} fontWeight={r.live ? 600 : 500} fill={r.fill}>
        {r.live && <tspan fontSize={9.5} fontWeight={700} fill={color.live}>LIVE  </tspan>}{r.text}
      </text>
    </g>
  );
}

/** Watches each part's latest reading time and queues a pulse when a newer one arrives. */
function usePulses(readings: Record<string, PartReadings>) {
  const prev = useRef<Record<string, number | null> | null>(null);
  const [list, setList] = useState<{ key: string; partId: string }[]>([]);
  useEffect(() => {
    const now: Record<string, number | null> = {};
    for (const [id, r] of Object.entries(readings)) now[id] = r.latest_ms;
    const before = prev.current;
    prev.current = now;
    if (!before) return; // first render: values that were already there are not "arriving"
    const fresh = Object.entries(now).filter(([id, t]) => t !== null && t !== before[id]).map(([id, t]) => ({ key: `${id}-${t}`, partId: id }));
    if (fresh.length) setList((l) => [...l, ...fresh]);
  }, [readings]);
  return { list, remove: (key: string) => setList((l) => l.filter((p) => p.key !== key)) };
}

const PULSE_MS = 900;

function Pulse({ steps, els, onDone }: { steps: { conn: Connection; reverse: boolean }[]; els: React.RefObject<Map<string, SVGPathElement>>; onDone: () => void }) {
  const dot = useRef<SVGCircleElement>(null);
  useEffect(() => {
    const segs = steps.map((s) => ({ el: els.current.get(s.conn.id), reverse: s.reverse })).filter((s): s is { el: SVGPathElement; reverse: boolean } => !!s.el);
    if (segs.length === 0) { onDone(); return; }
    const lens = segs.map((s) => s.el.getTotalLength());
    const total = lens.reduce((a, b) => a + b, 0);
    const t0 = performance.now();
    let raf = 0;
    const frame = (t: number) => {
      const k = Math.min(1, (t - t0) / PULSE_MS);
      let d = k * total;
      let i = 0;
      while (i < segs.length - 1 && d > lens[i]!) { d -= lens[i]!; i++; }
      const s = segs[i]!;
      const pt = s.el.getPointAtLength(s.reverse ? lens[i]! - d : d);
      dot.current?.setAttribute("cx", String(pt.x));
      dot.current?.setAttribute("cy", String(pt.y));
      dot.current?.setAttribute("opacity", String(k < 0.85 ? 1 : (1 - k) / 0.15));
      if (k < 1) raf = requestAnimationFrame(frame);
      else onDone();
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once per pulse
  }, []);
  return <circle ref={dot} r={6} fill={color.live} stroke="#FFFFFF" strokeWidth={2} pointerEvents="none" data-export-skip />;
}
