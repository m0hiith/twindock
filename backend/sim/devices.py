"""Simulated devices: what each commissioned SIM device in sites.json publishes, read from the true state through its
sensors (sim.sensors). Same topics, channels and payload schemas as before the core existed; every payload carries
source "sim". A device that has lost mains power (its zone is off in a grid failure) or was silenced publishes nothing.
"""

from __future__ import annotations

import math
from typing import Any

from .core import SimCore
from .sensors import Sensor, SensorSpec

FW = {"gateway": "sim-1.0", "machine_monitor": "sim-2.3", "env_sensor": "sim-1.4", "door_sensor": "sim-1.1",
      "occupancy_sensor": "sim-1.2", "badge": "sim-3.0", "asset_tag": "sim-1.0", "power_meter": "sim-1.0",
      "light": "sim-1.0", "air_quality": "sim-1.3", "truck_telematics": "sim-1.0", "dock_bay": "sim-1.0",
      "conveyor_monitor": "sim-1.0", "compressor_monitor": "sim-1.0", "helmet_clip": "sim-1.0", "gas_detector": "sim-1.0",
      "leak_sensor": "sim-1.0", "tank_level": "sim-1.0", "fire_panel": "sim-1.0", "water_quality": "sim-1.0",
      "genset_controller": "sim-1.0"}

# Mains-powered devices report no battery and go quiet when their zone loses power.
MAINS = {"machine_monitor", "air_quality", "power_meter", "light", "gateway", "dock_bay", "conveyor_monitor", "compressor_monitor",
         "gas_detector", "fire_panel", "tank_level", "truck_telematics", "water_quality"}
# Powered from the generator's own 24 V control battery: keeps reporting through a grid failure.
BATTERY_BACKED = {"genset_controller"}

Payload = dict[str, Any]
Out = list[tuple[str, Payload]]


def sim(p: Payload) -> Payload:
    p["source"] = "sim"
    return p


class Device:
    """One simulated device. Subclasses implement `readings(t)`; this class adds status, battery and power loss."""

    def __init__(self, d: dict[str, Any], core: SimCore) -> None:
        self.d = d
        self.core = core
        self.id = str(d["id"])
        self.type = str(d["type"])
        p = core.p
        self.silent = False
        self.battery: float | None = None
        if self.type not in MAINS and self.type not in BATTERY_BACKED:
            self.battery = float(d.get("sim", {}).get("battery_pct", core.rng.draw("devices.initial_battery_pct", f"{self.id}.battery")))
        self.rssi = float(d.get("sim", {}).get("rssi_dbm", core.rng.draw("devices.rssi_dbm", f"{self.id}.rssi")))
        self.status_sensor = Sensor(SensorSpec("status", None, p.f("devices.status_period_s"), 0, 0, None, None, 0, "", ""),
                                    core.rng, f"{self.id}.status")
        self.sensors: dict[str, Sensor] = {}
        self._last: dict[str, Any] = {}
        self.dt = 0.0

    # ------------------------------------------------------------------ helpers for subclasses

    def sensor(self, channel: str) -> Sensor:
        s = self.sensors.get(channel)
        if s is None:
            s = self.sensors[channel] = Sensor(SensorSpec.from_params(self.core.p, self.type, channel), self.core.rng, f"{self.id}.{channel}")
        return s

    def reading(self, ts_ms: int, channel: str, value: Any) -> tuple[str, Payload]:
        p: Payload = {"ts_ms": ts_ms, "value": value}
        unit = self.sensors[channel].spec.unit if channel in self.sensors else None
        if unit:
            p["unit"] = unit
        return channel, sim(p)

    def sample(self, out: Out, ts_ms: int, channel: str, true: float, t: float) -> None:
        """A numeric channel on its sample clock: true value -> sensor -> reading (unless the sample is lost)."""
        s = self.sensor(channel)
        if s.due(t):
            v = s.read(true)
            if v is not None:
                out.append(self.reading(ts_ms, channel, v))

    def state(self, out: Out, ts_ms: int, channel: str, value: Any, t: float) -> None:
        """A state channel (flag, name, counter): reported at once when it changes and on its heartbeat period."""
        s = self.sensor(channel)
        changed = self._last.get(channel, object()) != value
        if changed or s.due(t):
            if changed:
                s.force(t)
                s.due(t)
            self._last[channel] = value
            out.append(self.reading(ts_ms, channel, value))

    # ------------------------------------------------------------------ device interface

    @property
    def dormant(self) -> bool:
        """Switched off entirely (a badge in the gate rack off shift): no readings, no status."""
        return False

    @property
    def power_off(self) -> bool:
        return self.type in MAINS and not self.core.q.powered(self.d["zone_id"])

    def hello(self) -> Payload:
        return sim({"type": self.type, "protocol": self.d["protocol"], "capabilities": list(self.d["capabilities"]), "fw_version": FW[self.type]})

    def status(self, ts_ms: int) -> Payload:
        p: Payload = {"ts_ms": ts_ms, "rssi_dbm": int(round(self.rssi + self.core.rng.gauss(f"{self.id}.rssi", self.core.p.f("devices.rssi_sigma_db")))),
                      "fault": None}
        if self.battery is not None:
            p["battery_pct"] = round(self.battery, 1)
        return sim(p)

    def step(self, t: float, dt: float, ts_ms: int) -> tuple[Out, bool]:
        """(readings, status due). Battery drains whether or not the device can publish."""
        if self.battery is not None:
            self.battery = max(0.0, self.battery - dt * self.core.p.f("devices.battery_drain_pct_per_s"))
        self.dt = dt
        out = self.readings(t, ts_ms)
        return out, self.status_sensor.due(t)

    def readings(self, t: float, ts_ms: int) -> Out:
        return []

    def command(self, action: str, data: dict[str, Any]) -> bool:
        """Device-level commands (silence). Everything else goes to the models through the core."""
        if action == "silence":
            self.silent = bool(data.get("on", True))
            return True
        return False


