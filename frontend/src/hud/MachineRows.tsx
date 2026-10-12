// Inspect-card rows for a FAC-01 machine: state, cycle time, current, vibration against its learned
// baseline (chart with the normal band), units today, last fault, OEE parts. All simulated (SIM).
import { useState } from "react";
import type { Unit } from "../contract";
import { RangeBar, useHistory, type HistoryRange } from "../fleet/DevicePanel";
import { BandChart } from "../fleet/ui";
import { stateLabel } from "../status";
import { useWorld } from "../store/world";
import { ago, SimBadge, useTick } from "./ui";

const pct = (x: number | null) => (x === null ? "—" : `${Math.round(x * 100)}%`);
const num = (x: number | null, unit: string, d = 1) => (x === null ? "—" : `${x.toFixed(d)} ${unit}`);

function Row({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5 text-[13px]">
      <span className="shrink-0 text-ink-2">{k}</span>
      <span className="min-w-0 truncate text-right font-medium">{children}</span>
    </div>
  );
}

export function MachineRows({ u }: { u: Unit }) {
  const m = useWorld((s) => s.production?.machines.find((x) => x.id === u.id));
  const cfg = useWorld((s) => s.production?.config);
  const [range, setRange] = useState<HistoryRange>("15m");
  const history = useHistory(m?.device_id ?? "", m ? "vibration_rms" : null, range);
  useTick(1000);
  if (!m || !cfg) return <Row k="Data">Waiting for machine monitor</Row>;
  const b = m.baseline;
  const band: [number, number] | null = b.learned && b.mean !== null && b.std !== null
    ? [b.mean - cfg.z_threshold * b.std, b.mean + cfg.z_threshold * b.std] : null;
  return (
    <>
      <Row k="State">{stateLabel(m.state)}</Row>
      <Row k="Source"><span className="inline-flex items-center gap-1.5">Machine monitor {m.device_id} <SimBadge /></span></Row>
      <Row k="Data age">{m.data_ms ? ago(m.data_ms) : "never"}</Row>
      <Row k="Cycle time"><span className="tabular">{num(m.cycle_time_s, "s")} <span className="text-ink-2">(ideal {m.ideal_cycle_s} s)</span></span></Row>
      <Row k="Motor current"><span className="tabular">{num(m.current_a, "A")}</span></Row>
      <div className="py-2">
        <div className="flex items-baseline justify-between text-[13px]">
          <span className="text-ink-2">Vibration (RMS)</span>
          <span className={`tabular font-medium ${m.abnormal ? "text-warn" : ""}`}>
            {num(m.vibration_rms, "mm/s", 2)}{m.z !== null && <span className="text-ink-2"> · z {m.z.toFixed(1)}</span>}
          </span>
        </div>
        {m.abnormal && (
          <div className="mt-1 rounded-lg bg-warn-bg px-2.5 py-1.5 text-[12px] text-warn">
            Abnormal compared with this machine's baseline (z above {cfg.z_threshold}). Not a failure prediction.
          </div>
        )}
        <div className="mt-1.5">
          <RangeBar id={m.device_id} channel="vibration_rms" range={range} onRange={setRange} />
          <BandChart points={history} band={band} mean={b.learned ? b.mean : null} unit="mm/s" />
        </div>
        <div className="text-[11px] text-ink-2">
          {b.learned ? `Baseline ${b.mean?.toFixed(2)} ± ${b.std?.toFixed(2)} mm/s from ${b.samples} running readings`
            : `Learning baseline: ${b.samples} readings so far (needs ${cfg.baseline_s} s of running)`}
        </div>
      </div>
      <Row k="Units today"><span className="tabular">{m.units_today}{m.rejects_today ? ` · ${m.rejects_today} rejected` : ""}</span></Row>
      <Row k="Last fault">{m.last_fault ? `${m.last_fault.text} · ${ago(m.last_fault.at_ms)}` : "None today"}</Row>
      <Row k="Severity zone">{m.iso_zone ? `ISO 10816 zone ${m.iso_zone}` : "—"}</Row>
      <Row k="OEE"><span className="tabular">{pct(m.oee)} <span className="text-ink-2">(A {pct(m.availability)} · P {pct(m.performance)} · Q {pct(m.quality)})</span></span></Row>
      <Row k="Biggest loss">{biggestLoss(m.losses)}</Row>
    </>
  );
}

const LOSS_LABEL: Record<string, string> = {
  breakdown_s: "Breakdowns", setup_s: "Set-up", starved_s: "Starved", blocked_s: "Blocked", speed_s: "Slow cycles", quality_s: "Scrap",
};

/** The largest OEE loss so far, from the machine's event log (planned stops are not losses). */
function biggestLoss(losses: Record<string, number>): string {
  const [k, v] = Object.entries(losses).filter(([k]) => k in LOSS_LABEL).sort((a, b) => b[1] - a[1])[0] ?? ["", 0];
  return v > 0 ? `${LOSS_LABEL[k]} · ${Math.round(v / 60)} min` : "None yet";
}
