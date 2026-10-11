// PCBs, chips, passives, crystals, antennas, LEDs and buttons, drawn from above at true size.
import { useId } from "react";
import { GOLD, GOLD_DARK, PCB_MASK, PLASTIC_BLACK, SILK, TIN, TIN_DARK, type PcbColor } from "./palette";
import type { Spec } from "./types";

/** Shrinks a label so it fits its package. */
const fit = (label: string, w: number, h: number) => Math.max(3, Math.min(h * 0.34, w / (label.length * 0.62 + 0.4)));

export function Pcb({ w, h, s, pcb = "green", variant, label }: Spec) {
  const id = useId();
  const c = PCB_MASK[(pcb in PCB_MASK ? pcb : "green") as PcbColor];
  if (variant === "hole") {
    // Plated mounting hole: copper ring around a through hole.
    const r = Math.min(w, h) / 2;
    return (
      <g>
        <circle cx={w / 2} cy={h / 2} r={r} fill={GOLD} stroke={GOLD_DARK} strokeWidth={s * 0.08} />
        <circle cx={w / 2} cy={h / 2} r={r * 0.62} fill="#EDEDED" stroke="#00000055" strokeWidth={s * 0.06} />
      </g>
    );
  }
  if (variant === "silk") {
    return <text x={0} y={h * 0.8} fontSize={Math.max(h, s * 1.2)} fontFamily="ui-monospace, Menlo, monospace" fill={SILK} opacity={0.85}>{label}</text>;
  }
  const rx = Math.min(s * 1.2, w / 8, h / 8);
  return (
    <g>
      <defs>
        <linearGradient id={`${id}-m`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={c.light} /><stop offset="0.55" stopColor={c.base} /><stop offset="1" stopColor={c.dark} />
        </linearGradient>
      </defs>
      <rect width={w} height={h} rx={rx} fill={`url(#${id}-m)`} stroke={c.dark} strokeWidth={s * 0.12} />
      <rect x={s * 0.25} y={s * 0.25} width={w - s * 0.5} height={h - s * 0.5} rx={rx * 0.8} fill="none" stroke="#FFFFFF" strokeOpacity={0.12} strokeWidth={s * 0.08} />
    </g>
  );
}

export function Chip({ w, h, s, variant = "qfn", label }: Spec) {
  const id = useId();
  const pin = Math.max(0.5, s * 0.22);
  const ticks = (n: number, along: "x" | "y", at: number, len: number, color: string) =>
    Array.from({ length: n }, (_, i) => {
      const t = ((i + 0.5) / n) * (along === "x" ? w : h);
      return along === "x"
        ? <rect key={`${at}x${i}`} x={t - pin / 2} y={at} width={pin} height={len} fill={color} />
        : <rect key={`${at}y${i}`} x={at} y={t - pin / 2} width={len} height={pin} fill={color} />;
    });
  const n = (len: number) => Math.max(3, Math.round(len / (s * 0.6)));
  if (variant === "module") {
    // RF module under a stamped metal shield can.
    return (
      <g>
        <defs><linearGradient id={`${id}-t`} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#EEF0F2" /><stop offset="1" stopColor={TIN_DARK} /></linearGradient></defs>
        <rect width={w} height={h} rx={s * 0.35} fill={`url(#${id}-t)`} stroke="#6D7279" strokeWidth={s * 0.1} />
        <rect x={s * 0.5} y={s * 0.5} width={w - s} height={h - s} rx={s * 0.2} fill="none" stroke="#FFFFFF" strokeOpacity={0.5} strokeWidth={s * 0.08} />
        {label && <text x={w / 2} y={h / 2 + fit(label, w, h) * 0.35} textAnchor="middle" fontSize={fit(label, w, h)} fontWeight={600} fill="#4A4F55" fontFamily="ui-monospace, Menlo, monospace">{label}</text>}
      </g>
    );
  }
  const legs = variant === "soic" ? [...ticks(n(w), "x", -s * 0.28, s * 0.4, TIN), ...ticks(n(w), "x", h - s * 0.12, s * 0.4, TIN)]
    : variant === "qfn" ? [...ticks(n(w), "x", h - s * 0.1, s * 0.22, GOLD), ...ticks(n(w), "x", -s * 0.12, s * 0.22, GOLD), ...ticks(n(h), "y", -s * 0.12, s * 0.22, GOLD), ...ticks(n(h), "y", w - s * 0.1, s * 0.22, GOLD)]
    : [];
  const inset = variant === "soic" ? 0 : s * 0.1;
  const body = { x: inset, y: inset, w: w - inset * 2, h: h - inset * 2 };
  return (
    <g>
      <defs><linearGradient id={`${id}-b`} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#3A3A3E" /><stop offset="1" stopColor={PLASTIC_BLACK} /></linearGradient></defs>
      {legs}
      <rect x={body.x} y={body.y} width={body.w} height={body.h} rx={s * 0.12} fill={`url(#${id}-b)`} stroke="#000" strokeWidth={s * 0.06} />
      <circle cx={body.x + Math.min(s * 0.5, body.w * 0.16)} cy={body.y + Math.min(s * 0.5, body.h * 0.16)} r={Math.min(s * 0.2, body.w * 0.07)} fill="#8A8A90" />
      {label && body.w > s * 1.6 && body.h > s * 1.2 && (
        <text x={w / 2} y={h / 2 + fit(label, body.w, body.h) * 0.35} textAnchor="middle" fontSize={fit(label, body.w, body.h)}
          fill="#B8B8BE" fontFamily="ui-monospace, Menlo, monospace">{label}</text>
      )}
    </g>
  );
}

export function Passive({ w, h, s, variant = "r0603", label }: Spec) {
  const cap = Math.max(w, h) * 0.2;
  const horizontal = w >= h;
  const body = variant.startsWith("c") ? "#B79562" : variant.startsWith("l") ? "#6E6E72" : "#202022";
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.05} fill={body} stroke="#00000066" strokeWidth={s * 0.04} />
      {horizontal
        ? <><rect width={cap} height={h} fill={TIN} /><rect x={w - cap} width={cap} height={h} fill={TIN} /></>
        : <><rect width={w} height={cap} fill={TIN} /><rect y={h - cap} width={w} height={cap} fill={TIN} /></>}
      {label && horizontal && w > s * 1.4 && <text x={w / 2} y={h / 2 + h * 0.18} textAnchor="middle" fontSize={h * 0.5} fill="#CFCFCF" fontFamily="ui-monospace, Menlo, monospace">{label}</text>}
    </g>
  );
}

