// Larger parts: sensor windows, relays, cells, clamps, load cells, switches, domes, buzzers, probes, meters.
import { useId } from "react";
import { GOLD, PLASTIC_BLACK, TIN, TIN_DARK } from "./palette";
import { countOf, type Spec } from "./types";

const MONO = "ui-monospace, Menlo, monospace";

export function SensorWindow({ w, h, s, variant = "tof" }: Spec) {
  const id = useId();
  if (variant === "gas") {
    // Electrochemical / MOX gas sensor: metal can with a perforated mesh cap.
    const r = Math.min(w, h) / 2;
    const dots: [number, number][] = [];
    for (let y = -4; y <= 4; y++) for (let x = -4; x <= 4; x++) if (Math.hypot(x, y) <= 3.6) dots.push([x, y]);
    return (
      <g>
        <defs><radialGradient id={id} cx="0.4" cy="0.35"><stop offset="0" stopColor="#F2F3F5" /><stop offset="1" stopColor={TIN_DARK} /></radialGradient></defs>
        <circle cx={w / 2} cy={h / 2} r={r} fill={`url(#${id})`} stroke="#5A5F65" strokeWidth={s * 0.14} />
        <circle cx={w / 2} cy={h / 2} r={r * 0.72} fill="#3A3D41" />
        {dots.map(([x, y]) => <circle key={`${x}${y}`} cx={w / 2 + x * r * 0.17} cy={h / 2 + y * r * 0.17} r={r * 0.045} fill="#C9CDD2" />)}
      </g>
    );
  }
  if (variant === "mic") {
    return (
      <g>
        <rect width={w} height={h} rx={s * 0.2} fill="#BFC3C8" stroke={TIN_DARK} strokeWidth={s * 0.08} />
        <circle cx={w / 2} cy={h / 2} r={Math.min(w, h) * 0.26} fill="#0C0C0E" stroke="#6D7279" strokeWidth={s * 0.1} />
      </g>
    );
  }
  if (variant === "light") {
    return (
      <g>
        <rect width={w} height={h} rx={s * 0.1} fill="#D5D8DC" stroke={TIN_DARK} strokeWidth={s * 0.06} />
        <rect x={w * 0.2} y={h * 0.2} width={w * 0.6} height={h * 0.6} rx={s * 0.08} fill="#2B3036" stroke="#000" strokeWidth={s * 0.05} />
      </g>
    );
  }
  // Time-of-flight: dark glass window over an emitter lens (left) and a receiver lens (right).
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.2} fill="#D8DADD" stroke={TIN_DARK} strokeWidth={s * 0.08} />
      <rect x={w * 0.07} y={h * 0.14} width={w * 0.86} height={h * 0.72} rx={s * 0.12} fill="#16181B" stroke="#000" strokeWidth={s * 0.05} />
      <circle cx={w * 0.3} cy={h * 0.5} r={Math.min(w, h) * 0.2} fill="#2A2F36" stroke="#4A5058" strokeWidth={s * 0.06} />
      <rect x={w * 0.56} y={h * 0.3} width={w * 0.28} height={h * 0.4} rx={s * 0.08} fill="#2A2F36" stroke="#4A5058" strokeWidth={s * 0.06} />
      <circle cx={w * 0.26} cy={h * 0.44} r={Math.min(w, h) * 0.04} fill="#FFFFFF" opacity={0.35} />
    </g>
  );
}

export function PirDome({ w, h, s }: Spec) {
  const r = Math.min(w, h) / 2;
  return (
    <g>
      <circle cx={w / 2} cy={h / 2} r={r} fill="#EFEFEA" stroke="#B9B9B2" strokeWidth={s * 0.12} />
      {Array.from({ length: 8 }, (_, i) => {
        const a = (Math.PI * 2 * i) / 8;
        return <line key={i} x1={w / 2} y1={h / 2} x2={w / 2 + Math.cos(a) * r} y2={h / 2 + Math.sin(a) * r} stroke="#C9C9C1" strokeWidth={s * 0.1} />;
      })}
      <circle cx={w / 2} cy={h / 2} r={r * 0.5} fill="none" stroke="#C9C9C1" strokeWidth={s * 0.1} />
      <circle cx={w / 2} cy={h / 2} r={r * 0.16} fill="#DADAD2" />
    </g>
  );
}

