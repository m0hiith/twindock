// /parts: every part family drawn side by side at true size, with a zoom switch. A visual test page for the
// part library (frontend/src/wiring/parts): if something looks toy-like or out of scale, it shows here first.
import { useState } from "react";
import { Brand } from "../hud/Brand";
import { PageTabs } from "../hud/PageTabs";
import { FeatureArt, PartArt, PX_PER_MM, type PartDrawing } from "../wiring/parts";
import type { Family } from "../wiring/parts/types";

interface Specimen { name: string; f: { family: Family; variant?: string; label?: string; color?: string; w_mm: number; h_mm: number; rot?: 0 | 90 | 180 | 270 }; note?: string }

const SPECIMENS: Specimen[] = [
  { name: "Chip · QFN 4×4", f: { family: "chip", variant: "qfn", label: "EFR32", w_mm: 4, h_mm: 4 } },
  { name: "Chip · QFN 7×7 (SiWG917)", f: { family: "chip", variant: "qfn", label: "SiWG917", w_mm: 7, h_mm: 7 } },
  { name: "Chip · LGA 3×3", f: { family: "chip", variant: "lga", label: "ICM", w_mm: 3, h_mm: 3 } },
  { name: "Chip · SOIC-8", f: { family: "chip", variant: "soic", label: "MAX3485", w_mm: 4.9, h_mm: 3.9 } },
  { name: "Module · shielded", f: { family: "chip", variant: "module", label: "SiWG917Y", w_mm: 16, h_mm: 13 } },
  { name: "Resistor 0603", f: { family: "passive", variant: "r0603", w_mm: 1.6, h_mm: 0.8 } },
  { name: "Resistor 0805", f: { family: "passive", variant: "r0805", label: "103", w_mm: 2, h_mm: 1.25 } },
  { name: "Capacitor 0805", f: { family: "passive", variant: "c0805", w_mm: 2, h_mm: 1.25 } },
  { name: "Crystal", f: { family: "crystal", label: "32.768k", w_mm: 3.2, h_mm: 1.5 } },
  { name: "Chip antenna", f: { family: "antenna", variant: "chip", w_mm: 3.2, h_mm: 1.6 } },
  { name: "PCB trace antenna", f: { family: "antenna", variant: "trace", w_mm: 12, h_mm: 4 } },
  { name: "u.FL connector", f: { family: "antenna", variant: "ufl", w_mm: 3, h_mm: 3 } },
  { name: "LED 0603", f: { family: "led", color: "#E5392B", w_mm: 1.6, h_mm: 0.8 } },
  { name: "Tactile button", f: { family: "button", w_mm: 6, h_mm: 6 } },
  { name: "Qwiic / JST-SH 4", f: { family: "connector", variant: "qwiic", w_mm: 7.4, h_mm: 4.4 } },
  { name: "JST-PH 4", f: { family: "connector", variant: "jst_ph_4", w_mm: 9.8, h_mm: 6 } },
  { name: "Screw terminal ×3", f: { family: "connector", variant: "screw_3", w_mm: 15.2, h_mm: 10 } },
  { name: "Pin header ×6", f: { family: "connector", variant: "header_6", w_mm: 15.24, h_mm: 2.54 } },
  { name: "USB-C", f: { family: "connector", variant: "usb_c", w_mm: 9, h_mm: 7.3 } },
  { name: "M12 A-coded 4-pin", f: { family: "connector", variant: "m12_4", w_mm: 15, h_mm: 15 } },
  { name: "ToF optical window", f: { family: "sensor_window", variant: "tof", w_mm: 4.9, h_mm: 2.5 } },
  { name: "Gas sensor mesh cap", f: { family: "sensor_window", variant: "gas", w_mm: 20, h_mm: 20 } },
  { name: "Microphone port", f: { family: "sensor_window", variant: "mic", w_mm: 3.5, h_mm: 2.65 } },
  { name: "Light sensor window", f: { family: "sensor_window", variant: "light", w_mm: 2, h_mm: 2 } },
  { name: "Relay", f: { family: "relay", label: "5 V · 10 A", w_mm: 19, h_mm: 15.5 } },
  { name: "Terminal block ×4", f: { family: "terminal_block", variant: "tb_4", w_mm: 28, h_mm: 14 } },
  { name: "Coin-cell holder", f: { family: "coin_cell_holder", w_mm: 24, h_mm: 24 } },
  { name: "LiPo pouch cell", f: { family: "lipo", label: "3.7 V 500 mAh", w_mm: 50, h_mm: 30 } },
  { name: "Current clamp", f: { family: "current_clamp", w_mm: 30, h_mm: 38 } },
  { name: "Load cell (bar)", f: { family: "load_cell", w_mm: 100, h_mm: 12.7 } },
  { name: "Reed switch", f: { family: "reed_switch", w_mm: 14, h_mm: 2.5 } },
  { name: "Magnet", f: { family: "magnet", w_mm: 20, h_mm: 8 } },
  { name: "PIR dome", f: { family: "pir_dome", w_mm: 23, h_mm: 23 } },
  { name: "Buzzer", f: { family: "buzzer", w_mm: 12, h_mm: 12 } },
  { name: "Temperature probe", f: { family: "probe", w_mm: 60, h_mm: 6 } },
  { name: "Enclosure (outline)", f: { family: "enclosure", w_mm: 80, h_mm: 60 } },
  { name: "DIN-rail meter", f: { family: "din_meter", label: "METER", w_mm: 36, h_mm: 90 } },
];

