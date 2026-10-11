// Connectors seen from above: Qwiic (JST-SH), JST-PH, screw terminals, pin headers, USB-C, M12.
import { useId } from "react";
import { CREAM, CREAM_DARK, GOLD, GOLD_DARK, PLASTIC_BLACK, TIN, TIN_DARK } from "./palette";
import { countOf, type Spec } from "./types";

export function Connector(p: Spec) {
  const v = p.variant ?? "qwiic";
  if (v.startsWith("qwiic") || v.startsWith("jst_sh")) return <JstSh {...p} n={countOf(v, 4)} />;
  if (v.startsWith("jst_ph")) return <JstPh {...p} n={countOf(v, 4)} />;
  if (v.startsWith("screw")) return <Screw {...p} n={countOf(v, 2)} />;
  if (v.startsWith("header")) return <Header {...p} n={countOf(v, 4)} />;
  if (v === "usb_c") return <UsbC {...p} />;
  if (v.startsWith("m12")) return <M12 {...p} n={countOf(v, 4)} />;
  return <JstSh {...p} n={4} />;
}

/** 1.0 mm pitch, 4 contacts, opening towards the bottom edge of the box. */
function JstSh({ w, h, s, n }: Spec & { n: number }) {
  const pitch = w / (n + 2.2);
  const x0 = (w - pitch * (n - 1)) / 2;
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.15} fill={CREAM} stroke={CREAM_DARK} strokeWidth={s * 0.08} />
      <rect x={w * 0.1} y={h * 0.08} width={w * 0.8} height={h * 0.34} rx={s * 0.1} fill="#CFC5A8" />
      <rect x={w * 0.08} y={h * 0.46} width={w * 0.84} height={h * 0.48} rx={s * 0.1} fill="#2A2A2C" />
      {Array.from({ length: n }, (_, i) => <rect key={i} x={x0 + i * pitch - pitch * 0.2} y={h * 0.5} width={pitch * 0.4} height={h * 0.34} fill={GOLD} />)}
      {[0, 1].map((i) => <rect key={i} x={i ? w - s * 0.5 : 0} y={h * 0.55} width={s * 0.5} height={h * 0.4} fill={TIN} stroke={TIN_DARK} strokeWidth={s * 0.04} />)}
    </g>
  );
}

function JstPh({ w, h, s, n }: Spec & { n: number }) {
  const pitch = 2 * s;
  const x0 = (w - pitch * (n - 1)) / 2;
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.2} fill="#E4E4DA" stroke="#8E8E84" strokeWidth={s * 0.08} />
      <rect x={w * 0.06} y={h * 0.14} width={w * 0.88} height={h * 0.58} rx={s * 0.15} fill="#B9B9AE" />
      {Array.from({ length: n }, (_, i) => <rect key={i} x={x0 + i * pitch - s * 0.28} y={h * 0.2} width={s * 0.56} height={h * 0.46} fill={TIN} stroke={TIN_DARK} strokeWidth={s * 0.04} />)}
      <path d={`M${w * 0.4},${h * 0.9} h${w * 0.2}`} stroke="#B4B4AC" strokeWidth={s * 0.12} />
    </g>
  );
}

function Screw({ w, h, s, n }: Spec & { n: number }) {
  const id = useId();
  const pole = w / n;
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.2} fill="#2E8B57" stroke="#1B5E3A" strokeWidth={s * 0.1} />
      {Array.from({ length: n }, (_, i) => {
        const cx = pole * (i + 0.5);
        const r = Math.min(pole, h) * 0.3;
        return (
          <g key={i}>
            <rect x={cx - pole * 0.4} y={h * 0.62} width={pole * 0.8} height={h * 0.3} rx={s * 0.1} fill="#12301F" />
            <circle cx={cx} cy={h * 0.32} r={r} fill={`url(#${id})`} stroke={TIN_DARK} strokeWidth={s * 0.08} />
            <path d={`M${cx - r * 0.7},${h * 0.32 - r * 0.2} L${cx + r * 0.7},${h * 0.32 + r * 0.2}`} stroke="#555B61" strokeWidth={s * 0.22} strokeLinecap="round" />
          </g>
        );
      })}
      <defs><radialGradient id={id} cx="0.35" cy="0.3"><stop offset="0" stopColor="#F5F6F7" /><stop offset="1" stopColor={TIN_DARK} /></radialGradient></defs>
    </g>
  );
}