export function Buzzer({ w, h, s }: Spec) {
  const r = Math.min(w, h) / 2;
  return (
    <g>
      <circle cx={w / 2} cy={h / 2} r={r} fill="#1D1D20" stroke="#000" strokeWidth={s * 0.1} />
      <circle cx={w / 2} cy={h / 2} r={r * 0.82} fill="none" stroke="#3A3A3F" strokeWidth={s * 0.08} />
      <circle cx={w / 2} cy={h / 2} r={r * 0.16} fill="#050506" />
      <text x={w / 2 - r * 0.74} y={h / 2 - r * 0.45} fontSize={s * 1.2} fill="#BBB" fontFamily={MONO}>+</text>
    </g>
  );
}

export function Relay({ w, h, s, label }: Spec) {
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.3} fill="#3A3A3E" stroke="#000" strokeWidth={s * 0.1} />
      <rect x={s * 0.5} y={s * 0.5} width={w - s} height={h - s} rx={s * 0.2} fill="#2B2B2F" />
      <rect x={w * 0.12} y={h * 0.16} width={w * 0.76} height={h * 0.26} rx={s * 0.1} fill="#D9D9D4" />
      <text x={w / 2} y={h * 0.55} textAnchor="middle" fontSize={Math.min(h * 0.18, s * 1.6)} fill="#E2E2DD" fontFamily={MONO}>{label ?? "RELAY"}</text>
      {[0.14, 0.5, 0.86].map((x) => <circle key={x} cx={w * x} cy={h * 0.88} r={s * 0.35} fill={TIN} stroke={TIN_DARK} strokeWidth={s * 0.05} />)}
    </g>
  );
}

export function TerminalBlock({ w, h, s, variant }: Spec) {
  const n = countOf(variant, 4);
  const pole = w / n;
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.3} fill="#C9CCD0" stroke="#7B8086" strokeWidth={s * 0.12} />
      {Array.from({ length: n }, (_, i) => {
        const x = i * pole;
        return (
          <g key={i}>
            <rect x={x + s * 0.2} y={s * 0.3} width={pole - s * 0.4} height={h - s * 0.6} rx={s * 0.15} fill="#E6E8EA" stroke="#9A9FA5" strokeWidth={s * 0.06} />
            <circle cx={x + pole / 2} cy={h * 0.3} r={Math.min(pole, h) * 0.2} fill={TIN} stroke={TIN_DARK} strokeWidth={s * 0.07} />
            <path d={`M${x + pole * 0.3},${h * 0.3} h${pole * 0.4}`} stroke="#555B61" strokeWidth={s * 0.2} />
            <rect x={x + pole * 0.25} y={h * 0.62} width={pole * 0.5} height={h * 0.26} rx={s * 0.1} fill="#25282C" />
          </g>
        );
      })}
    </g>
  );
}

export function CoinCellHolder({ w, h, s }: Spec) {
  const id = useId();
  const r = Math.min(w, h) / 2;
  return (
    <g>
      <defs><radialGradient id={id} cx="0.38" cy="0.32"><stop offset="0" stopColor="#F4F5F6" /><stop offset="1" stopColor="#A5AAB0" /></radialGradient></defs>
      <rect width={w} height={h} rx={s * 0.6} fill="#2B2B2F" stroke="#000" strokeWidth={s * 0.1} />
      <circle cx={w / 2} cy={h / 2} r={r * 0.9} fill={`url(#${id})`} stroke="#6D7279" strokeWidth={s * 0.12} />
      <circle cx={w / 2} cy={h / 2} r={r * 0.68} fill="none" stroke="#8E949B" strokeWidth={s * 0.08} />
      <text x={w / 2} y={h / 2 - r * 0.05} textAnchor="middle" fontSize={r * 0.34} fontWeight={700} fill="#4D5258" fontFamily={MONO}>CR2032</text>
      <text x={w / 2} y={h / 2 + r * 0.3} textAnchor="middle" fontSize={r * 0.26} fill="#4D5258" fontFamily={MONO}>+ 3V</text>
    </g>
  );
}

