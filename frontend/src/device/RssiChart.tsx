// Smoothed RSSI of one tag over time, from real scans only, with the zone thresholds drawn as
// reference lines. Hover shows the reading under the cursor.
import { useState } from "react";
import { nodeLabel } from "../hud/ui";

interface Point { t: number; avg: number; raw: number }

const W = 520, H = 150, PAD = { l: 34, r: 64, t: 8, b: 18 };

export function RssiChart({ points, zones, windowMs }: { points: Point[]; zones: { node: string; min_rssi_dbm: number }[]; windowMs: number }) {
  const [hover, setHover] = useState<number | null>(null);
  if (points.length === 0) return <div className="grid h-[150px] place-items-center rounded-lg bg-idle-bg text-ink-2">Waiting for scans</div>;

  const t1 = points.at(-1)!.t, t0 = t1 - windowMs;
  const vals = [...points.map((p) => p.avg), ...points.map((p) => p.raw), ...zones.map((z) => z.min_rssi_dbm)];
  const lo = Math.floor((Math.min(...vals) - 3) / 10) * 10, hi = Math.ceil((Math.max(...vals) + 3) / 10) * 10;
  const x = (t: number) => PAD.l + ((t - t0) / windowMs) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + ((hi - v) / (hi - lo)) * (H - PAD.t - PAD.b);
  const shown = points.filter((p) => p.t >= t0);
  const ticks: number[] = [];
  for (let v = hi; v >= lo; v -= 10) ticks.push(v);
  const h = hover !== null ? shown[hover] : undefined;

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    let best = 0;
    shown.forEach((p, i) => { if (Math.abs(x(p.t) - px) < Math.abs(x(shown[best]!.t) - px)) best = i; });
    setHover(best);
  };

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full touch-none" onPointerMove={onMove} onPointerLeave={() => setHover(null)}
        role="img" aria-label={`Smoothed RSSI, latest ${points.at(-1)!.avg} dBm`}>
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(v)} y2={y(v)} stroke="var(--card-border)" />
            <text x={PAD.l - 6} y={y(v)} fontSize={10} fill="var(--ink-2)" textAnchor="end" dominantBaseline="central">{v}</text>
          </g>
        ))}
        {zones.map((z) => (
          <g key={z.node}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(z.min_rssi_dbm)} y2={y(z.min_rssi_dbm)} stroke="var(--ink-2)" strokeDasharray="4 3" />
            <text x={W - PAD.r + 4} y={y(z.min_rssi_dbm)} fontSize={10} fill="var(--ink-2)" dominantBaseline="central">{nodeLabel(z.node)}</text>
          </g>
        ))}
        {shown.map((p) => <circle key={p.t} cx={x(p.t)} cy={y(p.raw)} r={2} fill="var(--idle)" opacity={0.6} />)}
        <polyline points={shown.map((p) => `${x(p.t)},${y(p.avg)}`).join(" ")} fill="none" stroke="var(--live)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {h && (
          <g>
            <line x1={x(h.t)} x2={x(h.t)} y1={PAD.t} y2={H - PAD.b} stroke="var(--ink-2)" strokeOpacity={0.4} />
            <circle cx={x(h.t)} cy={y(h.avg)} r={4} fill="var(--live)" stroke="#fff" strokeWidth={2} />
          </g>
        )}
        <text x={PAD.l} y={H - 4} fontSize={10} fill="var(--ink-2)">−{Math.round(windowMs / 60000)} min</text>
        <text x={W - PAD.r} y={H - 4} fontSize={10} fill="var(--ink-2)" textAnchor="end">now</text>
      </svg>
      {h && (
        <div className="pointer-events-none absolute right-2 top-1 rounded-lg border border-[var(--card-border)] bg-white px-2 py-1 text-[12px] shadow-[var(--card-shadow)]">
          <span className="tabular font-semibold">{h.avg.toFixed(1)} dBm</span> <span className="text-ink-2">smoothed · raw {h.raw}</span>
        </div>
      )}
      <div className="mt-1 flex gap-4 text-[12px] text-ink-2">
        <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 rounded bg-live" />Smoothed</span>
        <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-idle" />Raw reading</span>
        {zones.length > 0 && <span className="flex items-center gap-1.5"><span className="w-4 border-t border-dashed border-ink-2" />Zone threshold</span>}
      </div>
    </div>
  );
}
