"""Production line machines and conveyors (true state).

R0 port of the original machine monitor story, with every number in params/production.yaml: a machine alternates
between running and short idle or fault spells drawn from named distributions; while running it completes cycles
(ideal cycle time × a small variation × wear × compressed-air shortage), each cycle good or scrap. Motor current,
surface temperature and vibration RMS are true physical values here; the machine monitor's sensors add noise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..core import Model


@dataclass
class Machine:
    id: str          # M-01
    device: str      # MM-01 (its monitor)
    kind: str        # press | packer
    line: int
    zone: str
    state: str = "running"
    state_until: float = 0.0
    units: int = 0
    rejects: int = 0
    next_cycle: float = 0.0
    last_cycle_s: float | None = None
    vib_offset: float = 0.0      # mm/s added by wear (bearing)
    degrade_rate: float = 0.0    # mm/s per s while degrading (demo command)
    surface_c: float = 0.0
    alarm: str | None = None
    unpowered: bool = False      # its zone has no mains power (grid failure): stopped, nothing drawn
    air_stopped: bool = False    # stopped by the low air pressure trip
    events: list[tuple[str, Any]] = field(default_factory=list)  # (channel, value) the monitor reports at once


class Production(Model):
    key = "production"
    title = "Production line machines"
    equations = (
        "State: running for a drawn dwell, then idle (starved) or fault with fixed probabilities, then running again; "
        "maintenance only on command.",
        "Cycle time = ideal cycle × U(1, 1 + variation) × (1 + wear_slowdown × vibration offset) × air factor.",
        "Each cycle is scrap with probability = scrap rate, otherwise a good unit.",
        "Motor current = rated current while running, idle current while idle, 0 otherwise; + wear_current × offset.",
        "Surface temperature: dT/dt = (ambient + k_current × I + k_wear × offset − T) / τ.",
        "Vibration RMS = healthy level + wear offset while running; a small residual when stopped.",
        "Electrical load (kW) = √3 × V × I × PF / 1000 per machine; compressed air (Nm³/min) while running.",
        "Without mains power (a shed zone in a grid failure) a machine stops and draws nothing; it restarts when power returns.",
        "Below the air trip pressure a pneumatic machine stops with \"Low air pressure\" and restarts when the pressure recovers.",
    )
    reads = ("air_pressure_bar", "flags.air_trip", "zone_powered")
    writes = ("power_kw", "air_demand_nm3_min")
    params_prefix = ("production",)

    def __init__(self, cfg: dict[str, Any], line_machines: list[dict[str, Any]]) -> None:
        self.cfg = cfg
        by_unit = {d.get("attached_to"): d for d in cfg["devices"] if d["type"] == "machine_monitor"}
        self.machines: dict[str, Machine] = {}
        for m in line_machines:
            d = by_unit.get(m["id"])
            if d is None:
                continue
            self.machines[d["id"]] = Machine(m["id"], d["id"], m["kind"], int(m.get("line", 1)), d["zone_id"])
        self.conveyors = {d["id"]: {"jam_until": -1.0, "zone": d["zone_id"]} for d in cfg["devices"] if d["type"] == "conveyor_monitor"}
        self.air_factor = 1.0

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        for m in self.machines.values():
            m.surface_c = p.f("production.ambient_c")
            m.state_until = core.rng.draw("production.state.first_dwell_s", f"{m.device}.dwell")

    def mp(self, m: Machine, name: str) -> Any:
        return self.core.p.v(f"production.machines.{m.id}.{name}")

    def set_state(self, m: Machine, state: str, dwell: float, cause: str, alarm: str | None = None) -> None:
        m.state, m.state_until = state, self.core.t + dwell
        m.events.append(("state", state))
        if state == "fault":
            alarms = list(self.mp(m, "alarms"))
            m.alarm = alarm or alarms[int(self.core.rng.stream(f"{m.device}.alarm").random() * len(alarms))]
            m.events.append(("alarm", m.alarm))
        if state == "running":
            m.next_cycle = self.core.t + float(self.mp(m, "ideal_cycle_s"))
        self.core.record(f"{m.id} {state}", cause)

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        m = self.machines.get(target)
        if m is not None:
            if action == "degrade":
                m.degrade_rate = self.core.p.f("production.demo_degrade_rate_mm_s_per_s")
            elif action == "restore":
                m.degrade_rate, m.vib_offset = 0.0, 0.0
            elif action == "maintenance":
                self.set_state(m, "maintenance", self.core.p.f("production.maintenance_s"), "maintenance command")
            else:
                return False
            return True
        cv = self.conveyors.get(target)
        if cv is not None and action == "jam":
            cv["jam_until"] = self.core.t + self.core.p.f("production.conveyor.jam_s")
            self.core.record(f"{target} jam", "jam command")
            return True
        return False

    def current_a(self, m: Machine) -> float:
        p = self.core.p
        if m.state == "running":
            return float(self.mp(m, "rated_current_a")) + p.f("production.wear_current_a_per_mm_s") * m.vib_offset
        if m.state == "idle":
            return p.f("production.idle_current_a")
        return 0.0

    def vibration(self, m: Machine) -> float:
        if m.state == "running":
            return float(self.mp(m, "healthy_vibration_mm_s")) + m.vib_offset
        return self.core.p.f("production.stopped_vibration_mm_s")

    def conveyor_jammed(self, dev: str) -> bool:
        return self.core.t < self.conveyors[dev]["jam_until"]

    def conveyor_current_a(self, dev: str) -> float:
        p = self.core.p
        return p.f("production.conveyor.jam_current_a") if self.conveyor_jammed(dev) else p.f("production.conveyor.run_current_a")

    def conveyor_speed(self, dev: str) -> float:
        return 0.0 if self.conveyor_jammed(dev) else self.core.p.f("production.conveyor.belt_speed_m_s")

    def step(self, dt: float) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        bar = core.q.air_pressure_bar
        low = p.f("production.air.slow_below_bar")
        self.air_factor = 1.0 if bar >= low else min(p.f("production.air.max_factor"), 1.0 + (low - bar) * p.f("production.air.factor_per_bar"))
        kw_per_a = 3 ** 0.5 * p.f("production.supply_v") * p.f("production.power_factor") / 1000.0
        trip = bool(core.q.flags.get("air_trip"))
        for m in self.machines.values():
            core.q.power_zone[m.id] = m.zone
            core.q.power_kind[m.id] = "motor"
            if not core.q.powered(m.zone):
                if not m.unpowered:
                    m.unpowered = True
                    core.record(f"{m.id} stopped", "no mains power in the production zone (load shed)")
                core.q.power_kw[m.id] = 0.0
                core.q.air_demand_nm3_min[m.id] = 0.0
                continue
            if m.unpowered:
                m.unpowered = False
                self.set_state(m, "running", core.rng.draw("production.state.running_dwell_s", f"{m.device}.dwell"), "mains power restored")
            uses_air = float(self.mp(m, "air_nm3_min")) > 0
            if trip and uses_air and not m.air_stopped and m.state in ("running", "idle"):
                m.air_stopped = True
                self.set_state(m, "fault", math.inf, "low air pressure trip", alarm=str(p.v("production.air.trip_alarm")))
            elif m.air_stopped and not trip:
                m.air_stopped = False
                self.set_state(m, "running", core.rng.draw("production.state.running_dwell_s", f"{m.device}.dwell"), "air pressure recovered")
            if t >= m.state_until and m.state != "running":
                self.set_state(m, "running", core.rng.draw("production.state.running_dwell_s", f"{m.device}.dwell"), f"{m.state} spell ended")
            elif t >= m.state_until:
                r = core.rng.stream(f"{m.device}.next").random()
                if r < p.f("production.state.p_fault"):
                    self.set_state(m, "fault", core.rng.draw("production.state.fault_dwell_s", f"{m.device}.dwell"), "random fault (R0 model)")
                elif r < p.f("production.state.p_fault") + p.f("production.state.p_idle"):
                    self.set_state(m, "idle", core.rng.draw("production.state.idle_dwell_s", f"{m.device}.dwell"), "starved (R0 model)")
                else:
                    m.state_until = t + core.rng.draw("production.state.running_dwell_s", f"{m.device}.dwell")
            m.vib_offset += m.degrade_rate * dt
            if m.state == "running" and t >= m.next_cycle:
                var = core.rng.stream(f"{m.device}.cycle").uniform(1.0, 1.0 + p.f("production.cycle_variation"))
                took = float(self.mp(m, "ideal_cycle_s")) * var * (1 + p.f("production.wear_slowdown_per_mm_s") * m.vib_offset) * self.air_factor
                m.next_cycle = t + took
                m.last_cycle_s = took
                if core.rng.chance(f"{m.device}.scrap", float(self.mp(m, "scrap_rate"))):
                    m.rejects += 1
                    m.events.append(("rejects", m.rejects))
                else:
                    m.units += 1
                    m.events.append(("units", m.units))
                m.events.append(("cycle_time_s", round(took, 2)))
            i = self.current_a(m)
            target = p.f("production.ambient_c") + p.f("production.thermal.k_current_c_per_a") * i + p.f("production.thermal.k_wear_c_per_mm_s") * m.vib_offset
            m.surface_c += (target - m.surface_c) * min(1.0, dt / p.f("production.thermal.tau_s"))
            core.q.power_kw[m.id] = kw_per_a * i
            core.q.air_demand_nm3_min[m.id] = float(self.mp(m, "air_nm3_min")) if m.state == "running" else 0.0
        for dev, cv in self.conveyors.items():
            on = core.q.powered(cv["zone"])
            core.q.power_kw[dev] = kw_per_a * self.conveyor_current_a(dev) if on else 0.0
            core.q.power_zone[dev] = cv["zone"]
            core.q.power_kind[dev] = "motor"