export function LiPo({ w, h, s, label }: Spec) {
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.5} fill="#B9BEC4" stroke="#7B8086" strokeWidth={s * 0.14} />
      <rect x={0} y={0} width={s * 1.2} height={h} rx={s * 0.4} fill="#9CA2A9" />
      <rect x={w * 0.14} y={h * 0.16} width={w * 0.72} height={h * 0.68} rx={s * 0.3} fill="#F2F2EE" stroke="#C4C4BC" strokeWidth={s * 0.06} />
      <text x={w * 0.5} y={h * 0.46} textAnchor="middle" fontSize={Math.min(h * 0.16, w * 0.09)} fontWeight={700} fill="#222" fontFamily={MONO}>Li-Po</text>
      <text x={w * 0.5} y={h * 0.66} textAnchor="middle" fontSize={Math.min(h * 0.12, w * 0.07)} fill="#444" fontFamily={MONO}>{label ?? "3.7 V"}</text>
    </g>
  );
}

/** Split-core current transformer: a black ring that opens, plus its output lead. */
export function CurrentClamp({ w, h, s }: Spec) {
  const R = Math.min(w, h) / 2;
  return (
    <g>
      <rect x={0} y={0} width={w} height={h} rx={s * 1.2} fill="#222226" stroke="#000" strokeWidth={s * 0.12} />
      <circle cx={w / 2} cy={h * 0.46} r={R * 0.52} fill="#EDEDED" stroke="#000" strokeWidth={s * 0.12} />
      <circle cx={w / 2} cy={h * 0.46} r={R * 0.52} fill="none" stroke="#444" strokeWidth={s * 0.5} opacity={0.5} />
      <rect x={w * 0.08} y={h * 0.86} width={w * 0.84} height={h * 0.08} fill="#E9E9E3" />
      <rect x={w * 0.35} y={h * 0.9} width={w * 0.3} height={h * 0.1} fill="#D4D4CE" />
      <line x1={w * 0.04} y1={h * 0.46} x2={w * 0.96} y2={h * 0.46} stroke="#000" strokeWidth={s * 0.08} opacity={0.35} />
    </g>
  );
}

/** Aluminium bar load cell with its cable; the four leads end on the right edge. */
export function LoadCell({ w, h, s }: Spec) {
  const id = useId();
  const body = w * 0.8;
  return (
    <g>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#F2F3F5" /><stop offset="0.5" stopColor="#C6CAD0" /><stop offset="1" stopColor="#9EA3AA" /></linearGradient></defs>
      <rect x={0} y={0} width={body} height={h} rx={s * 0.4} fill={`url(#${id})`} stroke="#6D7279" strokeWidth={s * 0.12} />
      {[0.1, 0.9].map((x) => <circle key={x} cx={body * x} cy={h / 2} r={h * 0.18} fill="#5A5F65" stroke="#2D3035" strokeWidth={s * 0.08} />)}
      <ellipse cx={body / 2} cy={h / 2} rx={body * 0.14} ry={h * 0.3} fill="#8A9097" stroke="#4A4F55" strokeWidth={s * 0.1} />
      <rect x={body * 0.42} y={h * 0.4} width={body * 0.16} height={h * 0.2} fill="#D7DADE" />
      <rect x={body} y={h * 0.38} width={w - body} height={h * 0.24} rx={s * 0.1} fill="#2A2A2E" />
    </g>
  );
}

