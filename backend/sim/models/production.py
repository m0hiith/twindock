"""Production lines (true state): shift calendar, machines, buffers and material, failures and wear, machine physics.

Two lines share the press infeed (raw blanks, fed a pallet at a time by the twin's forklifts) and each runs
press → buffer → packer → outfeed. A machine starts a cycle only when it has input and somewhere to put its output,
so starving and blocking come from the buffers, not from dice. Shifts, breaks, start-up and handover come from the
calendar. Failures come from Weibull times-to-failure in operating time; a bearing wears slowly then faster, raises
vibration as it goes and fails when its wear reaches its own limit, so a rising vibration really does predict a
breakdown. Material is conserved: blanks in = blanks waiting + parts in machines and buffers + good + scrap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..core import Model


# ====================================================================== shift calendar

def shift_phase(p: Any, h: float) -> tuple[str, str]:
    """(shift, phase) at local hour h from the calendar in params: setup, production, break, handover or closed."""
    for sh in p.v("production.shifts.calendar"):
        start, end = float(sh["start_h"]), float(sh["end_h"])
        span = (end - start) % 24
        since = (h - start) % 24
        if since >= span:
            continue
        name = str(sh["name"])
        if since * 60 < p.f("production.shifts.startup_min"):
            return name, "setup"
        if (span - since) * 60 <= p.f("production.shifts.handover_min"):
            return name, "handover"
        for a, b in sh["breaks"]:
            if (h - a) % 24 < (b - a) % 24:
                return name, "break"
        return name, "production"
    return "none", "closed"


class Shifts(Model):
    key = "shifts"
    title = "Shift calendar"
    equations = (
        "Three 8-hour shifts. In each: start-up (set-up) for the first minutes, then production with fixed breaks, "
        "then a handover (cleaning, hand-over notes) before the next shift.",
        "Lines stop in breaks and handovers (planned stops) and set up at the start of each shift.",
    )
    writes = ("flags.shift", "flags.shift_phase")
    params_prefix = ("production.shifts",)

    def phase(self, h: float) -> tuple[str, str]:
        return shift_phase(self.core.p, h)

    def step(self, dt: float) -> None:
        name, ph = self.phase(self.core.hour_of_day())
        q = self.core.q.flags
        if q.get("shift_phase") != ph or q.get("shift") != name:
            if "shift_phase" in q:
                self.core.record(f"shift {name}: {ph}", "shift calendar")
            q["shift"], q["shift_phase"] = name, ph


# ====================================================================== machines and lines

@dataclass
class Machine:
    id: str          # M-01
    device: str      # MM-01 (its monitor)
    kind: str        # press | packer
    line: int
    zone: str
    state: str = "planned_stop"
    cycle_end: float | None = None   # a cycle in progress ends at this time
    holding: bool = False            # a finished part waiting for room downstream
    units: int = 0                   # good output (press: parts made; packer: good cartons)
    rejects: int = 0
    cycles: int = 0
    last_cycle_s: float | None = None
    stop_until: float = 0.0          # fault or maintenance ends
    alarm: str | None = None
    # wear and failures
    wear: float = 0.0                # bearing wear, 0 new … 1 worn out (each bearing has its own limit)
    wear_limit: float = 1.0
    defect_rate: float = 0.0         # extra wear rate from a seeded defect (the demo's "degrade")
    op_s: float = 0.0                # operating seconds since the last minor stop
    next_minor_s: float = 0.0        # operating seconds to the next minor stop (Weibull)
    surface_c: float = 0.0
    unpowered: bool = False
    air_stopped: bool = False
    events: list[tuple[str, Any]] = field(default_factory=list)  # (channel, value) the monitor reports at once


@dataclass
class Line:
    n: int
    press: str        # device ids
    packer: str
    buffer: int = 0   # parts between press and packer
    good: int = 0     # good cartons out of the packer (to the palletiser)
    scrap: int = 0


class Production(Model):
    key = "production"
    title = "Production lines (machines, buffers, material, failures, wear)"
    equations = (
        "A machine starts a cycle when it has input (press: a blank at the infeed; packer: a part in the buffer) and is not holding "
        "a finished part. Without input it is starved; holding a part with a full buffer, it is blocked.",
        "Cycle time = ideal cycle × lognormal(1, σ) × (1 + wear slowdown × wear) × air factor; each packer cycle is scrap with the scrap rate.",
        "Shift calendar: set-up at shift start, planned stop in breaks and handovers.",
        "Minor stops (jams): operating time between them is Weibull(β, η); the scale shrinks with wear: η × (1 − k × wear). "
        "Repair time is lognormal (median MTTR).",
        "Bearing wear (running only): dw/dt = r × (1 + a × w) + defect rate, so it grows slowly, then faster; the bearing fails when w "
        "reaches its own limit (normal around 1). The repair fits a new bearing.",
        "Vibration RMS = healthy level × load factor + wear amplitude × w²; ISO 10816 zones in the twin.",
        "Motor current = rated while cycling (+ a little with wear); idle share while set-up, starved or blocked; 0 when stopped.",
        "Surface temperature: dT/dt = (ambient + ΔT_rated × (I / I_rated)² + k_wear × w − T) / τ.",
        "Electrical load = √3 × V × I × PF / 1000; compressed air while cycling. A shed zone stops its machines; "
        "below the air trip pneumatic machines stop with \"Low air pressure\".",
    )
    reads = ("air_pressure_bar", "flags.air_trip", "flags.shift_phase", "zone_powered")
    writes = ("power_kw", "air_demand_nm3_min")
    params_prefix = ("production",)

    def __init__(self, cfg: dict[str, Any], line_machines: list[dict[str, Any]]) -> None:
        by_unit = {d.get("attached_to"): d for d in cfg["devices"] if d["type"] == "machine_monitor"}
        self.machines: dict[str, Machine] = {}
        for m in line_machines:
            d = by_unit.get(m["id"])
            if d is None:
                continue
            self.machines[d["id"]] = Machine(m["id"], d["id"], m["kind"], int(m.get("line", 1)), d["zone_id"])
        self.lines: dict[int, Line] = {}
        for n in sorted({m.line for m in self.machines.values()}):
            press = next(m.device for m in self.machines.values() if m.line == n and m.kind == "press")
            packer = next(m.device for m in self.machines.values() if m.line == n and m.kind == "packer")
            self.lines[n] = Line(n, press, packer)
        self.conveyors = {d["id"]: {"jam_until": -1.0, "zone": d["zone_id"]} for d in cfg["devices"] if d["type"] == "conveyor_monitor"}
        self.infeed = 0          # raw blanks at the presses' infeed (shared by both lines)
        self.fed = 0             # blanks ever fed (initial kit + pallets from the twin)
        self.air_factor = 1.0

    # ------------------------------------------------------------------ setup

    def mp(self, m: Machine, name: str) -> Any:
        return self.core.p.v(f"production.machines.{m.id}.{name}")

    def mf(self, m: Machine, name: str) -> float:
        return self.core.p.f(f"production.machines.{m.id}.{name}")

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        self.infeed = self.fed = int(p.f("production.material.initial_kit_blanks"))
        for m in self.machines.values():
            m.surface_c = p.f("production.ambient_c")
            m.wear = core.rng.draw("production.wear.initial", f"{m.device}.wear")
            m.wear_limit = core.rng.draw("production.wear.limit", f"{m.device}.wear")
            m.next_minor_s = self._draw_minor(m)

    def _draw_minor(self, m: Machine) -> float:
        k = self.core.p.f("production.failures.wear_shortens_by")
        floor = self.core.p.f("production.failures.min_scale_share")
        return float(self.core.rng.draw("production.failures.minor_ttf_s", f"{m.device}.minor", scale=max(floor, 1 - k * m.wear)))

    # ------------------------------------------------------------------ commands

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        p = self.core.p
        m = self.machines.get(target)
        if m is not None:
            if action == "degrade":
                m.defect_rate = p.f("production.wear.demo_defect_rate_per_s")
                self.core.record(f"{m.id} bearing defect", "degrade command (demo)")
            elif action == "restore":
                m.defect_rate, m.wear = 0.0, p.f("production.wear.new")
                self.core.record(f"{m.id} bearing restored", "restore command (demo)")
            elif action == "maintenance":
                self._stop(m, "maintenance", p.f("production.maintenance_s"), "maintenance command")
            elif action == "repair":  # a work order's repair (R5): a new bearing, fitted in the given time
                secs = float(data.get("seconds", p.f("production.maintenance_s")))
                m.defect_rate, m.wear = 0.0, p.f("production.wear.new")
                m.wear_limit = self.core.rng.draw("production.wear.limit", f"{m.device}.wear")
                self._stop(m, "maintenance", secs, "work order: bearing replaced")
            elif action == "feed":  # a raw pallet dropped at the press infeed by the twin's forklift
                n = int(data.get("units", p.f("production.material.blanks_per_raw_pallet")))
                self.infeed += n
                self.fed += n
                self.core.record("raw pallet at the press infeed", f"forklift dropped a pallet ({n} blanks)")
            else:
                return False
            return True
        cv = self.conveyors.get(target)
        if cv is not None and action == "jam":
            cv["jam_until"] = self.core.t + p.f("production.conveyor.jam_s")
            self.core.record(f"{target} jam", "jam command")
            return True
        return False

    # ------------------------------------------------------------------ state and material

    def _set(self, m: Machine, state: str, cause: str) -> None:
        if state == m.state:
            return
        m.state = state
        m.events.append(("state", state))
        self.core.record(f"{m.id} {state.replace('_', ' ')}", cause)

    def _stop(self, m: Machine, state: str, secs: float, cause: str, alarm: str | None = None) -> None:
        """Fault or maintenance for secs. A cycle in progress goes back to its input: nothing is made or scrapped."""
        if m.cycle_end is not None:
            self._return_input(m)
            m.cycle_end = None
        m.stop_until = self.core.t + secs
        if state == "fault":
            m.alarm = alarm
            m.events.append(("alarm", alarm))
        self._set(m, state, cause)

    def _return_input(self, m: Machine) -> None:
        if m.kind == "press":
            self.infeed += 1
        else:
            self.lines[m.line].buffer += 1

    def _take_input(self, m: Machine) -> bool:
        ln = self.lines[m.line]
        if m.kind == "press":
            if self.infeed > 0:
                self.infeed -= 1
                return True
            return False
        if ln.buffer > 0:
            ln.buffer -= 1
            return True
        return False

    def _push_output(self, m: Machine) -> bool:
        """Hand the finished part on. Press: into the buffer if there is room. Packer: to the palletiser (the twin's
        outbound spot and its backlog take the pallets, so it is never full here)."""
        ln = self.lines[m.line]
        if m.kind == "press":
            if ln.buffer >= int(self.core.p.f("production.material.buffer_capacity")):
                return False
            ln.buffer += 1
            m.units += 1
            m.events.append(("units", m.units))
            return True
        if self.core.rng.chance(f"{m.device}.scrap", self.mf(m, "scrap_rate")):
            m.rejects += 1
            ln.scrap += 1
            m.events.append(("rejects", m.rejects))
        else:
            m.units += 1
            ln.good += 1
            m.events.append(("units", m.units))
        return True

    def wip(self) -> int:
        """Parts inside the lines: buffers, cycles in progress, finished parts held."""
        return sum(ln.buffer for ln in self.lines.values()) + sum(1 for m in self.machines.values() if m.cycle_end is not None or m.holding)

    # ------------------------------------------------------------------ physics

    def current_a(self, m: Machine) -> float:
        p = self.core.p
        if m.state == "running":
            return self.mf(m, "rated_current_a") + p.f("production.wear.extra_current_a") * m.wear
        if m.state in ("starved", "blocked", "setup"):
            return p.f("production.idle_current_share") * self.mf(m, "rated_current_a")
        return 0.0

    def vibration(self, m: Machine) -> float:
        p = self.core.p
        healthy = self.mf(m, "healthy_vibration_mm_s")
        wear = p.f("production.wear.vibration_mm_s_at_limit") * m.wear ** 2
        if m.state == "running":
            return healthy + wear
        if m.state in ("starved", "blocked", "setup"):
            return (healthy + wear) * p.f("production.idle_vibration_share")
        return p.f("production.stopped_vibration_mm_s")

    def conveyor_jammed(self, dev: str) -> bool:
        return self.core.t < self.conveyors[dev]["jam_until"]

    def conveyor_current_a(self, dev: str) -> float:
        p = self.core.p
        return p.f("production.conveyor.jam_current_a") if self.conveyor_jammed(dev) else p.f("production.conveyor.run_current_a")

    def conveyor_speed(self, dev: str) -> float:
        return 0.0 if self.conveyor_jammed(dev) else self.core.p.f("production.conveyor.belt_speed_m_s")

    # ------------------------------------------------------------------ step

    def _machine(self, m: Machine, dt: float, phase: str, trip: bool) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        if not core.q.powered(m.zone):
            if not m.unpowered:
                m.unpowered = True
                if m.cycle_end is not None:
                    self._return_input(m)
                    m.cycle_end = None
                self._set(m, "planned_stop" if m.state == "planned_stop" else "fault", "no mains power in the production zone (load shed)")
            return
        if m.unpowered:
            m.unpowered = False
            m.stop_until = t
            self._set(m, "starved", "mains power restored")
        if trip and float(self.mp(m, "air_nm3_min")) > 0 and not m.air_stopped and m.state not in ("planned_stop", "maintenance"):
            m.air_stopped = True
            self._stop(m, "fault", math.inf, "low air pressure trip", alarm=str(p.v("production.air.trip_alarm")))
            return
        if m.air_stopped:
            if trip:
                return
            m.air_stopped = False
            m.stop_until = t
        if m.state in ("fault", "maintenance") and t < m.stop_until:
            return
        if m.state in ("fault", "maintenance"):
            if m.state == "fault" and m.wear >= m.wear_limit:  # the repair after a bearing failure fits a new bearing
                m.wear, m.defect_rate = p.f("production.wear.new"), 0.0  # (the defect went with the old one)
                m.wear_limit = core.rng.draw("production.wear.limit", f"{m.device}.wear")
            m.alarm = None
            self._set(m, "starved", "repair complete" if m.state == "fault" else "maintenance complete")
        idle_phase = phase in ("break", "handover", "closed")
        if (idle_phase or phase == "setup") and m.cycle_end is None and not m.holding:
            self._set(m, "setup" if phase == "setup" else "planned_stop", "shift start-up" if phase == "setup" else f"shift {phase}")
            return
        if m.cycle_end is not None:
            # wear and failures accumulate while cycling
            rate = p.f("production.wear.rate_per_s") * (1 + p.f("production.wear.acceleration") * m.wear) + m.defect_rate
            m.wear = min(p.f("production.wear.max"), m.wear + rate * dt)
            m.op_s += dt
            if m.wear >= m.wear_limit:
                self._stop(m, "fault", core.rng.draw("production.failures.bearing_ttr_s", f"{m.device}.ttr"),
                           f"bearing worn out (wear {m.wear:.2f} at its limit {m.wear_limit:.2f})", alarm=str(p.v("production.failures.bearing_alarm")))
                return
            if m.op_s >= m.next_minor_s:
                alarms = list(self.mp(m, "alarms"))
                alarm = alarms[int(core.rng.stream(f"{m.device}.alarm").random() * len(alarms))]
                m.op_s, m.next_minor_s = 0.0, self._draw_minor(m)
                self._stop(m, "fault", core.rng.draw("production.failures.minor_ttr_s", f"{m.device}.ttr"),
                           f"minor stop after its Weibull operating time ({alarm})", alarm=alarm)
                return
            if t >= m.cycle_end:
                m.cycle_end = None
                m.holding = True
                m.cycles += 1
        if m.holding:
            if not self._push_output(m):
                self._set(m, "blocked", "buffer full downstream")
                return
            m.holding = False
            if m.last_cycle_s is not None:
                m.events.append(("cycle_time_s", round(m.last_cycle_s, 2)))
        if m.cycle_end is None:
            if idle_phase or phase == "setup":
                self._set(m, "setup" if phase == "setup" else "planned_stop", "shift start-up" if phase == "setup" else f"shift {phase}")
                return
            if not self._take_input(m):
                self._set(m, "starved", "no blanks at the infeed" if m.kind == "press" else "buffer empty upstream")
                return
            var = core.rng.draw("production.cycle_variation", f"{m.device}.cycle")
            took = self.mf(m, "ideal_cycle_s") * var * (1 + p.f("production.wear.slowdown") * m.wear) * self.air_factor
            m.cycle_end, m.last_cycle_s = t + took, took
            self._set(m, "running", "input available")

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        bar = core.q.air_pressure_bar
        low = p.f("production.air.slow_below_bar")
        self.air_factor = 1.0 if bar >= low else min(p.f("production.air.max_factor"), 1.0 + (low - bar) * p.f("production.air.factor_per_bar"))
        kw_per_a = 3 ** 0.5 * p.f("production.supply_v") * p.f("production.power_factor") / 1000.0
        trip = bool(core.q.flags.get("air_trip"))
        phase = str(core.q.flags.get("shift_phase", "production"))
        for m in self.machines.values():
            self._machine(m, dt, phase, trip)
            i = self.current_a(m)
            target = p.f("production.ambient_c") + p.f("production.thermal.rise_at_rated_c") * (i / self.mf(m, "rated_current_a")) ** 2 \
                + p.f("production.thermal.k_wear_c") * m.wear
            m.surface_c += (target - m.surface_c) * min(1.0, dt / p.f("production.thermal.tau_s"))
            core.q.power_kw[m.id] = kw_per_a * i
            core.q.power_zone[m.id] = m.zone
            core.q.power_kind[m.id] = "motor"
            core.q.air_demand_nm3_min[m.id] = float(self.mp(m, "air_nm3_min")) if m.state == "running" else 0.0
        for dev, cv in self.conveyors.items():
            on = core.q.powered(cv["zone"])
            core.q.power_kw[dev] = kw_per_a * self.conveyor_current_a(dev) if on else 0.0
            core.q.power_zone[dev] = cv["zone"]
            core.q.power_kind[dev] = "motor"
