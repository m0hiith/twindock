"""Sanity checks over a long simulated run (R7). Pure simulation core and devices, no backend.

    .venv/bin/python -m sim.validate --hours 4 --seed 7 [--out docs/validation.json]   (from backend/)

The run includes a 10 min grid failure (hour 2) and a 10 min trip of the duty compressor (hour 3).

Checks (each with its tolerance or band and why):
- energy balance: supply (grid + solar + generator + UPS) equals load at every step, and the metered energies agree;
- material conservation: blanks fed = blanks at the infeed + work in progress + good + scrap, at every sample;
- compressor duty: the duty compressor is loaded 30-95 % of the time with production running, load/unload cycles stay
  under 120 an hour (the inlet valve's duty) and motor starts under 6 an hour per compressor (what screw-compressor
  makers allow; the sequencer's start delay and idle stop exist for this);
- OEE: every machine's OEE, folded from its own state log, is within 25-95 % (presses are blocked behind the slower
  packers, so 40-60 % is normal here; world class is ~85 %);
- sensor ranges: no true value was outside what its sensor can report (noise held at a limit, like a stopped
  motor's current reading 0, is normal and only counted);
- causes: every logged event has a cause.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def run(hours: float = 4.0, seed: int = 7, start_hour: float = 6.0, step: float = 0.5) -> dict[str, Any]:
    from site_sim import SITES, SiteSim, select_devices  # type: ignore[import-not-found]

    cfg = json.loads(SITES.read_text())
    s = SiteSim(cfg, select_devices(cfg, None, None), seed=seed)
    s.verbose, s.validate = False, False
    clock = {"h": start_hour}
    s.local_hour = lambda: clock["h"] % 24  # type: ignore[method-assign]
    s.publish = lambda *a, **k: None  # type: ignore[method-assign]
    core = s.core
    prod, air, pw = core.get("production"), core.get("air"), core.get("power")
    states: dict[str, dict[str, float]] = {m.id: {} for m in prod.machines.values()}
    worst_balance = 0.0
    conservation_ok = True
    duty_loaded = duty_total = 0.0
    loads = 0
    supply_kwh = load_kwh = 0.0
    seen = {"events": 0, "without_cause": []}

    def watch(e: Any) -> None:
        seen["events"] += 1
        if not e.cause:
            seen["without_cause"].append(e.name)
    core.listeners.append(watch)
    load_events = [0]
    core.listeners.append(lambda e: load_events.__setitem__(0, load_events[0] + (e.name == "CP-01 loaded")))
    t_wall = time.perf_counter()
    n = int(hours * 3600 / step)
    disturb = {int(3600 / step): ("PM-04", "grid_failure"), int(4200 / step): ("PM-04", "grid_restore"),
               int(7200 / step): ("CP-01", "fault"), int(7800 / step): ("CP-01", "restore")}
    for i in range(n):
        if i in disturb:  # a 10 min grid failure in hour 2 and a 10 min duty-compressor trip in hour 3
            core.command(disturb[i][0], disturb[i][1], {})
        s.step(step)
        clock["h"] += step / 3600
        bal = pw.import_kw + pw.solar_kw + pw.gen_kw + pw.ups_kw - pw.load_kw
        worst_balance = max(worst_balance, abs(bal))
        supply_kwh += (pw.import_kw + pw.solar_kw + pw.gen_kw + pw.ups_kw) * step / 3600
        load_kwh += pw.load_kw * step / 3600
        for m in prod.machines.values():
            states[m.id][m.state] = states[m.id].get(m.state, 0.0) + step
        if core.q.flags.get("shift_phase") == "production":
            duty_total += step
            duty_loaded += step if air.compressors["CP-01"].loaded else 0.0
        if i % 120 == 0:
            good = sum(ln.good for ln in prod.lines.values())
            scrap = sum(ln.scrap for ln in prod.lines.values())
            conservation_ok &= prod.fed == prod.infeed + prod.wip() + good + scrap
        if prod.infeed < 60:  # the twin's forklifts would feed the presses: one raw pallet when they run low
            core.command("MM-01", "feed", {"units": int(core.p.f("production.material.blanks_per_raw_pallet"))})
    loads = load_events[0]
    from twindock.production import oee_from_durations
    oee = {}
    for m in prod.machines.values():
        ideal = core.p.f(f"production.machines.{m.id}.ideal_cycle_s")
        d = {k: v * 1000 for k, v in states[m.id].items()}
        o = oee_from_durations(d, ideal, m.units if m.kind == "packer" else m.units, m.rejects)
        oee[m.id] = None if o["oee"] is None else round(o["oee"], 3)
    clipped = {f"{dev.id}.{ch}": sen.clipped for dev in s.models.values() for ch, sen in dev.sensors.items() if sen.clipped}
    outside = {f"{dev.id}.{ch}": sen.out_of_range for dev in s.models.values() for ch, sen in dev.sensors.items() if sen.out_of_range}
    starts_per_h = {c.id: round(c.starts / hours, 2) for c in air.compressors.values()}
    no_cause = seen["without_cause"]
    duty = duty_loaded / duty_total if duty_total else None
    cycles_per_h = loads / hours
    checks = {
        "energy_balance": {"ok": worst_balance < 1e-6 and abs(supply_kwh - load_kwh) < 1e-3,
                           "worst_kw": worst_balance, "supply_kwh": round(supply_kwh, 2), "load_kwh": round(load_kwh, 2)},
        "material_conservation": {"ok": conservation_ok, "fed": prod.fed, "good": sum(ln.good for ln in prod.lines.values()),
                                  "scrap": sum(ln.scrap for ln in prod.lines.values()), "wip": prod.wip(), "infeed": prod.infeed},
        "compressor_duty": {"ok": duty is not None and 0.3 <= duty <= 0.95 and cycles_per_h <= 120 and all(v <= 6 for v in starts_per_h.values()),
                            "loaded_share": None if duty is None else round(duty, 3), "load_cycles_per_h": round(cycles_per_h, 1),
                            "motor_starts_per_h": starts_per_h},
        "oee_plausible": {"ok": all(v is not None and 0.25 <= v <= 0.95 for v in oee.values()), "oee": oee},
        "sensor_ranges": {"ok": not outside, "true_values_outside_range": outside, "noise_held_at_a_limit": clipped},
        "events_have_causes": {"ok": not no_cause, "events": seen["events"], "without_cause": no_cause[:10]},
    }
    return {"hours": hours, "seed": seed, "start_hour": start_hour, "step_s": step, "wall_s": round(time.perf_counter() - t_wall, 1),
            "all_ok": all(c["ok"] for c in checks.values()), "checks": checks}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=4.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--start-hour", type=float, default=6.0)
    ap.add_argument("--out")
    a = ap.parse_args()
    r = run(a.hours, a.seed, a.start_hour)
    text = json.dumps(r, indent=1)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")
    sys.exit(0 if r["all_ok"] else 1)


if __name__ == "__main__":
    main()
