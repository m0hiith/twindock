"""Utilities: compressed air, electrical supply, water and effluent, other campus loads (true state).

Compressed air: a duty and a standby screw compressor on load/unload control feed one receiver; the receiver
integrates net flow (delivery − machine demand − leaks) into pressure. The standby starts when pressure falls below
its start level and stops after running unloaded for a while. Below the trip level pneumatic machines stop.

Electrical: every consumer writes its kW (and what kind of load it is, for the power factor) on the bus with its
zone. The incomer carries what the grid supplies, the PV meter what the roof makes, the generator what the critical
bus draws while the transfer switch is on generator. A grid failure runs the auto-mains-failure sequence: confirm,
crank, accelerate, transfer; the grid's return runs retransfer and a cool-down.

Water: tanks with pump control; demand from the canteen (meal times), cooling-tower make-up (from the heat the
machines and compressors reject) and process water per unit made; effluent to the ETP equalisation tank, treated
at the ETP's capacity, with outflow quality that worsens under hydraulic overload.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..core import Model


def day_curve(h: float, start: float, end: float) -> float:
    """0 outside [start, end] (hours), a half sine inside: the shape of daylight or of a working day."""
    return math.sin(math.pi * (h - start) / (end - start)) if start < h < end else 0.0


# ====================================================================== weather

class Weather(Model):
    key = "weather"
    title = "Outdoor weather (temperature, cloud)"
    equations = (
        "Outdoor temperature = mean + amplitude × cos(2π (h − warmest hour) / 24): a daily cycle.",
        "Cloud factor (share of clear-sky sun reaching the panels) follows a mean-reverting random process: "
        "dc = θ (mean − c) dt + σ dW, kept between its minimum and 1.",
    )
    writes = ("flags.outdoor_c", "flags.cloud")
    params_prefix = ("weather",)

    def bind(self, core: Any) -> None:
        super().bind(core)
        self.cloud = core.p.f("weather.cloud.mean")

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        h = core.hour_of_day()
        outdoor = p.f("weather.mean_c") + p.f("weather.amplitude_c") * math.cos(2 * math.pi * (h - p.f("weather.warmest_h")) / 24)
        th, sg = p.f("weather.cloud.theta_per_s"), p.f("weather.cloud.sigma_per_sqrt_s")
        self.cloud += th * (p.f("weather.cloud.mean") - self.cloud) * dt + core.rng.gauss("weather.cloud", sg) * math.sqrt(dt)
        self.cloud = max(p.f("weather.cloud.min"), min(1.0, self.cloud))
        core.q.flags["outdoor_c"] = outdoor
        core.q.flags["cloud"] = self.cloud


# ====================================================================== compressed air

@dataclass
class Compressor:
    id: str           # device id of its monitor (CP-01)
    zone: str
    role: str         # duty | standby
    state: str = "stopped"   # stopped | starting | unloaded | loaded
    low_since: float | None = None  # standby: when pressure first fell below its start level
    tripped: bool = False
    run_hours: float = 0.0   # loaded hours (what a screw compressor's hour meter counts)
    service_hours: float = 0.0  # loaded hours since the last service
    unloaded_since: float = 0.0
    delivery_nm3_min: float = 0.0
    power_kw: float = 0.0
    discharge_c: float = 0.0
    starts: int = 0
    service_until: float = -1.0

    @property
    def loaded(self) -> bool:
        return self.state == "loaded"


class CompressedAir(Model):
    key = "air"
    title = "Compressed air (duty and standby compressors, receiver)"
    equations = (
        "Receiver (isothermal): dP/dt = (Σ Q_compressors − Q_demand − Q_leak) × P_atm / (60 × V_receiver)   [bar/s, flows in Nm³/min].",
        "Each running compressor loads at or below its lower band limit and unloads at or above its upper one.",
        "The standby compressor starts when pressure has stayed below its start level for the sequencer's start delay; "
        "its motor then runs up (star-delta) before it loads. It stops after running unloaded for its idle time.",
        "Delivery while loaded = free air delivery (FAD); 0 when unloaded, stopped or tripped.",
        "Power: loaded = specific power × FAD; unloaded = unloaded share × loaded power; stopped or tripped = 0.",
        "Leaks bleed all the time, like orifices: Q_leak = leak flow at 7 bar × (P / 7 bar); the leak flow grows slowly "
        "with time since the last leak-fix work order, which brings it back down.",
        "Below the trip pressure pneumatic machines stop (low air pressure) until it recovers above the reset pressure.",
        "Discharge temperature relaxes towards the loaded or unloaded level with time constant τ.",
    )
    reads = ("air_demand_nm3_min", "zone_powered")
    writes = ("air_pressure_bar", "power_kw", "flags.air_trip")
    params_prefix = ("air",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.compressors = {d["id"]: Compressor(d["id"], d["zone_id"], "duty") for d in cfg["devices"] if d["type"] == "compressor_monitor"}
        self.bar = 0.0
        self.extra_leak = 0.0
        self.demand = 0.0
        self.leak = 0.0
        self.leak_ref = 0.0   # leak flow (Nm³/min) at the reference pressure
        self.supply = 0.0
        self.trip = False
        self.forced: set[str] = set()  # monitors that report at once (after a command)

    def cp(self, c: Compressor, name: str) -> float:
        return self.core.p.f(f"air.compressors.{c.id}.{name}")

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        for c in self.compressors.values():
            c.role = str(p.v(f"air.compressors.{c.id}.role"))
            c.run_hours = self.cp(c, "initial_run_hours")
            c.service_hours = self.cp(c, "initial_hours_since_service")
            c.discharge_c = p.f("air.ambient_c")
            c.state = "loaded" if c.role == "duty" else "stopped"
        self.bar = (p.f("air.duty_band_low_bar") + p.f("air.duty_band_high_bar")) / 2
        self.leak_ref = p.f("air.leaks.initial_nm3_min")
        core.q.air_pressure_bar = self.bar  # machines read it before this model's first step

    def band(self, c: Compressor) -> tuple[float, float]:
        p = self.core.p
        if c.role == "duty":
            return p.f("air.duty_band_low_bar"), p.f("air.duty_band_high_bar")
        return p.f("air.standby_band_low_bar"), p.f("air.standby_band_high_bar")

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        c = self.compressors.get(target)
        if c is None:
            return False
        if action == "leak":
            self.extra_leak = self.core.p.f("air.leaks.injected_nm3_min")
        elif action == "fault":
            c.tripped = True
        elif action in ("clear", "restore"):
            self.extra_leak, c.tripped = 0.0, False
        elif action == "fix_leaks":
            self.extra_leak, self.leak_ref = 0.0, self.core.p.f("air.leaks.after_fix_nm3_min")
        elif action == "service":  # a service stops this compressor for the job's time (the other one covers)
            c.service_until = self.core.t + float(data.get("seconds", self.core.p.f("air.service_default_s")))
            c.service_hours = 0.0
        else:
            return False
        self.forced.add(c.id)
        self.core.record(f"{c.id} {action}", f"{action} command")
        return True

    def set_state(self, c: Compressor, state: str, cause: str) -> None:
        if state == c.state:
            return
        if c.state == "stopped":
            c.starts += 1
        if state in ("unloaded", "starting"):
            c.unloaded_since = self.core.t
        if state == "stopped":
            c.low_since = None
        c.state = state
        self.forced.add(c.id)
        self.core.record(f"{c.id} {state}", cause)

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        self.demand = sum(core.q.air_demand_nm3_min.values())
        self.leak_ref = min(p.f("air.leaks.max_nm3_min"), self.leak_ref + p.f("air.leaks.growth_nm3_min_per_h") * dt / 3600.0)
        self.leak = (self.leak_ref + self.extra_leak) * self.bar / p.f("air.leaks.ref_bar")
        supply = 0.0
        for c in self.compressors.values():
            lo, hi = self.band(c)
            serviced = core.t < c.service_until
            if c.tripped or serviced or not core.q.powered(c.zone):
                self.set_state(c, "stopped", "compressor tripped" if c.tripped else "taken out for service" if serviced else "no mains power in the compressor room")
            elif c.state == "stopped":
                if c.role == "duty":
                    self.set_state(c, "starting", "duty compressor enabled")
                elif self.bar < p.f("air.standby_start_bar"):
                    # The sequencer waits out short dips before it starts the lag compressor.
                    c.low_since = core.t if c.low_since is None else c.low_since
                    if core.t - c.low_since >= p.f("air.standby_start_delay_s"):
                        self.set_state(c, "starting", f"pressure below the standby start level {p.f('air.standby_start_bar')} bar for {p.f('air.standby_start_delay_s'):.0f} s")
                else:
                    c.low_since = None
            elif c.state == "starting":
                if core.t - c.unloaded_since >= p.f("air.star_delta_s"):
                    self.set_state(c, "loaded", "motor up to speed (star-delta start complete)")
            elif self.bar <= lo and c.state == "unloaded":
                self.set_state(c, "loaded", f"pressure {self.bar:.2f} bar at the lower limit {lo} bar")
            elif self.bar >= hi and c.state == "loaded":
                self.set_state(c, "unloaded", f"pressure {self.bar:.2f} bar at the upper limit {hi} bar")
            elif c.role == "standby" and c.state == "unloaded" and core.t - c.unloaded_since >= p.f("air.standby_idle_stop_s"):
                self.set_state(c, "stopped", f"standby ran unloaded for {p.f('air.standby_idle_stop_s'):.0f} s")
            fad = self.cp(c, "fad_nm3_min")
            loaded_kw = self.cp(c, "specific_power_kw_per_nm3_min") * fad
            c.delivery_nm3_min = fad if c.loaded else 0.0
            c.power_kw = loaded_kw if c.loaded else loaded_kw * p.f("air.unloaded_power_share") if c.state in ("unloaded", "starting") else 0.0
            if c.loaded:
                c.run_hours += dt / 3600.0
                c.service_hours += dt / 3600.0
            target = p.f("air.discharge_loaded_c") if c.loaded else p.f("air.discharge_unloaded_c") if c.state == "unloaded" else p.f("air.ambient_c")
            c.discharge_c += (target - c.discharge_c) * min(1.0, dt / p.f("air.discharge_tau_s"))
            supply += c.delivery_nm3_min
            core.q.power_kw[c.id] = c.power_kw
            core.q.power_zone[c.id] = c.zone
            core.q.power_kind[c.id] = "motor"
        self.supply = supply
        net = supply - self.demand - self.leak
        self.bar += net * p.f("air.p_atm_bar") / (60.0 * p.f("air.receiver_m3")) * dt
        self.bar = max(0.0, min(self.bar, p.f("air.safety_valve_bar")))
        if not self.trip and self.bar < p.f("air.trip_bar"):
            self.trip = True
            core.record("low air pressure trip", f"header pressure {self.bar:.2f} bar below the trip level {p.f('air.trip_bar')} bar")
        elif self.trip and self.bar > p.f("air.trip_reset_bar"):
            self.trip = False
            core.record("low air pressure trip cleared", f"header pressure {self.bar:.2f} bar back above {p.f('air.trip_reset_bar')} bar")
        core.q.flags["air_trip"] = self.trip
        core.q.air_pressure_bar = self.bar


# ====================================================================== electrical

class Electrical(Model):
    key = "power"
    title = "Electrical supply (grid, solar, generator with transfer switch)"
    equations = (
        "Zone load = Σ consumers wired in the zone + the zone's fixed load; building load = lighting + HVAC + offices.",
        "Lighting = installed kW × (1 − daylight dimming × sun) during the working day, night share outside it.",
        "HVAC = base + kW per °C × max(0, outdoor temperature − setpoint).",
        "Solar available = kWp × performance ratio × clear-sky shape(h) × cloud factor; 0 while the grid is down (inverters do not island).",
        "Zero-export limiter: solar = min(available, site load − minimum import), so the incomer never exports.",
        "Power factor = P / √(P² + Q²), with Q = P × tan(acos(PF)) for each load kind (motors, lighting/IT, chargers).",
        "APFC bank at the main board switches capacitor steps in to bring the incomer towards its target PF (solar supplies "
        "real power only, so at midday the incomer's PF falls unless the bank compensates).",
        "Grid import (incomer) = everything on the mains − solar, while the grid is up.",
        "Load shedding (on the twin's request): EV charging limited to its base, non-critical lighting dimmed by a share.",
        "Grid failure: the AMF controller confirms the loss, cranks, accelerates to rated speed, then transfers the "
        "critical bus to the generator; non-critical zones are shed until the grid returns.",
        "Grid return: after the retransfer delay the critical bus goes back to the mains; the engine cools down unloaded, then stops.",
        "Fuel = idle L/h + L/kWh × load (a straight-line fuel curve); coolant: dT/dt = (T_target(load) − T) / τ.",
    )
    reads = ("power_kw", "power_kind", "flags.outdoor_c", "flags.cloud")
    writes = ("zone_powered",)
    params_prefix = ("power",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.u = cfg.get("utilities") or {}
        self.zones = {z["id"] for s in cfg["sites"] for z in s["zones"]}
        self.critical: set[str] = set(self.u.get("critical_zones", []))
        self.grid_down = False
        self.grid_since = 0.0
        self.gen_state = "off"
        self.gen_since = 0.0
        self.transfer = "mains"   # mains | open | generator: the critical bus's source
        self.rpm = 0.0
        self.coolant_c = 0.0
        self.fuel_lph = 0.0
        self.gen_kw = 0.0
        self.solar_kw = 0.0
        self.solar_available_kw = 0.0
        self.building_kw = 0.0
        self.zone_kw: dict[str, float] = {}
        self.zone_kvar: dict[str, float] = {}
        self.import_kw = 0.0
        self.import_kvar = 0.0
        self.apfc_kvar = 0.0
        self.load_kw = 0.0   # everything consuming now (incl. critical loads on the generator or the UPS)
        self.ups_kw = 0.0    # critical load carried by batteries during the transfer gap
        self.forced: set[str] = set()  # meters and the genset bridge report at once (the grid just changed)
        self.shed = False  # the BMS has shed non-critical loads (EV charging, some lighting) on the twin's request

    def bind(self, core: Any) -> None:
        super().bind(core)
        self.coolant_c = core.p.f("power.generator.coolant_standby_c")

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        if target == self.u.get("incomer") and action == "shed":
            self.shed = bool(data.get("on", True))
            core = self.core
            core.q.flags["shed"] = self.shed
            core.record("non-critical loads shed" if self.shed else "shed loads restored", "shed command (peak demand control)")
            return True
        if target != self.u.get("incomer") or action not in ("grid_failure", "grid_restore"):
            return False
        self.grid_down, self.grid_since = action == "grid_failure", self.core.t
        self.forced |= {self.u.get("incomer"), self.u.get("generator"), self.u.get("genset"), self.u.get("solar_meter"), *(self.u.get("feeders") or {})}
        self.core.record("grid failure" if self.grid_down else "grid restored", f"{action} command at {target}")
        return True

    def _gen(self, state: str, cause: str) -> None:
        self.gen_state, self.gen_since = state, self.core.t
        self.forced.add(self.u.get("genset"))
        self.core.record(f"generator {state.replace('_', ' ')}", cause)

    def _transfer(self, to: str, cause: str) -> None:
        self.transfer = to
        self.forced |= {self.u.get("generator"), self.u.get("genset"), *(self.u.get("feeders") or {})}
        self.core.record(f"transfer switch to {to}", cause)

    def _sequence(self) -> None:
        """The AMF controller's sequence (timings from ISO 8528-12 / NFPA 110 type 10 in the params)."""
        p, t = self.core.p, self.core.t
        since = t - self.gen_since
        g = self.gen_state
        if self.grid_down:
            if self.transfer == "mains":
                self._transfer("open", "mains lost")
            if g == "off":
                self._gen("start_delay", "mains lost")
            elif g == "cooldown":
                self._gen("running", "mains lost again during cool-down")
                self._transfer("generator", "generator still at rated speed")
            elif g == "start_delay" and since >= p.f("power.generator.mains_fail_delay_s"):
                self._gen("cranking", "mains failure confirmed")
            elif g == "cranking" and since >= p.f("power.generator.crank_s"):
                self._gen("accelerating", "engine fired")
            elif g == "accelerating" and since >= p.f("power.generator.accelerate_s"):
                self._gen("running", "rated speed and voltage reached")
                self._transfer("generator", "generator ready")
        else:
            if g == "start_delay":
                self._gen("off", "mains back before the start was confirmed")
                self._transfer("mains", "mains back")
            elif g in ("cranking", "accelerating", "running") and t - self.grid_since >= p.f("power.generator.retransfer_delay_s"):
                self._transfer("mains", f"mains stable for {p.f('power.generator.retransfer_delay_s'):.0f} s")
                self._gen("cooldown", "load back on the mains")
            elif g == "cooldown" and since >= p.f("power.generator.cooldown_s"):
                self._gen("off", "cool-down complete")
            elif g == "off" and self.transfer != "mains":
                self._transfer("mains", "mains back")

    def _tan(self, kind: str) -> float:
        p = self.core.p
        pf = p.f(f"power.pf.{kind}") if f"power.pf.{kind}" in p.leaves else p.f("power.pf.fixed")
        return math.tan(math.acos(pf))

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        self._sequence()
        h = core.hour_of_day()
        sun = day_curve(h, p.f("power.solar.sunrise_h"), p.f("power.solar.sunset_h"))
        working = day_curve(h, p.f("power.building.day_start_h"), p.f("power.building.day_end_h")) > 0
        lights = p.f("power.building.lighting_kw") * ((1 - p.f("power.building.daylight_dimming") * sun) if working else p.f("power.building.lighting_night_share"))
        if self.shed:
            lights *= 1 - p.f("power.shed.lighting_share")
        outdoor = float(core.q.flags.get("outdoor_c", p.f("power.building.hvac_setpoint_c")))
        hvac = p.f("power.building.hvac_base_kw") + p.f("power.building.hvac_kw_per_c") * max(0.0, outdoor - p.f("power.building.hvac_setpoint_c"))
        offices = p.f("power.building.offices_kw") * (1.0 if working else p.f("power.building.offices_night_share"))
        self.building_kw = lights + hvac + offices
        crit_share = p.f("power.building.critical_share")
        zone_kw: dict[str, float] = {z: float(kw) for z, kw in (p.v("power.zone_fixed_kw") or {}).items()}
        zone_kvar: dict[str, float] = {z: kw * self._tan("fixed") for z, kw in zone_kw.items()}
        for name, kw in core.q.power_kw.items():
            z = core.q.power_zone.get(name)
            if z is None:
                continue
            zone_kw[z] = zone_kw.get(z, 0.0) + kw
            zone_kvar[z] = zone_kvar.get(z, 0.0) + kw * self._tan(core.q.power_kind.get(name, "fixed"))
        for z in self.zones:
            # critical zones ride through the transfer gap on their UPS / battery back-up
            core.q.zone_powered[z] = (not self.grid_down) or z in self.critical
        building = self.building_kw * (crit_share if self.grid_down else 1.0)
        if self.grid_down:
            zone_kw = {z: (kw if z in self.critical else 0.0) for z, kw in zone_kw.items()}
            zone_kvar = {z: (kv if z in self.critical else 0.0) for z, kv in zone_kvar.items()}
        self.zone_kw, self.zone_kvar = zone_kw, zone_kvar
        critical_kw = sum(kw for z, kw in zone_kw.items() if z in self.critical) + self.building_kw * crit_share
        critical_kvar = sum(kv for z, kv in zone_kvar.items() if z in self.critical) + self.building_kw * crit_share * self._tan("building")
        total_kw = sum(zone_kw.values()) + building
        total_kvar = sum(zone_kvar.values()) + building * self._tan("building")
        self.load_kw = total_kw
        cloud = float(core.q.flags.get("cloud", 1.0))
        crit_on_gen = self.transfer == "generator" and self.gen_state == "running"
        on_gen_kw = critical_kw if crit_on_gen else 0.0
        on_gen_kvar = critical_kvar if crit_on_gen else 0.0
        self.solar_available_kw = 0.0 if self.grid_down else p.f("power.solar.kwp") * p.f("power.solar.performance_ratio") * sun * cloud
        # Zero-export limiter: the inverters are curtailed so the incomer never exports (no net metering).
        self.solar_kw = min(self.solar_available_kw, max(0.0, total_kw - on_gen_kw - p.f("power.solar.min_import_kw")))
        if self.grid_down:
            self.import_kw, self.import_kvar, self.apfc_kvar = 0.0, 0.0, 0.0
        else:
            self.import_kw = total_kw - on_gen_kw - self.solar_kw
            q = total_kvar - on_gen_kvar
            # APFC capacitor bank at the main board: switches in whole steps to bring the incomer towards its target PF.
            want = max(0.0, q - self.import_kw * math.tan(math.acos(p.f("power.apfc.target_pf"))))
            step = p.f("power.apfc.step_kvar")
            self.apfc_kvar = min(p.f("power.apfc.capacity_kvar"), math.floor(want / step) * step)
            self.import_kvar = q - self.apfc_kvar
        self.ups_kw = critical_kw if (self.transfer == "open") else 0.0
        self.gen_kw = on_gen_kw
        g = self.gen_state
        rated_rpm = p.f("power.generator.rated_rpm")
        target_rpm = {"off": 0.0, "start_delay": 0.0, "cranking": p.f("power.generator.crank_rpm")}.get(g, rated_rpm)
        self.rpm += (target_rpm - self.rpm) * min(1.0, dt / p.f("power.generator.rpm_tau_s"))
        running = g in ("accelerating", "running", "cooldown")
        self.fuel_lph = (p.f("power.generator.idle_lph") + p.f("power.generator.lph_per_kw") * self.gen_kw) if running else 0.0
        load_frac = self.gen_kw / p.f("power.generator.rated_kw")
        target_c = (p.f("power.generator.coolant_idle_c") + p.f("power.generator.coolant_rise_full_load_c") * load_frac) if running \
            else p.f("power.generator.coolant_standby_c")
        self.coolant_c += (target_c - self.coolant_c) * min(1.0, dt / p.f("power.generator.coolant_tau_s"))
        water = core.by_key.get("water")
        diesel = self.u.get("diesel_tank")
        if water is not None and diesel in water.tanks and self.fuel_lph > 0:
            water.draw(diesel, self.fuel_lph * dt / 3600.0)

    # ------------------------------------------------------------------ what each meter sees

    def feeder_kw(self, meter: str) -> float:
        zone = (self.u.get("feeders") or {}).get(meter)
        return self.zone_kw.get(zone, 0.0) if zone else 0.0

    def meter_kw(self, meter: str) -> float:
        if meter == self.u.get("incomer"):
            return self.import_kw
        if meter == self.u.get("generator"):
            return self.gen_kw
        if meter == self.u.get("solar_meter"):
            return self.solar_kw
        return self.feeder_kw(meter)

    def meter_pf(self, meter: str) -> float | None:
        if meter == self.u.get("incomer"):
            kw, kvar = self.import_kw, self.import_kvar
        elif meter == self.u.get("solar_meter"):
            kw, kvar = self.solar_kw, 0.0
        elif meter == self.u.get("generator"):
            kw = self.gen_kw
            kvar = kw * self._tan("motor")
        else:
            zone = (self.u.get("feeders") or {}).get(meter) or ""
            kw, kvar = self.zone_kw.get(zone, 0.0), self.zone_kvar.get(zone, 0.0)
        if kw <= 0:
            return None  # a meter shows no power factor without load
        return kw / math.hypot(kw, kvar)

    def meter_volts(self, meter: str) -> float:
        nominal = self.core.p.f("power.nominal_v")
        if meter in (self.u.get("incomer"), self.u.get("solar_meter")):
            return 0.0 if self.grid_down else nominal
        if meter == self.u.get("generator"):
            return nominal if self.gen_state in ("running", "cooldown") else 0.0
        zone = (self.u.get("feeders") or {}).get(meter)
        if zone in self.critical:
            on = (self.transfer == "mains" and not self.grid_down) or (self.transfer == "generator" and self.gen_state == "running")
            return nominal if on else 0.0
        return 0.0 if self.grid_down else nominal


