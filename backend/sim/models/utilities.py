"""Utilities: compressed air, electrical supply (grid, solar, generator) and tanks (true state).

Compressed air is physical: a receiver integrates net flow (compressor delivery − demand − leaks) into pressure, and
the compressor loads and unloads on a pressure band. Demand is what the running machines draw (on the bus).

Electrical: every consumer writes its kW on the bus with its zone. Feeder meters read their zone's sum, the incomer
reads the campus total minus solar, and on a grid failure the generator starts and carries the critical zones only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..core import Model


def day_curve(h: float, start: float, end: float) -> float:
    """0 outside [start, end] (hours), a half sine inside: the shape of daylight or of a working day."""
    return math.sin(math.pi * (h - start) / (end - start)) if start < h < end else 0.0


@dataclass
class Compressor:
    id: str           # device id of its monitor (CP-01)
    zone: str
    loaded: bool = True
    tripped: bool = False
    run_hours: float = 0.0
    delivery_nm3_min: float = 0.0
    power_kw: float = 0.0
    discharge_c: float = 0.0


class CompressedAir(Model):
    key = "air"
    title = "Compressed air (receiver and compressor)"
    equations = (
        "Receiver (isothermal): dP/dt = (Q_compressor − Q_demand − Q_leak) × P_atm / (60 × V_receiver)   [bar/s, flows in Nm³/min].",
        "Load/unload control: the compressor loads at or below the lower band limit and unloads at or above the upper one.",
        "Delivery while loaded = free air delivery (FAD); 0 when unloaded or tripped.",
        "Power: loaded = specific power × FAD; unloaded = unloaded share × loaded power; tripped = 0.",
        "Leaks = leak share × machine demand (+ any injected leak).",
        "Run hours count while loaded (the hour meter on a screw compressor counts loaded hours).",
        "Discharge temperature relaxes towards the loaded or unloaded level with time constant τ.",
    )
    reads = ("air_demand_nm3_min",)
    writes = ("air_pressure_bar", "power_kw")
    params_prefix = ("air",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.compressors = {d["id"]: Compressor(d["id"], d["zone_id"]) for d in cfg["devices"] if d["type"] == "compressor_monitor"}
        self.bar = 0.0
        self.extra_leak = 0.0
        self.demand = 0.0
        self.leak = 0.0
        self.forced: set[str] = set()  # monitors that report at once (after a command)

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        self.bar = (p.f("air.band_low_bar") + p.f("air.band_high_bar")) / 2
        core.q.air_pressure_bar = self.bar  # machines read it before this model's first step
        for c in self.compressors.values():
            c.run_hours = p.f("air.compressor.initial_run_hours")
            c.discharge_c = p.f("air.compressor.discharge_loaded_c")

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        c = self.compressors.get(target)
        if c is None:
            return False
        if action == "leak":
            self.extra_leak = self.core.p.f("air.injected_leak_nm3_min")
        elif action == "fault":
            c.tripped = True
        elif action in ("clear", "restore"):
            self.extra_leak, c.tripped = 0.0, False
        else:
            return False
        self.forced.add(c.id)
        self.core.record(f"{c.id} {action}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        lo, hi = p.f("air.band_low_bar"), p.f("air.band_high_bar")
        self.demand = sum(core.q.air_demand_nm3_min.values())
        self.leak = p.f("air.leak_share") * self.demand + self.extra_leak
        supply = 0.0
        for c in self.compressors.values():
            powered = core.q.powered(c.zone)
            if c.tripped or not powered:
                c.loaded = False
            elif self.bar <= lo and not c.loaded:
                c.loaded = True
                core.record(f"{c.id} loads", f"pressure {self.bar:.2f} bar at the lower limit {lo} bar")
            elif self.bar >= hi and c.loaded:
                c.loaded = False
                core.record(f"{c.id} unloads", f"pressure {self.bar:.2f} bar at the upper limit {hi} bar")
            fad = p.f("air.compressor.fad_nm3_min")
            loaded_kw = p.f("air.compressor.specific_power_kw_per_nm3_min") * fad
            c.delivery_nm3_min = fad if c.loaded else 0.0
            c.power_kw = 0.0 if (c.tripped or not powered) else loaded_kw if c.loaded else loaded_kw * p.f("air.compressor.unloaded_power_share")
            if c.loaded:
                c.run_hours += dt / 3600.0
            target = p.f("air.compressor.discharge_loaded_c") if c.loaded else (
                p.f("air.compressor.discharge_unloaded_c") if c.power_kw > 0 else p.f("air.ambient_c"))
            c.discharge_c += (target - c.discharge_c) * min(1.0, dt / p.f("air.compressor.discharge_tau_s"))
            supply += c.delivery_nm3_min
            core.q.power_kw[c.id] = c.power_kw
            core.q.power_zone[c.id] = c.zone
        net = supply - self.demand - self.leak
        self.bar += net * p.f("air.p_atm_bar") / (60.0 * p.f("air.receiver_m3")) * dt
        self.bar = max(0.0, min(self.bar, p.f("air.safety_valve_bar")))
        core.q.air_pressure_bar = self.bar


class Electrical(Model):
    key = "power"
    title = "Electrical supply (grid, solar, generator)"
    equations = (
        "Zone load = Σ consumers wired in the zone (machines, compressors, conveyors, chargers, pumps, ...) + the zone's fixed load.",
        "Other campus load (lighting, HVAC, offices) = base × (night share + day share × sin(π (h − start) / (end − start))) during the working day.",
        "Solar = installed kWp × performance ratio × sin(π (h − sunrise) / (sunset − sunrise)) in daylight; 0 while the grid is down (no islanding).",
        "Incomer (grid import) = Σ zone loads + other − solar, while the grid is up.",
        "Grid failure: the generator starts and takes the critical zones after its start time; other zones lose power.",
        "Diesel use = generator kW × litres per kWh; the day tank level falls accordingly.",
    )
    reads = ("power_kw", "flags.fire_alarm")
    writes = ("zone_powered",)
    params_prefix = ("power",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.u = cfg.get("utilities") or {}
        self.zones = {z["id"] for s in cfg["sites"] for z in s["zones"]}
        self.grid_down = False
        self.gen_state = "off"  # off | starting | running | cooling
        self.gen_since = 0.0
        self.gen_kw = 0.0
        self.solar_kw = 0.0
        self.other_kw = 0.0
        self.zone_kw: dict[str, float] = {}
        self.import_kw = 0.0
        self.critical: set[str] = set(self.u.get("critical_zones", []))
        self.forced: set[str] = set()  # meters that report at once (the grid just changed)

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        if target != self.u.get("incomer") or action not in ("grid_failure", "grid_restore"):
            return False
        self.grid_down = action == "grid_failure"
        self.forced |= {self.u.get("incomer"), self.u.get("generator"), *(self.u.get("feeders") or {})}
        self.core.record("grid failure" if self.grid_down else "grid restored", f"{action} command at {target}")
        return True

    def sun(self) -> float:
        """Clear-sky shape of the day: 0 outside daylight, a half sine between sunrise and sunset."""
        return day_curve(self.core.hour_of_day(), self.core.p.f("power.solar.sunrise_h"), self.core.p.f("power.solar.sunset_h"))

    def step(self, dt: float) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        if self.grid_down and self.gen_state in ("off", "cooling"):
            self.gen_state, self.gen_since = "starting", t
            core.record("generator starting", "grid failure")
        elif self.grid_down and self.gen_state == "starting" and t - self.gen_since >= p.f("power.generator.start_s"):
            self.gen_state, self.gen_since = "running", t
            core.record("generator running", "start sequence complete")
        elif not self.grid_down and self.gen_state in ("starting", "running"):
            self.gen_state, self.gen_since = "cooling", t
            core.record("generator cooling down", "grid restored")
        elif self.gen_state == "cooling" and t - self.gen_since >= p.f("power.generator.cooldown_s"):
            self.gen_state = "off"
            core.record("generator off", "cool-down complete")
        # which zones have mains power: everything while the grid is up; critical zones keep it (battery back-up
        # covers the generator's start) while it is down.
        for z in self.zones:
            core.q.zone_powered[z] = (not self.grid_down) or z in self.critical
        h = core.hour_of_day()
        day = day_curve(h, p.f("power.other.day_start_h"), p.f("power.other.day_end_h"))
        self.other_kw = p.f("power.other.base_kw") * (p.f("power.other.night_share") + (1 - p.f("power.other.night_share")) * day)
        zone_kw: dict[str, float] = {z: float(kw) for z, kw in (p.v("power.zone_fixed_kw") or {}).items()}
        for name, kw in core.q.power_kw.items():
            z = core.q.power_zone.get(name)
            if z is not None:
                zone_kw[z] = zone_kw.get(z, 0.0) + kw
        total = sum(zone_kw.values()) + self.other_kw
        self.solar_kw = 0.0 if self.grid_down else p.f("power.solar.kwp") * p.f("power.solar.performance_ratio") * self.sun()
        critical_kw = sum(kw for z, kw in zone_kw.items() if z in self.critical) + self.other_kw * p.f("power.other.critical_share")
        if self.grid_down:
            zone_kw = {z: (kw if z in self.critical else 0.0) for z, kw in zone_kw.items()}
        self.zone_kw = zone_kw
        self.import_kw = 0.0 if self.grid_down else max(0.0, total - self.solar_kw)
        self.gen_kw = critical_kw if self.gen_state == "running" else 0.0
        tank = core.by_key.get("tanks")
        diesel = self.u.get("diesel_tank")
        if tank is not None and diesel in tank.tanks and self.gen_kw > 0:
            litres = self.gen_kw * dt / 3600.0 * p.f("power.generator.litres_per_kwh")
            tank.draw(diesel, litres)

    def feeder_kw(self, meter: str) -> float:
        zone = (self.u.get("feeders") or {}).get(meter)
        return self.zone_kw.get(zone, 0.0) if zone else 0.0

    def meter_kw(self, meter: str) -> float:
        if meter == self.u.get("incomer"):
            return self.import_kw
        if meter == self.u.get("generator"):
            return self.gen_kw
        return self.feeder_kw(meter)

    def meter_volts(self, meter: str) -> float:
        p = self.core.p
        if meter == self.u.get("incomer"):
            return 0.0 if self.grid_down else p.f("power.nominal_v")
        if meter == self.u.get("generator"):
            return p.f("power.nominal_v") if self.gen_state == "running" else 0.0
        zone = (self.u.get("feeders") or {}).get(meter)
        return p.f("power.nominal_v") if zone is None or self.core.q.powered(zone) or zone in self.critical and self.gen_state == "running" else 0.0


@dataclass
class Tank:
    id: str
    kind: str
    level_pct: float
    pumping: bool = False


class Tanks(Model):
    key = "tanks"
    title = "Tanks (water, fire water, ETP, diesel day tank)"
    equations = (
        "Level: dL/dt = (fill rate while the pump runs − draw-off) in % per second.",
        "Pump control: starts at the low level, stops at the high level (hysteresis).",
        "Diesel day tank: level falls by the generator's fuel use (litres / tank volume); it is not refilled by a pump here.",
    )
    reads = ()
    writes = ()
    params_prefix = ("tanks",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        diesel = (cfg.get("utilities") or {}).get("diesel_tank")
        self.tanks = {d["id"]: Tank(d["id"], "diesel" if d["id"] == diesel else "water", 0.0)
                      for d in cfg["devices"] if d["type"] == "tank_level"}

    def bind(self, core: Any) -> None:
        super().bind(core)
        for tk in self.tanks.values():
            tk.level_pct = core.p.f(f"tanks.{tk.kind}.initial_pct")

    def draw(self, tank_id: str, litres: float) -> None:
        tk = self.tanks[tank_id]
        tk.level_pct = max(0.0, tk.level_pct - 100.0 * litres / self.core.p.f(f"tanks.{tk.kind}.volume_l"))

    def step(self, dt: float) -> None:
        p = self.core.p
        for tk in self.tanks.values():
            if tk.kind == "diesel":
                tk.pumping = False
                continue
            rate = p.f("tanks.water.fill_pct_per_s") if tk.pumping else -p.f("tanks.water.draw_pct_per_s")
            tk.level_pct = max(0.0, min(100.0, tk.level_pct + rate * dt))
            if tk.level_pct <= p.f("tanks.water.pump_on_pct") and not tk.pumping:
                tk.pumping = True
                self.core.record(f"{tk.id} pump on", f"level {tk.level_pct:.0f} % at the low level")
            elif tk.level_pct >= p.f("tanks.water.pump_off_pct") and tk.pumping:
                tk.pumping = False
                self.core.record(f"{tk.id} pump off", f"level {tk.level_pct:.0f} % at the high level")


class CampusLoads(Model):
    """Loads that are not machines: EV chargers by time of day, the fire pump during a fire alarm."""
    key = "loads"
    title = "Other campus loads (EV chargers, fire pump)"
    equations = (
        "EV chargers = base + peak × sin(π (h − start) / (end − start)) while people are at work.",
        "Fire pump = rated kW while any fire panel reports an alarm, standby kW otherwise.",
    )
    reads = ("flags.fire_alarm",)
    writes = ("power_kw",)
    params_prefix = ("loads",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        zones = {z["id"]: z for s in cfg["sites"] for z in s["zones"]}
        self.ev_zone = next((z for z in zones if z.endswith("PARKING")), None)
        self.pump_zone = next((z for z in zones if z.endswith("FIREPUMP")), None)

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        h = core.hour_of_day()
        if self.ev_zone:
            day = day_curve(h, p.f("loads.ev.start_h"), p.f("loads.ev.end_h"))
            core.q.power_kw["EV chargers"] = p.f("loads.ev.base_kw") + p.f("loads.ev.peak_kw") * day
            core.q.power_zone["EV chargers"] = self.ev_zone
        if self.pump_zone:
            fire = bool(core.q.flags.get("fire_alarm"))
            core.q.power_kw["Fire pump"] = p.f("loads.fire_pump.rated_kw") if fire else p.f("loads.fire_pump.standby_kw")
            core.q.power_zone["Fire pump"] = self.pump_zone