export function Crystal({ w, h, s, label }: Spec) {
  const id = useId();
  return (
    <g>
      <defs><linearGradient id={`${id}-t`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#F2F4F6" /><stop offset="1" stopColor={TIN_DARK} /></linearGradient></defs>
      <rect width={w} height={h} rx={s * 0.2} fill={`url(#${id}-t)`} stroke="#6D7279" strokeWidth={s * 0.06} />
      <rect x={s * 0.15} y={s * 0.15} width={w - s * 0.3} height={h - s * 0.3} rx={s * 0.12} fill="none" stroke="#FFF" strokeOpacity={0.6} strokeWidth={s * 0.05} />
      {label && <text x={w / 2} y={h / 2 + h * 0.14} textAnchor="middle" fontSize={h * 0.34} fill="#555A60" fontFamily="ui-monospace, Menlo, monospace">{label}</text>}
    </g>
  );
}

export function Antenna({ w, h, s, variant = "chip" }: Spec) {
  if (variant === "ufl") {
    // u.FL / IPEX: a small round coax socket, centre pin in a ground shell.
    const r = Math.min(w, h) / 2;
    return (
      <g>
        <rect width={w} height={h} rx={s * 0.2} fill={TIN} stroke={TIN_DARK} strokeWidth={s * 0.06} />
        <circle cx={w / 2} cy={h / 2} r={r * 0.62} fill="#2A2A2E" stroke={TIN_DARK} strokeWidth={s * 0.08} />
        <circle cx={w / 2} cy={h / 2} r={r * 0.22} fill={GOLD} />
      </g>
    );
  }
  if (variant === "trace") {
    // Meandered copper trace printed on the board.
    const turns = Math.max(3, Math.floor(w / (s * 0.9)));
    let d = `M0,${h}`;
    for (let i = 0; i < turns; i++) {
      const x = (i + 0.5) * (w / turns);
      d += ` L${x},${i % 2 === 0 ? s * 0.2 : h} L${x + w / turns / 2},${i % 2 === 0 ? s * 0.2 : h}`;
    }
    return <path d={d} fill="none" stroke={GOLD} strokeWidth={s * 0.28} strokeLinejoin="round" opacity={0.95} />;
  }
  // Ceramic chip antenna: a tan block with copper end caps.
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.1} fill="#CBBB9A" stroke="#8C7C5A" strokeWidth={s * 0.05} />
      <rect width={w * 0.14} height={h} fill={GOLD} /><rect x={w * 0.86} width={w * 0.14} height={h} fill={GOLD} />
      <path d={`M${w * 0.22},${h * 0.7} H${w * 0.4} V${h * 0.3} H${w * 0.58} V${h * 0.7} H${w * 0.78}`} fill="none" stroke="#8C7C5A" strokeWidth={s * 0.07} />
    </g>
  );
}

export function Led({ w, h, s, color = "#E5392B" }: Spec) {
  const id = useId();
  return (
    <g>
      <defs><radialGradient id={`${id}-g`}><stop offset="0" stopColor="#FFFFFF" stopOpacity={0.9} /><stop offset="1" stopColor={color} /></radialGradient></defs>
      <rect width={w} height={h} rx={s * 0.08} fill="#E8E8E4" stroke="#9A9A94" strokeWidth={s * 0.05} />
      <rect x={w * 0.1} y={h * 0.14} width={w * 0.8} height={h * 0.72} rx={s * 0.1} fill={`url(#${id}-g)`} opacity={0.95} />
      <rect x={0} y={0} width={w * 0.08} height={h} fill={GOLD} /><rect x={w * 0.92} y={0} width={w * 0.08} height={h} fill={GOLD} />
    </g>
  );
}

export function Button({ w, h, s }: Spec) {
  const id = useId();
  const r = Math.min(w, h) * 0.32;
  return (
    <g>
      <defs><radialGradient id={`${id}-d`} cx="0.35" cy="0.3"><stop offset="0" stopColor="#555" /><stop offset="1" stopColor="#1B1B1D" /></radialGradient></defs>
      {[0.14, 0.86].flatMap((fx) => [0.2, 0.8].map((fy) => <rect key={`${fx}${fy}`} x={w * fx - s * 0.3} y={h * fy - s * 0.2} width={s * 0.6} height={s * 0.4} fill={TIN} />))}
      <rect x={w * 0.04} y={h * 0.04} width={w * 0.92} height={h * 0.92} rx={s * 0.25} fill="#D6D8DB" stroke={TIN_DARK} strokeWidth={s * 0.08} />
      <circle cx={w / 2} cy={h / 2} r={r} fill={`url(#${id}-d)`} stroke="#000" strokeWidth={s * 0.06} />
      {[[0.16, 0.16], [0.84, 0.16], [0.16, 0.84], [0.84, 0.84]].map(([x, y]) => <circle key={`${x}${y}`} cx={w * x!} cy={h * y!} r={s * 0.12} fill={TIN_DARK} />)}
    </g>
  );
}