class EnvSensor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        r = self.core.get("rooms").rooms[self.d["zone_id"]]
        out: Out = []
        self.sample(out, ts_ms, "temperature", r.temp_c, t)
        self.sample(out, ts_ms, "humidity", r.rh_pct, t)
        if "co2_ppm" in self.d["capabilities"]:
            self.sample(out, ts_ms, "co2_ppm", r.co2_ppm, t)
            self.sample(out, ts_ms, "pm25_ugm3", r.pm25, t)
        return out


class AirQuality(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        r = self.core.get("rooms").rooms[self.d["zone_id"]]
        out: Out = []
        self.sample(out, ts_ms, "co2_ppm", r.co2_ppm, t)
        self.sample(out, ts_ms, "pm25_ugm3", r.pm25, t)
        return out


class DoorSensor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        out: Out = []
        doors = self.core.get("doors")
        if self.id in doors.changed:
            doors.changed.discard(self.id)
            self._last.pop("open", None)
        self.state(out, ts_ms, "open", bool(doors.doors[self.id]["open"]), t)
        return out


class OccupancySensor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        out: Out = []
        occ = self.core.get("occupancy")
        if self.id in occ.changed:
            occ.changed.discard(self.id)
            self._last.pop("occupied", None)
        self.state(out, ts_ms, "occupied", bool(occ.rooms[self.id]["occupied"]), t)
        return out


class MachineMonitor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        prod = self.core.get("production")
        m = prod.machines[self.id]
        out: Out = []
        for ch, v in m.events:
            if ch == "cycle_time_s":
                self.sensor(ch)
            out.append(self.reading(ts_ms, ch, v))
            if ch in ("state", "units", "rejects"):
                self._last[ch] = v
        m.events.clear()
        self.sample(out, ts_ms, "vibration_rms", prod.vibration(m), t)
        self.sample(out, ts_ms, "current_a", prod.current_a(m), t)
        if "temperature_c" in self.d["capabilities"]:
            self.sample(out, ts_ms, "temperature_c", m.surface_c, t)
        self.state(out, ts_ms, "state", m.state, t)
        self.state(out, ts_ms, "units", m.units, t)
        self.state(out, ts_ms, "rejects", m.rejects, t)
        return out


class Badge(Device):
    """A worker's BLE badge. Its position is the worker's true position plus a BLE positioning error that wanders
    slowly (an Ornstein-Uhlenbeck process: σ from the spec, correlation time τ), the way RSSI/AoA positioning drifts
    as people and vehicles move around, so the zone it reports is sometimes the neighbouring one near a boundary."""

    def __init__(self, d: dict[str, Any], core: SimCore) -> None:
        super().__init__(d, core)
        self.ex = self.ez = 0.0

    @property
    def dormant(self) -> bool:
        w = self.core.get("people").walkers.get(self.id)
        return w is not None and not w.on_site

    def readings(self, t: float, ts_ms: int) -> Out:
        w = self.core.get("people").walkers[self.id]
        if not w.on_site:
            w.events.clear()
            return []  # in the gate rack, switched off
        out: Out = [self.reading(ts_ms, ev, True) for ev in w.events]
        w.events.clear()
        s = self.sensor("position")
        spec = self.core.p.leaf("sensors.badge.position").value
        sigma, tau = float(spec.get("ble_sigma", 0.0)), float(spec.get("tau_s", 1.0))  # the slow BLE error; the spec's sigma is the white jitter
        if sigma > 0 and self.dt > 0:
            k = math.sqrt(2 * self.dt / tau) * sigma
            self.ex += -self.ex * self.dt / tau + self.core.rng.gauss(f"{self.id}.ble_x", k)
            self.ez += -self.ez * self.dt / tau + self.core.rng.gauss(f"{self.id}.ble_z", k)
        if s.due(t):
            x, z = s.read(w.x + self.ex), s.read(w.z + self.ez)
            if x is not None and z is not None:
                out.append(self.reading(ts_ms, "position", [x, z]))
        return out


class TruckTelematics(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        tel = self.core.get("telematics")
        tr = tel.trucks[self.id]
        out: Out = [self.reading(ts_ms, "harsh_event", e) for e in tr["events"]]
        tr["events"].clear()
        if self.sensor("door_open").due(t):
            out.append(self.reading(ts_ms, "door_open", tel.door_check(self.id)))
        self.sample(out, ts_ms, "speed_kmh", max(0.0, tr["speed"]), t)
        self.sample(out, ts_ms, "cargo_temp_c", tr["cargo_c"], t)
        return out


class DockBay(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        docks = self.core.get("docks")
        occ = bool(docks.bays[self.id]["occupied"])
        out: Out = []
        if self.id in docks.changed:
            docks.changed.discard(self.id)
            for ch in ("occupied", "door_position", "leveler", "dock_light"):
                self._last.pop(ch, None)
        self.state(out, ts_ms, "occupied", occ, t)
        self.state(out, ts_ms, "door_position", "open" if occ else "closed", t)
        self.state(out, ts_ms, "leveler", "deployed" if occ else "stowed", t)
        self.state(out, ts_ms, "dock_light", occ, t)
        return out


class ConveyorMonitor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        prod = self.core.get("production")
        out: Out = []
        if self.sensor("jam").due(t):
            self.sensors["jam"].force(t)  # jam, current and speed are one report
            self.sensors["jam"].due(t)
            out.append(self.reading(ts_ms, "jam", prod.conveyor_jammed(self.id)))
            for ch, v in (("motor_current_a", prod.conveyor_current_a(self.id)), ("belt_speed_m_s", prod.conveyor_speed(self.id))):
                s = self.sensor(ch)
                r = s.read(v)
                if r is not None:
                    out.append(self.reading(ts_ms, ch, r))
        return out


class CompressorMonitor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        air = self.core.get("air")
        c = air.compressors[self.id]
        p = self.core.p
        out: Out = []
        if self.id in air.forced:
            air.forced.discard(self.id)
            self.sensor("pressure_bar").force(t)
        if self.sensor("pressure_bar").due(t):
            amps = c.power_kw * 1000.0 / (3 ** 0.5 * p.f("power.nominal_v") * p.f("air.power_factor"))
            caps = set(self.d["capabilities"])
            for ch, v in (("pressure_bar", air.bar), ("current_a", amps), ("run_hours", c.run_hours),
                          ("dew_point_c", p.f("air.dryer.pressure_dew_point_c")), ("power_kw", c.power_kw),
                          ("flow_nm3_min", c.delivery_nm3_min), ("discharge_c", c.discharge_c)):
                if ch in caps:
                    r = self.sensor(ch).read(v)
                    if r is not None:
                        out.append(self.reading(ts_ms, ch, r))
            out.append(self.reading(ts_ms, "tripped", c.tripped))
            if "loaded" in caps:
                out.append(self.reading(ts_ms, "loaded", c.loaded))
        return out


class GensetController(Device):
    """The generator's AMF controller, read over Modbus: engine state and speed, coolant, fuel rate, load, transfer."""

    def readings(self, t: float, ts_ms: int) -> Out:
        pw = self.core.get("power")
        out: Out = []
        s = self.sensor("engine_state")
        if self.id in pw.forced:
            pw.forced.discard(self.id)
            s.force(t)
        if s.due(t):
            out += [self.reading(ts_ms, "engine_state", pw.gen_state), self.reading(ts_ms, "transfer", pw.transfer),
                    self.reading(ts_ms, "mains_ok", not pw.grid_down)]
            for ch, v in (("rpm", pw.rpm), ("coolant_c", pw.coolant_c), ("fuel_lph", pw.fuel_lph), ("load_kw", pw.gen_kw)):
                r = self.sensor(ch).read(v)
                if r is not None:
                    out.append(self.reading(ts_ms, ch, r))
        return out


class HelmetClip(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        c = self.core.get("helmets").clips[self.id]
        out: Out = []
        self.state(out, ts_ms, "worn", bool(c["worn"]), t)
        if c["impact"] is not None:
            r = self.sensor("impact_g").read(float(c["impact"]))
            c["impact"] = None
            if r is not None:
                out.append(self.reading(ts_ms, "impact_g", r))
        return out


class GasDetector(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        gas = self.core.get("gas")
        g = gas.points[self.id]
        out: Out = []
        if self.sensor("co_ppm").due(t):
            for ch, v in (("co_ppm", g["co"]), ("o2_pct", g["o2"])):
                r = self.sensor(ch).read(float(v))
                if r is not None:
                    out.append(self.reading(ts_ms, ch, r))
            out.append(self.reading(ts_ms, "alarm", gas.alarm(self.id)))
        return out


class LeakSensor(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        leaks = self.core.get("leaks")
        out: Out = []
        if self.id in leaks.changed:
            leaks.changed.discard(self.id)
            self._last.pop("wet", None)
        self.state(out, ts_ms, "wet", bool(leaks.wet[self.id]), t)
        return out


class TankLevel(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        tk = self.core.get("water").tanks[self.id]
        out: Out = []
        if self.sensor("level_pct").due(t):
            r = self.sensors["level_pct"].read(tk.level_pct)
            if r is not None:
                out.append(self.reading(ts_ms, "level_pct", r))
            out.append(self.reading(ts_ms, "pump_on", tk.pumping))
        return out


class FirePanel(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        fire = self.core.get("fire")
        fp = fire.panels[self.id]
        out: Out = []
        if self.id in fire.changed:
            fire.changed.discard(self.id)
            self.sensor("alarm").force(t)
        if self.sensor("alarm").due(t):
            out += [self.reading(ts_ms, "alarm", bool(fp["alarm"])), self.reading(ts_ms, "trouble", bool(fp["trouble"]))]
        return out


class PowerMeter(Device):
    def __init__(self, d: dict[str, Any], core: SimCore) -> None:
        super().__init__(d, core)
        self.kwh = core.p.f(f"devices.power_meter.initial_kwh.{self.id}") if f"devices.power_meter.initial_kwh.{self.id}" in core.p.leaves \
            else core.p.f("devices.power_meter.initial_kwh_default")

    def readings(self, t: float, ts_ms: int) -> Out:
        power = self.core.get("power")
        kw = power.meter_kw(self.id)
        self.kwh += kw * self.dt / 3600.0  # the meter integrates continuously (its register is exact)
        out: Out = []
        if self.id in power.forced:
            power.forced.discard(self.id)
            self.sensor("power_kw").force(t)
        if self.sensor("power_kw").due(t):
            for ch, v in (("power_kw", kw), ("energy_kwh", self.kwh), ("voltage_v", power.meter_volts(self.id))):
                r = self.sensor(ch).read(v)
                if r is not None:
                    out.append(self.reading(ts_ms, ch, r))
            pf = power.meter_pf(self.id)
            if pf is not None and "power_factor" in self.d["capabilities"]:  # the meter shows no PF without load
                r = self.sensor("power_factor").read(pf)
                if r is not None:
                    out.append(self.reading(ts_ms, "power_factor", r))
        return out


class WaterQuality(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        w = self.core.get("effluent").probes[self.id]
        out: Out = []
        if self.sensor("ph").due(t):
            for ch, v in (("ph", w["ph"]), ("turbidity_ntu", w["ntu"])):
                r = self.sensor(ch).read(float(v))
                if r is not None:
                    out.append(self.reading(ts_ms, ch, r))
        return out


class AssetTag(Device):
    def readings(self, t: float, ts_ms: int) -> Out:
        tags = self.core.get("tags")
        finding = tags.finding(self.id)
        out: Out = []
        s = self.sensor("find_me")
        if self.id in tags.changed:
            tags.changed.discard(self.id)
            s.force(t)
        # While finding, the tag reports every second; otherwise on its heartbeat.
        if s.due(t) or (finding and t + 1e-9 >= self._last.get("_find_next", 0.0)):
            self._last["_find_next"] = t + self.core.p.f("tags.finding_report_s")
            out.append(self.reading(ts_ms, "find_me", finding))
        return out


DEVICES: dict[str, type[Device]] = {
    "env_sensor": EnvSensor, "air_quality": AirQuality, "door_sensor": DoorSensor, "occupancy_sensor": OccupancySensor,
    "machine_monitor": MachineMonitor, "badge": Badge, "truck_telematics": TruckTelematics, "dock_bay": DockBay,
    "conveyor_monitor": ConveyorMonitor, "compressor_monitor": CompressorMonitor, "helmet_clip": HelmetClip,
    "gas_detector": GasDetector, "leak_sensor": LeakSensor, "tank_level": TankLevel, "fire_panel": FirePanel,
    "power_meter": PowerMeter, "water_quality": WaterQuality, "asset_tag": AssetTag, "genset_controller": GensetController,
}


def make_device(d: dict[str, Any], core: SimCore) -> Device:
    return DEVICES.get(d["type"], Device)(d, core)
