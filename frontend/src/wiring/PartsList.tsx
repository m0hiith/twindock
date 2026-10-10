// Parts list: every part with part number, quantity, location, bus, address and status. The
// on-screen table is HTML; a matching SVG (hidden) is what Export PNG / PDF renders.
import { color } from "../theme";
import { kindLabel, statusLabel, type Part, type WiringIndex } from "./model";
import { StatusBadge, FONT } from "./ui";

const COLS = ["Part", "Part number", "Qty", "Location", "Bus", "Address", "Status"] as const;

function row(ix: WiringIndex, p: Part): string[] {
  return [p.name, p.part_number, String(p.quantity), p.location === "on-board" ? "On board" : "External", ix.busName(p.bus), ix.address(p), statusLabel[p.status]];
}

export function PartsList({ ix, selected, onSelect, svgRef }: {
  ix: WiringIndex; selected: string | null; onSelect: (id: string) => void; svgRef: (el: SVGSVGElement | null) => void;
}) {
  return (
    <div className="h-full overflow-auto rounded-[14px] bg-white">
      <table className="w-full border-collapse text-left text-[14px]">
        <thead className="sticky top-0 bg-white">
          <tr className="border-b border-[var(--card-border)] text-[13px] text-ink-2">
            {COLS.map((c) => <th key={c} className="px-4 py-3 font-medium">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {ix.w.parts.map((p) => (
            <tr key={p.id} onClick={() => onSelect(p.id)} aria-selected={selected === p.id}
              className={`cursor-pointer border-b border-[var(--card-border)] align-top transition-colors hover:bg-idle-bg ${selected === p.id ? "bg-crit-bg/40" : ""} ${p.status === "planned" ? "text-ink-2" : ""}`}>
              <td className="px-4 py-3">
                <div className="font-semibold text-ink">{p.name}</div>
                <div className="mt-0.5 max-w-[420px] text-[13px] text-ink-2">{p.caption}</div>
              </td>
              <td className="px-4 py-3 font-medium">{p.part_number}</td>
              <td className="tabular px-4 py-3">{p.quantity}</td>
              <td className="px-4 py-3">{p.location === "on-board" ? "On board" : "External"}<div className="text-[12px] text-ink-2">{kindLabel[p.kind]}</div></td>
              <td className="px-4 py-3">{ix.busName(p.bus)}</td>
              <td className="tabular px-4 py-3">{ix.address(p)}</td>
              <td className="px-4 py-3">
                <StatusBadge status={p.status} />
                {p.status === "planned" && <div className="mt-1 text-[12px] text-ink-2">Not connected yet</div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <PartsTableSvg ix={ix} svgRef={svgRef} />
    </div>
  );
}

/** Export-only rendering of the same table. */
function PartsTableSvg({ ix, svgRef }: { ix: WiringIndex; svgRef: (el: SVGSVGElement | null) => void }) {
  const widths = [500, 220, 50, 110, 230, 170, 100];
  const xs = widths.map((_, i) => 20 + widths.slice(0, i).reduce((a, b) => a + b, 0));
  const rowH = 58;
  const W = xs.at(-1)! + widths.at(-1)! + 20;
  const H = 60 + ix.w.parts.length * rowH + 20;
  return (
    <svg ref={svgRef} className="hidden" width={W} height={H} viewBox={`0 0 ${W} ${H}`} fontFamily={FONT} data-full-w={W} data-full-h={H}>
      <rect width={W} height={H} fill="#FFFFFF" />
      {COLS.map((c, i) => <text key={c} x={xs[i]} y={36} fontSize={13} fill={color.ink2}>{c}</text>)}
      <line x1={20} x2={W - 20} y1={50} y2={50} stroke={color.cardBorder} />
      {ix.w.parts.map((p, r) => {
        const y = 60 + r * rowH;
        const cells = row(ix, p);
        const ink = p.status === "planned" ? color.ink2 : color.ink;
        return (
          <g key={p.id}>
            {cells.map((v, i) => (
              <text key={i} x={xs[i]} y={y + 22} fontSize={14} fontWeight={i === 0 ? 600 : 400} fill={i === 6 ? statusFill(p.status) : ink}>
                {clip(v, Math.floor(widths[i]! / 8))}
              </text>
            ))}
            <text x={xs[0]} y={y + 40} fontSize={12} fill={color.ink2}>{clip(p.caption, 78)}</text>
            <line x1={20} x2={W - 20} y1={y + rowH - 2} y2={y + rowH - 2} stroke={color.cardBorder} />
          </g>
        );
      })}
    </svg>
  );
}

const statusFill = (s: Part["status"]) => (s === "verified" ? color.ok : s === "wired" ? color.ink : color.idle);
const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);