# ====================================================================== water and effluent

@dataclass
class Tank:
    id: str
    kind: str          # day | storage | etp | fire | diesel
    zone: str
    level_pct: float
    pumping: bool = False


class Water(Model):
    key = "water"
    title = "Water and effluent (tanks, pumps, ETP)"
    equations = (
        "Tank level: dL/dt = (inflow − outflow) / volume × 100 %; flows in m³/h.",
        "Day tank demand = canteen (meal times) + cooling-tower make-up + process water per unit made.",
        "Cooling make-up = evaporation + blowdown ≈ L per kWh of heat rejected × (factory motor power).",
        "Pumps run with hysteresis, starting at the low level and stopping at the high level: the transfer pump fills "
        "the day tank from storage, the supply pump fills storage.",
        "Effluent = return share × (canteen + process) into the ETP equalisation tank; the ETP treats at its capacity "
        "while the tank is above its minimum. A tank at its overflow level means the plant is overloaded.",
        "Fire water is drawn only by the fire pump and refilled by its own pump. The diesel day tank falls by the generator's fuel use.",
    )
    reads = ("power_kw", "flags.fire_alarm")
    writes = ("power_kw", "flags.etp_overload")
    params_prefix = ("water",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        roles = (cfg.get("utilities") or {}).get("tanks", {})
        self.tanks = {d["id"]: Tank(d["id"], roles.get(d["id"], "storage"), d["zone_id"], 0.0)
                      for d in cfg["devices"] if d["type"] == "tank_level"}
        self.by_kind = {tk.kind: tk for tk in self.tanks.values()}
        self.flows: dict[str, float] = {}
        self.etp_load = 0.0
        self._units_seen: int | None = None

    def bind(self, core: Any) -> None:
        super().bind(core)
        for tk in self.tanks.values():
            tk.level_pct = core.p.f(f"water.tanks.{tk.kind}.initial_pct")

    def vol(self, tk: Tank) -> float:
        return self.core.p.f(f"water.tanks.{tk.kind}.volume_m3")

    def draw(self, tank_id: str, litres: float) -> None:
        tk = self.tanks[tank_id]
        tk.level_pct = max(0.0, tk.level_pct - 100.0 * litres / 1000.0 / self.vol(tk))

    def _change(self, tk: Tank, m3h: float, dt: float) -> None:
        tk.level_pct = max(0.0, min(100.0, tk.level_pct + 100.0 * m3h * dt / 3600.0 / self.vol(tk)))

    def _pump(self, tk: Tank, name: str) -> None:
        p = self.core.p
        on, off = p.f(f"water.tanks.{tk.kind}.pump_on_pct"), p.f(f"water.tanks.{tk.kind}.pump_off_pct")
        if not tk.pumping and tk.level_pct <= on:
            tk.pumping = True
            self.core.record(f"{name} on", f"{tk.id} at {tk.level_pct:.0f} %, its start level {on:.0f} %")
        elif tk.pumping and tk.level_pct >= off:
            tk.pumping = False
            self.core.record(f"{name} off", f"{tk.id} at {tk.level_pct:.0f} %, its stop level {off:.0f} %")

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        h = core.hour_of_day()
        canteen = p.f("water.canteen.meal_m3h") if any(a <= h < b for a, b in p.v("water.canteen.meals_h")) else p.f("water.canteen.base_m3h")
        heat_kw = sum(kw for name, kw in core.q.power_kw.items()
                      if core.q.power_kind.get(name) == "motor" and core.q.power_zone.get(name) in p.v("water.cooling.zones"))
        cooling = p.f("water.cooling.l_per_kwh_heat") * heat_kw / 1000.0  # L/kWh × kW = L/h → m³/h
        prod = core.by_key.get("production")
        made = sum(m.units + m.rejects for m in prod.machines.values()) if prod else 0
        new_units = made - (self._units_seen if self._units_seen is not None else made)
        self._units_seen = made
        process = p.f("water.process.l_per_unit") * new_units / 1000.0 * 3600.0 / dt  # m³ this step → m³/h
        demand = canteen + cooling + process
        self.flows = {"canteen_m3h": canteen, "cooling_m3h": cooling, "process_m3h": process, "demand_m3h": demand}
        pump_kw = 0.0
        day, storage, etp, fire = (self.by_kind.get(k) for k in ("day", "storage", "etp", "fire"))
        if day is not None:
            self._pump(day, "transfer pump")
            transfer = p.f("water.pumps.transfer_m3h") if day.pumping and (storage is None or storage.level_pct > p.f("water.tanks.storage.min_pct")) else 0.0
            self._change(day, transfer - demand, dt)
            if storage is not None:
                self._change(storage, -transfer, dt)
            pump_kw += p.f("water.pumps.transfer_kw") if transfer else 0.0
        if storage is not None:
            self._pump(storage, "supply pump")
            if storage.pumping:
                self._change(storage, p.f("water.pumps.supply_m3h"), dt)
                pump_kw += p.f("water.pumps.supply_kw")
        overload = False
        if etp is not None:
            inflow = p.f("water.etp.return_share") * (canteen + process)
            etp.pumping = etp.level_pct > p.f("water.tanks.etp.min_pct")
            treat = p.f("water.etp.capacity_m3h") if etp.pumping else 0.0
            self._change(etp, inflow - treat, dt)
            self.etp_load = inflow / p.f("water.etp.capacity_m3h")
            overload = etp.level_pct >= p.f("water.tanks.etp.overflow_pct")
            pump_kw += p.f("water.etp.plant_kw") if etp.pumping else 0.0
        core.q.flags["etp_overload"] = overload
        if fire is not None:
            if core.q.flags.get("fire_alarm"):
                self._change(fire, -p.f("water.pumps.fire_pump_m3h"), dt)
            self._pump(fire, "fire tank refill pump")
            if fire.pumping:
                self._change(fire, p.f("water.pumps.fire_refill_m3h"), dt)
        diesel = self.by_kind.get("diesel")
        if diesel is not None:
            diesel.pumping = False  # refilled by tanker, not by a pump here
        core.q.power_kw["Water pumps"] = pump_kw
        core.q.power_zone["Water pumps"] = day.zone if day else str(p.v("water.pumps.zone"))
        core.q.power_kind["Water pumps"] = "motor"


# ====================================================================== other loads

class CampusLoads(Model):
    """Loads that are not machines: EV chargers by time of day, the fire pump during a fire alarm."""
    key = "loads"
    title = "Other campus loads (EV chargers, welding, fire pump)"
    equations = (
        "EV chargers = base + peak × sin(π (h − start) / (end − start)) while people are at work; base only while shed.",
        "Welding (hot work) in the workshop = rated kW × duty during production; interlocked off by any gas or fire alarm.",
        "Fire pump = rated kW while any fire panel reports an alarm, standby kW otherwise.",
    )
    reads = ("flags.fire_alarm",)
    writes = ("power_kw",)
    params_prefix = ("loads",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        zones = {z["id"]: z for s in cfg["sites"] for z in s["zones"]}
        self.ev_zone = next((z for z in zones if z.endswith("PARKING")), None)
        self.pump_zone = next((z for z in zones if z.endswith("FIREPUMP")), None)
        self.workshop = next((z for z in zones if z.endswith("WORKSHOP")), None)
        self.hot_work_stopped = False

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        h = core.hour_of_day()
        if self.ev_zone:
            day = 0.0 if core.q.flags.get("shed") else day_curve(h, p.f("loads.ev.start_h"), p.f("loads.ev.end_h"))
            core.q.power_kw["EV chargers"] = p.f("loads.ev.base_kw") + p.f("loads.ev.peak_kw") * day
            core.q.power_zone["EV chargers"] = self.ev_zone
            core.q.power_kind["EV chargers"] = "electronic"
        if self.workshop:
            # Hot work (welding) in the workshop during production; the gas and fire interlocks stop it campus-wide.
            stop = bool(core.q.flags.get("gas_alarm_zones")) or bool(core.q.flags.get("fire_alarm"))
            if stop != self.hot_work_stopped:
                self.hot_work_stopped = stop
                core.record("hot work stopped" if stop else "hot work permitted again",
                            "interlock: gas or fire alarm" if stop else "gas and fire alarms clear")
            welding = core.q.flags.get("shift_phase") == "production" and not stop
            core.q.power_kw["Welding (hot work)"] = p.f("loads.welding.kw") * p.f("loads.welding.duty") if welding else 0.0
            core.q.power_zone["Welding (hot work)"] = self.workshop
            core.q.power_kind["Welding (hot work)"] = "fixed"
        if self.pump_zone:
            fire = bool(core.q.flags.get("fire_alarm"))
            core.q.power_kw["Fire pump"] = p.f("loads.fire_pump.rated_kw") if fire else p.f("loads.fire_pump.standby_kw")
            core.q.power_zone["Fire pump"] = self.pump_zone
            core.q.power_kind["Fire pump"] = "motor"