function Header({ w, h, s, n }: Spec & { n: number }) {
  const vertical = h > w;
  const pitch = 2.54 * s;
  const len = pitch * n;
  const ox = vertical ? (w - pitch) / 2 : (w - len) / 2;
  const oy = vertical ? (h - len) / 2 : (h - pitch) / 2;
  return (
    <g>
      <rect x={ox} y={oy} width={vertical ? pitch : len} height={vertical ? len : pitch} fill={PLASTIC_BLACK} stroke="#000" strokeWidth={s * 0.05} />
      {Array.from({ length: n }, (_, i) => {
        const cx = vertical ? ox + pitch / 2 : ox + pitch * (i + 0.5);
        const cy = vertical ? oy + pitch * (i + 0.5) : oy + pitch / 2;
        return <g key={i}><rect x={cx - s * 0.32} y={cy - s * 0.32} width={s * 0.64} height={s * 0.64} fill={GOLD} stroke={GOLD_DARK} strokeWidth={s * 0.05} /><rect x={cx - s * 0.12} y={cy - s * 0.12} width={s * 0.24} height={s * 0.24} fill="#FFF3C8" /></g>;
      })}
    </g>
  );
}

function UsbC({ w, h, s }: Spec) {
  return (
    <g>
      <rect width={w} height={h} rx={s * 0.5} fill="#E3E5E8" stroke={TIN_DARK} strokeWidth={s * 0.12} />
      <rect x={w * 0.07} y={h * 0.12} width={w * 0.86} height={h * 0.72} rx={s * 0.3} fill="#18181A" />
      <rect x={w * 0.2} y={h * 0.38} width={w * 0.6} height={h * 0.16} fill="#0A0A0B" />
      {Array.from({ length: 12 }, (_, i) => <rect key={i} x={w * 0.22 + i * (w * 0.56 / 12)} y={h * 0.3} width={w * 0.025} height={h * 0.14} fill={GOLD} />)}
      {Array.from({ length: 12 }, (_, i) => <rect key={`b${i}`} x={w * 0.22 + i * (w * 0.56 / 12)} y={h * 0.5} width={w * 0.025} height={h * 0.14} fill={GOLD} />)}
    </g>
  );
}

/** M12 A-coded panel connector, face on: knurled nut, keyed insert, pins on a circle. */
function M12({ w, h, s, n }: Spec & { n: number }) {
  const id = useId();
  const r = Math.min(w, h) / 2;
  const pins = Array.from({ length: n }, (_, i) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 4;
    return { x: w / 2 + Math.cos(a) * r * 0.42, y: h / 2 + Math.sin(a) * r * 0.42 };
  });
  return (
    <g>
      <defs><radialGradient id={id} cx="0.4" cy="0.35"><stop offset="0" stopColor="#F2F3F5" /><stop offset="1" stopColor={TIN_DARK} /></radialGradient></defs>
      <circle cx={w / 2} cy={h / 2} r={r} fill={`url(#${id})`} stroke="#5A5F65" strokeWidth={s * 0.15} />
      {Array.from({ length: 24 }, (_, i) => {
        const a = (Math.PI * 2 * i) / 24;
        return <line key={i} x1={w / 2 + Math.cos(a) * r * 0.9} y1={h / 2 + Math.sin(a) * r * 0.9} x2={w / 2 + Math.cos(a) * r} y2={h / 2 + Math.sin(a) * r} stroke="#5A5F65" strokeWidth={s * 0.12} />;
      })}
      <circle cx={w / 2} cy={h / 2} r={r * 0.68} fill="#1F1F22" stroke="#000" strokeWidth={s * 0.08} />
      <rect x={w / 2 - s * 0.35} y={h / 2 - r * 0.68 - s * 0.05} width={s * 0.7} height={s * 0.6} fill={TIN} />
      {pins.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r={s * 0.38} fill={GOLD} stroke={GOLD_DARK} strokeWidth={s * 0.06} />)}
    </g>
  );
}