export function ReedSwitch({ w, h, s }: Spec) {
  return (
    <g>
      <line x1={0} y1={h / 2} x2={w} y2={h / 2} stroke={TIN} strokeWidth={s * 0.25} />
      <rect x={w * 0.14} y={0} width={w * 0.72} height={h} rx={h / 2} fill="#CFE8E4" fillOpacity={0.55} stroke="#6E8F8A" strokeWidth={s * 0.1} />
      <path d={`M${w * 0.16},${h * 0.42} H${w * 0.5} M${w * 0.84},${h * 0.58} H${w * 0.52}`} stroke="#8A9097" strokeWidth={s * 0.28} />
    </g>
  );
}

export function Magnet({ w, h, s }: Spec) {
  return (
    <g>
      <rect width={w / 2} height={h} fill="#D91E2A" stroke="#000" strokeWidth={s * 0.08} />
      <rect x={w / 2} width={w / 2} height={h} fill="#E8E8E8" stroke="#000" strokeWidth={s * 0.08} />
      <text x={w * 0.25} y={h * 0.68} textAnchor="middle" fontSize={h * 0.5} fontWeight={700} fill="#FFF" fontFamily={MONO}>N</text>
      <text x={w * 0.75} y={h * 0.68} textAnchor="middle" fontSize={h * 0.5} fontWeight={700} fill="#444" fontFamily={MONO}>S</text>
    </g>
  );
}

/** Stainless temperature probe with its cable. */
export function Probe({ w, h, s }: Spec) {
  const id = useId();
  return (
    <g>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#F2F3F5" /><stop offset="1" stopColor="#9EA3AA" /></linearGradient></defs>
      <rect x={w * 0.42} y={h * 0.3} width={w * 0.58} height={h * 0.4} fill="#2A2A2E" />
      <rect x={0} y={h * 0.18} width={w * 0.5} height={h * 0.64} rx={h * 0.32} fill={`url(#${id})`} stroke="#6D7279" strokeWidth={s * 0.1} />
      <rect x={w * 0.34} y={h * 0.1} width={w * 0.12} height={h * 0.8} fill="#1F1F22" />
    </g>
  );
}

/** DIN-rail energy meter, front face: grey housing, LCD, label. */
export function DinMeter({ w, h, s, label }: Spec) {
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.5} fill="#E7E8EA" stroke="#9A9FA5" strokeWidth={s * 0.14} />
      <rect x={w * 0.1} y={h * 0.08} width={w * 0.8} height={h * 0.3} rx={s * 0.3} fill="#9DB09A" stroke="#4E5A4D" strokeWidth={s * 0.1} />
      <text x={w / 2} y={h * 0.28} textAnchor="middle" fontSize={h * 0.14} fill="#2B332A" fontFamily={MONO}>0.00 kWh</text>
      <text x={w / 2} y={h * 0.55} textAnchor="middle" fontSize={Math.min(h * 0.08, w * 0.12)} fontWeight={700} fill="#333" fontFamily={MONO}>{label ?? "METER"}</text>
      {[0.2, 0.5, 0.8].map((x) => <rect key={x} x={w * x - w * 0.09} y={h * 0.86} width={w * 0.18} height={h * 0.08} fill="#25282C" />)}
      <rect x={w * 0.1} y={h * 0.64} width={w * 0.8} height={h * 0.1} fill={PLASTIC_BLACK} opacity={0.12} />
      <circle cx={w * 0.86} cy={h * 0.5} r={s * 0.35} fill={GOLD} />
    </g>
  );
}

export function Enclosure({ w, h, s }: Spec) {
  return (
    <g>
      <rect width={w} height={h} rx={s * 1.5} fill="none" stroke="#A3A7AD" strokeWidth={s * 0.3} strokeDasharray={`${s * 1.2} ${s * 0.8}`} />
      {[[1.2, 1.2], [w / s - 1.2, 1.2], [1.2, h / s - 1.2], [w / s - 1.2, h / s - 1.2]].map(([x, y]) => <circle key={`${x}${y}`} cx={x! * s} cy={y! * s} r={s * 0.5} fill="#D9DBDE" stroke="#8E949B" strokeWidth={s * 0.1} />)}
    </g>
  );
}