const BOARDS: { name: string; d: PartDrawing }[] = (["green", "blue", "black", "red", "white", "yellow"] as const).map((c) => ({
  name: `${c[0]!.toUpperCase()}${c.slice(1)} PCB`,
  d: {
    family: "pcb", w_mm: 30, h_mm: 20, pcb_color: c, dims_evidence: "typical",
    features: [
      { family: "pcb", variant: "hole", x_mm: 1.5, y_mm: 1.5, w_mm: 2.8, h_mm: 2.8 },
      { family: "pcb", variant: "hole", x_mm: 25.7, y_mm: 15.7, w_mm: 2.8, h_mm: 2.8 },
      { family: "chip", variant: "qfn", label: "MCU", x_mm: 11, y_mm: 6, w_mm: 5, h_mm: 5 },
      { family: "connector", variant: "qwiic", x_mm: 11, y_mm: 15, w_mm: 7.4, h_mm: 4.4 },
      { family: "passive", variant: "r0603", x_mm: 19, y_mm: 8, w_mm: 1.6, h_mm: 0.8 },
      { family: "passive", variant: "c0805", x_mm: 19, y_mm: 10, w_mm: 2, h_mm: 1.25 },
      { family: "led", x_mm: 22, y_mm: 6, w_mm: 1.6, h_mm: 0.8 },
      { family: "pcb", variant: "silk", label: c.toUpperCase(), x_mm: 3, y_mm: 18.5, w_mm: 10, h_mm: 1.4 },
    ],
  },
}));

export function PartsGallery() {
  const [zoom, setZoom] = useState<1 | 3>(1);
  const s = PX_PER_MM * zoom * 0.5; // 1x = 5 px/mm so every family fits a card; 3x = 15 px/mm
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4"><Brand /><PageTabs className="ml-2" /></header>
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-[20px] font-semibold">Part gallery</h1>
            <p className="text-[13px] text-ink-2">Every part family at true relative size ({s} px per mm). Procedural SVG, no third-party artwork.</p>
          </div>
          <div className="ml-auto flex gap-1 rounded-xl bg-idle-bg p-1" role="group" aria-label="Zoom">
            {([1, 3] as const).map((z) => (
              <button key={z} type="button" onClick={() => setZoom(z)} aria-pressed={zoom === z}
                className={`h-8 rounded-lg px-3 text-[13px] font-medium ${zoom === z ? "bg-white shadow-sm" : "text-ink-2"}`}>{z * 100}%</button>
            ))}
          </div>
        </div>
        <section className="flex flex-wrap gap-3" aria-label="PCBs">
          {BOARDS.map((b) => (
            <Card key={b.name} name={b.name} w={b.d.w_mm * s + 24} h={b.d.h_mm * s + 24}>
              <g transform="translate(12 12)"><PartArt drawing={b.d} s={s} /></g>
            </Card>
          ))}
        </section>
        <section className="flex flex-wrap items-start gap-3" aria-label="Parts">
          {SPECIMENS.map((p) => {
            const swap = p.f.rot === 90 || p.f.rot === 270;
            const w = (swap ? p.f.h_mm : p.f.w_mm) * s;
            const h = (swap ? p.f.w_mm : p.f.h_mm) * s;
            return (
              <Card key={p.name} name={p.name} sub={`${p.f.w_mm} × ${p.f.h_mm} mm`} w={Math.max(w + 24, 130)} h={h + 24}>
                <g transform={`translate(${Math.max(12, (Math.max(w + 24, 130) - w) / 2)} 12)`}><FeatureArt f={p.f} s={s} /></g>
              </Card>
            );
          })}
        </section>
      </div>
    </div>
  );
}

function Card({ name, sub, w, h, children }: { name: string; sub?: string; w: number; h: number; children: React.ReactNode }) {
  return (
    <figure className="card flex flex-col gap-1 p-2" data-testid="part-card">
      <svg width={w} height={h} className="rounded-lg bg-[#F1F1F1]" role="img" aria-label={name}>{children}</svg>
      <figcaption className="text-[12px]"><b>{name}</b>{sub && <span className="text-ink-2"> · {sub}</span>}</figcaption>
    </figure>
  );
}
