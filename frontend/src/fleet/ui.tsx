// Small fleet widgets: signal bars, a history sparkline and a site mini-map.
import type { Device, Site } from "../contract";
import type { Layout } from "../layout";
import { deviceTone, toneColor } from "../status";
import { color } from "../theme";
import { signalBars } from "./logic";

export function SignalBars({ rssi }: { rssi: number | null | undefined }) {
  const n = signalBars(rssi);
  return (
    <span className="flex items-center gap-1.5" title={rssi === null || rssi === undefined ? "No signal reported" : `${rssi} dBm`}>
      <span className="flex h-3.5 items-end gap-[2px]" aria-hidden="true">
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className="w-[3px] rounded-sm" style={{ height: `${i * 25}%`, background: i <= n ? color.ink : color.cardBorder }} />
        ))}
      </span>
      <span className="tabular text-[12px] text-ink-2">{rssi ?? "—"}</span>
    </span>
  );
}

/** Line chart of [ms, value] points with min/max labels. Booleans (0/1) draw as steps. */
export function Sparkline({ points, unit, step = false, height = 96 }: { points: [number, number][]; unit?: string; step?: boolean; height?: number }) {
  const W = 340, H = height, pad = { l: 36, r: 6, t: 8, b: 16 };
  if (points.length < 2) {
    return <div className="grid place-items-center rounded-lg bg-[#F8F8F8] text-[12px] text-ink-2" style={{ height: H }}>Collecting history…</div>;
  }
  const t0 = points[0]![0], t1 = points.at(-1)![0];
  let lo = Math.min(...points.map((p) => p[1])), hi = Math.max(...points.map((p) => p[1]));
  if (hi - lo < 1e-6) { lo -= 1; hi += 1; }
  const x = (t: number) => pad.l + ((t - t0) / Math.max(1, t1 - t0)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - lo) / (hi - lo)) * (H - pad.t - pad.b);
  let d = "";
  points.forEach(([t, v], i) => {
    if (i === 0) d += `M${x(t)},${y(v)}`;
    else d += step ? `H${x(t)}V${y(v)}` : `L${x(t)},${y(v)}`;
  });
  const fmt = (v: number) => (step ? (v >= 0.5 ? "1" : "0") : Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1));
  const mins = Math.round((t1 - t0) / 60000);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Recent history">
      <line x1={pad.l} x2={W - pad.r} y1={y(hi)} y2={y(hi)} stroke={color.cardBorder} />
      <line x1={pad.l} x2={W - pad.r} y1={y(lo)} y2={y(lo)} stroke={color.cardBorder} />
      <text x={pad.l - 4} y={y(hi) + 4} textAnchor="end" fontSize="10" fill={color.ink2}>{fmt(hi)}</text>
      <text x={pad.l - 4} y={y(lo) + 4} textAnchor="end" fontSize="10" fill={color.ink2}>{fmt(lo)}</text>
      <path d={d} fill="none" stroke={color.ink} strokeWidth="1.6" strokeLinejoin="round" />
      <text x={W - pad.r} y={H - 2} textAnchor="end" fontSize="10" fill={color.ink2}>now</text>
      <text x={pad.l} y={H - 2} fontSize="10" fill={color.ink2}>{mins ? `${mins} min ago` : "<1 min ago"}{unit ? ` · ${unit}` : ""}</text>
    </svg>
  );
}

/** Top-down sketch of one site: buildings, zones, and the device as a ring in its status tone. */
export function MiniMap({ layout, site, device, others }: { layout: Layout; site: Site; device: Device; others: Device[] }) {
  const [x0, x1] = site.bounds.x, [z0, z1] = site.bounds.z;
  const W = 340, H = Math.round((W * (z1 - z0)) / (x1 - x0));
  const sx = (x: number) => ((x - x0) / (x1 - x0)) * W;
  const sz = (z: number) => ((z - z0) / (z1 - z0)) * H;
  const tone = toneColor[deviceTone(device)].fg;
  const inSite = (b: { x: number; z: number; w: number; d: number }) => b.x + b.w > x0 && b.x < x1 && b.z + b.d > z0 && b.z < z1;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-lg bg-[#F4F4F4]" role="img" aria-label={`${device.id} on the ${site.name} map`}>
      {site.zones.map((z) => (
        <polygon key={z.id} points={z.polygon.map(([x, zz]) => `${sx(x)},${sz(zz)}`).join(" ")}
          fill={z.id === device.zone_id ? "rgba(217,30,42,0.07)" : "none"} stroke={color.marking} strokeWidth="1" />
      ))}
      {layout.buildings.filter(inSite).map((b) => (
        <rect key={b.id} x={sx(b.x)} y={sz(b.z)} width={sx(b.x + b.w) - sx(b.x)} height={sz(b.z + b.d) - sz(b.z)}
          fill="none" stroke={b.kind === "cold_room" ? color.ink2 : color.structure} strokeWidth="1.2" />
      ))}
      {others.map((o) => <circle key={o.id} cx={sx(o.x)} cy={sz(o.z)} r="2.2" fill={color.idle} />)}
      <circle cx={sx(device.x)} cy={sz(device.z)} r="8" fill="none" stroke={tone} strokeWidth="2" />
      <circle cx={sx(device.x)} cy={sz(device.z)} r="3" fill={tone} />
    </svg>
  );
}

/** Vibration (or any value) over time with a shaded "normal" band (baseline mean ± k·std). */
export function BandChart({ points, band, mean, unit, height = 110 }: {
  points: [number, number][]; band: [number, number] | null; mean: number | null; unit?: string; height?: number;
}) {
  const W = 300, H = height, pad = { l: 34, r: 6, t: 8, b: 16 };
  if (points.length < 2) {
    return <div className="grid place-items-center rounded-lg bg-[#F8F8F8] text-[12px] text-ink-2" style={{ height: H }}>Collecting history…</div>;
  }
  const vals = points.map((p) => p[1]).concat(band ? [band[0], band[1]] : []);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const padV = (hi - lo) * 0.1 || 0.5;
  lo -= padV; hi += padV;
  const t0 = points[0]![0], t1 = points.at(-1)![0];
  const x = (t: number) => pad.l + ((t - t0) / Math.max(1, t1 - t0)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - lo) / (hi - lo)) * (H - pad.t - pad.b);
  const d = points.map(([t, v], i) => `${i ? "L" : "M"}${x(t)},${y(v)}`).join("");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Vibration with its baseline band">
      {band && <rect x={pad.l} width={W - pad.l - pad.r} y={y(band[1])} height={Math.max(1, y(band[0]) - y(band[1]))} fill={color.okBg} />}
      {mean !== null && <line x1={pad.l} x2={W - pad.r} y1={y(mean)} y2={y(mean)} stroke={color.ok} strokeDasharray="3 3" />}
      <path d={d} fill="none" stroke={color.ink} strokeWidth="1.5" strokeLinejoin="round" />
      <text x={pad.l - 4} y={y(hi) + 10} textAnchor="end" fontSize="10" fill={color.ink2}>{hi.toFixed(1)}</text>
      <text x={pad.l - 4} y={y(lo)} textAnchor="end" fontSize="10" fill={color.ink2}>{lo.toFixed(1)}</text>
      <text x={pad.l} y={H - 2} fontSize="10" fill={color.ink2}>{band ? "Green band: learned baseline" : "Learning baseline…"}{unit ? ` · ${unit}` : ""}</text>
      <text x={W - pad.r} y={H - 2} textAnchor="end" fontSize="10" fill={color.ink2}>now</text>
    </svg>
  );
}
