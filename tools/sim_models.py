"""Device models for tools/site_sim.py. Pure Python, no MQTT, so tests can drive them.

Each model turns time into payloads for its channels. Values follow simple physical stories
(a cold room warms while its door is open, a press vibrates around its own baseline) so the
twin has something believable to show. Everything here is simulation: every payload carries
source "sim" and fw_version "sim-x.y".
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

FW = {"gateway": "sim-1.0", "machine_monitor": "sim-2.3", "env_sensor": "sim-1.4", "door_sensor": "sim-1.1",
      "occupancy_sensor": "sim-1.2", "badge": "sim-3.0", "asset_tag": "sim-1.0", "power_meter": "sim-1.0",
      "light": "sim-1.0", "air_quality": "sim-1.3", "truck_telematics": "sim-1.0", "dock_bay": "sim-1.0",
      "conveyor_monitor": "sim-1.0", "compressor_monitor": "sim-1.0", "helmet_clip": "sim-1.0", "gas_detector": "sim-1.0",
      "leak_sensor": "sim-1.0", "tank_level": "sim-1.0", "fire_panel": "sim-1.0"}

# Mains-powered devices report no battery; the rest start somewhere plausible.
MAINS = {"machine_monitor", "air_quality", "power_meter", "light", "gateway", "dock_bay", "conveyor_monitor", "compressor_monitor",
         "gas_detector", "fire_panel", "tank_level", "truck_telematics"}

Payload = dict[str, Any]
Out = list[tuple[str, Payload]]  # (channel, payload)


def sim(p: Payload) -> Payload:
    p["source"] = "sim"
    return p


@dataclass
class Model:
    d: dict[str, Any]  # the device's entry in backend/world/sites.json
    rng: random.Random
    battery: float | None = None
    rssi: float = -60.0
    fault: str | None = None
    silent: bool = False  # stop publishing (lets the twin show the device going stale)
    _due: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.d["type"] not in MAINS:
            self.battery = self.d.get("sim", {}).get("battery_pct", self.rng.uniform(55, 98))
        self.rssi = self.d.get("sim", {}).get("rssi_dbm", self.rng.uniform(-78, -52))

    @property
    def id(self) -> str:
        return str(self.d["id"])

    def hello(self) -> Payload:
        return sim({"type": self.d["type"], "protocol": self.d["protocol"],
                    "capabilities": list(self.d["capabilities"]), "fw_version": FW[self.d["type"]]})

    def status(self, ts_ms: int) -> Payload:
        p: Payload = {"ts_ms": ts_ms, "rssi_dbm": int(round(self.rssi + self.rng.gauss(0, 1.5))), "fault": self.fault}
        if self.battery is not None:
            p["battery_pct"] = round(self.battery, 1)
        return sim(p)

    def every(self, key: str, t: float, period: float) -> bool:
        """True once per period (first call fires), with a little jitter so devices don't sync up."""
        due = self._due.get(key)
        if due is None or t >= due:
            self._due[key] = t + period * self.rng.uniform(0.9, 1.1)
            return True
        return False

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        if self.battery is not None:
            self.battery = max(0.0, self.battery - dt * 0.0005)  # slow drain, visible over a long demo
        return []

    def reading(self, ts_ms: int, value: Any, unit: str | None = None) -> Payload:
        p: Payload = {"ts_ms": ts_ms, "value": value}
        if unit:
            p["unit"] = unit
        return sim(p)


@dataclass
class EnvSensor(Model):
    temp: float = 0.0
    hum: float = 0.0
    door_open: bool = False  # set by the simulator from the room's door sensor
    co2: float = 650.0
    pm: float = 8.0

    def __post_init__(self) -> None:
        super().__post_init__()
        cold = "COLD" in self.d["zone_id"]
        self.setpoint = 3.0 if cold else 19.0
        self.temp = self.setpoint + self.rng.uniform(-0.3, 0.3)
        self.hum = 82.0 if cold else 45.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        # First-order room model: an open door pulls the room towards ambient (~18 °C), the
        # cooling pulls it back to the setpoint. Time constants: minutes, as in a real cold room.
        ambient = 18.0
        if self.door_open:
            self.temp += (ambient - self.temp) * dt / 240.0
        else:
            self.temp += (self.setpoint - self.temp) * dt / 180.0
        self.temp += self.rng.gauss(0, 0.01) * math.sqrt(dt)
        self.hum += (self.rng.gauss(0, 0.2) - (self.hum - (82 if self.setpoint < 10 else 45)) * 0.01) * dt
        if self.every("env", t, 5.0):
            out: Out = [("temperature", self.reading(ts_ms, round(self.temp, 2), "°C")),
                        ("humidity", self.reading(ts_ms, round(self.hum, 1), "%RH"))]
            # Env nodes built from the env_node kit also carry a CO2 and a particle sensor.
            if "co2_ppm" in self.d["capabilities"]:
                self.co2 += (self.rng.gauss(0, 6) - (self.co2 - 700) * 0.01) * 5.0
                self.pm = max(1.0, self.pm + (self.rng.gauss(0, 0.4) - (self.pm - 9) * 0.02) * 5.0)
                out += [("co2_ppm", self.reading(ts_ms, round(self.co2), "ppm")), ("pm25_ugm3", self.reading(ts_ms, round(self.pm, 1), "µg/m³"))]
            return out
        return []


@dataclass
class DoorSensor(Model):
    open: bool = False
    next_change: float = 0.0
    forced_open_until: float = -1.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        changed = False
        if t >= self.next_change and t >= self.forced_open_until:
            # Someone walks in and out: open 6-20 s, then closed 60-150 s.
            self.open = not self.open
            self.next_change = t + (self.rng.uniform(6, 20) if self.open else self.rng.uniform(60, 150))
            changed = True
        if changed or self.every("hb", t, 30.0):
            return [("open", self.reading(ts_ms, self.open))]
        return []

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action == "door_close":
            self.open, self.forced_open_until, self.next_change = False, -1.0, t + 60.0
            self._due.pop("hb", None)

    def force_open(self, t: float, seconds: float) -> None:
        self.open = True
        self.forced_open_until = t + seconds
        self.next_change = t + seconds
        self._due.pop("hb", None)  # publish now


@dataclass
class Occupancy(Model):
    occupied: bool = True
    next_change: float = 0.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        changed = False
        if t >= self.next_change:
            self.occupied = self.rng.random() < 0.7
            self.next_change = t + self.rng.uniform(40, 120)
            changed = True
        if changed or self.every("hb", t, 30.0):
            return [("occupied", self.reading(ts_ms, self.occupied))]
        return []


@dataclass
class AirQuality(Model):
    co2: float = 650.0
    pm: float = 8.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        self.co2 += (self.rng.gauss(0, 6) - (self.co2 - 700) * 0.01) * dt
        self.pm = max(1.0, self.pm + (self.rng.gauss(0, 0.4) - (self.pm - 9) * 0.02) * dt)
        if self.every("aq", t, 10.0):
            return [("co2_ppm", self.reading(ts_ms, round(self.co2), "ppm")),
                    ("pm25_ugm3", self.reading(ts_ms, round(self.pm, 1), "µg/m³"))]
        return []


@dataclass
class MachineMonitor(Model):
    """A press or packer seen through its monitor: state machine, cycles, motor current, vibration.

    State machine: running -> (idle | fault) -> running, with random dwell times; maintenance
    only on command. Vibration RMS sits around the machine's own baseline with noise; the
    "degrade" command adds a slowly rising offset (a worn bearing), "restore" removes it.
    """
    state: str = "running"
    state_until: float = 0.0
    units: int = 0
    rejects: int = 0
    next_cycle: float = 0.0
    vib_offset: float = 0.0
    degrade_rate: float = 0.0  # mm/s per second while degrading
    surface_c: float = 30.0

    def __post_init__(self) -> None:
        super().__post_init__()
        p = self.d.get("sim", {})
        self.cycle_s = float(p.get("cycle_s", 6.0))
        self.vib_base = float(p.get("vibration_mm_s", 2.0))
        self.i_run = float(p.get("current_a", 10.0))
        self.reject_rate = float(p.get("reject_rate", 0.0))
        self.alarms = list(p.get("alarms", ["Fault"]))
        self.state_until = self.rng.uniform(40, 90)
        self.pending: list[tuple[str, Payload]] = []

    def set_state(self, state: str, t: float, dwell: float, ts_ms: int) -> None:
        self.state, self.state_until = state, t + dwell
        self.pending.append(("state", self.reading(ts_ms, state)))
        if state == "fault":
            self.pending.append(("alarm", self.reading(ts_ms, self.rng.choice(self.alarms))))
        if state == "running":
            self.next_cycle = t + self.cycle_s

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action == "degrade":
            self.degrade_rate = 0.015  # +0.9 mm/s per minute: visible within a minute, not instant
        elif action == "restore":
            self.degrade_rate, self.vib_offset = 0.0, 0.0
        elif action == "maintenance":
            self.set_state("maintenance", t, 30.0, ts_ms)

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        out: Out = []
        if t >= self.state_until and self.state != "running":
            self.set_state("running", t, self.rng.uniform(40, 120), ts_ms)
        elif t >= self.state_until:
            r = self.rng.random()
            if r < 0.08:
                self.set_state("fault", t, self.rng.uniform(15, 40), ts_ms)
            elif r < 0.22:
                self.set_state("idle", t, self.rng.uniform(8, 25), ts_ms)  # starved: waiting for material
            else:
                self.state_until = t + self.rng.uniform(40, 120)
        self.vib_offset += self.degrade_rate * dt
        if self.state == "running" and t >= self.next_cycle:
            # Each cycle runs a little slower than ideal (micro-stops); a worn machine slows more.
            took = self.cycle_s * self.rng.uniform(1.0, 1.12) * (1 + 0.05 * self.vib_offset)
            self.next_cycle = t + took
            if self.rng.random() < self.reject_rate:
                self.rejects += 1
                out.append(("rejects", self.reading(ts_ms, self.rejects)))
            else:
                self.units += 1
                out.append(("units", self.reading(ts_ms, self.units)))
            out.append(("cycle_time_s", self.reading(ts_ms, round(took, 2), "s")))
        out += self.pending
        self.pending = []
        if self.every("fast", t, 1.0):
            if self.state == "running":
                vib = self.vib_base + self.vib_offset + self.rng.gauss(0, 0.06 * self.vib_base)
                cur = self.i_run * (1 + self.rng.gauss(0, 0.03)) + 0.8 * self.vib_offset
            else:
                vib, cur = 0.15 + abs(self.rng.gauss(0, 0.03)), (1.2 if self.state == "idle" else 0.0)
            out.append(("vibration_rms", self.reading(ts_ms, round(max(0.0, vib), 3), "mm/s")))
            out.append(("current_a", self.reading(ts_ms, round(max(0.0, cur), 2), "A")))
            if "temperature_c" in self.d["capabilities"]:
                # Surface temperature follows the motor current (heat) and relaxes back to the shop floor's 24 °C.
                target = 24.0 + 2.6 * cur + 3.0 * self.vib_offset
                self.surface_c += (target - self.surface_c) * 0.02
                out.append(("temperature_c", self.reading(ts_ms, round(self.surface_c, 1), "°C")))
        if self.every("state", t, 5.0):
            out.append(("state", self.reading(ts_ms, self.state)))
            out.append(("units", self.reading(ts_ms, self.units)))
            out.append(("rejects", self.reading(ts_ms, self.rejects)))
        return out


WALKWAY_OFFSET_M = 1.7  # walkway beside a forklift aisle (outside a passing forklift's path, inside its 3 m warning radius)


@dataclass
class Badge(Model):
    """A worker's BLE badge. The worker walks a named route (layout node coordinates, looped) at
    walking pace, pausing at work stands (WALK_* nodes). Reports its position once a second.
    The "route" command switches route at the next node (e.g. the visitor's "press_visit")."""
    route_name: str = "default"
    leg: int = 0
    x: float = 0.0
    z: float = 0.0
    pause_until: float = 0.0
    next_route: str | None = None
    goto: tuple[float, float] | None = None  # evacuation: walk straight to the muster point and wait there
    still_until: float = -1.0  # lying still (simulated fall / man-down)
    pending: list[tuple[str, Payload]] = field(default_factory=list)
    last_buzz: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        # (node id, x, z, on a forklift lane)
        self.routes: dict[str, list[tuple[str, float, float, bool]]] = self.d.get("_routes", {})
        self.speed = float(self.d.get("_walk_speed", 1.3))
        pts = self.routes.get(self.route_name) or [("", float(self.d["x"]), float(self.d["z"]), False)]
        _, self.x, self.z, _ = pts[0]
        self.leg = 1 % len(pts)

    def command(self, action: str, t: float, ts_ms: int, data: Payload | None = None) -> None:
        data = data or {}
        if action == "route" and data.get("route") in self.routes:
            self.next_route = str(data["route"])
            self.goto = None
        elif action == "goto" and "x" in data and "z" in data:
            self.goto, self.still_until = (float(data["x"]), float(data["z"])), -1.0
        elif action == "buzz":
            self.last_buzz = str(data.get("route", "alert"))  # the motor/buzzer pattern; nothing to publish
        elif action == "fall":
            # Free fall then impact, then the worker lies still until they cancel (or someone helps).
            self.pending.append(("fall", self.reading(ts_ms, True)))
            self.still_until = t + 3600.0
        elif action == "still":
            self.still_until = t + float(data.get("seconds", 120))
        elif action == "cancel":
            self.pending.append(("cancel", self.reading(ts_ms, True)))
            self.still_until = -1.0
        elif action == "sos":
            self.pending.append(("sos", self.reading(ts_ms, True)))
        elif action == "checkin":
            self.pending.append(("checkin", self.reading(ts_ms, True)))

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        out: Out = self.pending
        self.pending = []
        pts = self.routes.get(self.route_name)
        if t < self.still_until:
            pts = None  # lying still: no walking
        elif self.goto is not None:
            pts = None
            gx, gz = self.goto
            dx, dz = gx - self.x, gz - self.z
            dist = math.hypot(dx, dz)
            stepm = self.speed * 1.3 * dt  # people walk briskly to the muster point
            if dist > 0.5:
                self.x += dx / dist * min(stepm, dist)
                self.z += dz / dist * min(stepm, dist)
        if pts and len(pts) > 1 and t >= self.pause_until:
            name, tx, tz, lane = pts[self.leg]
            _, px, pz, prev_lane = pts[self.leg - 1]
            if lane and prev_lane:
                # Along a forklift aisle people use the walkway beside it, not the lane itself.
                lx, lz = tx - px, tz - pz
                ll = math.hypot(lx, lz) or 1.0
                tx, tz = tx - lz / ll * WALKWAY_OFFSET_M, tz + lx / ll * WALKWAY_OFFSET_M
            dx, dz = tx - self.x, tz - self.z
            dist = math.hypot(dx, dz)
            stepm = self.speed * dt
            if dist <= stepm:
                self.x, self.z = tx, tz
                if name.startswith("WALK_") and name != "WALK_STAFF_DOOR":
                    self.pause_until = t + self.rng.uniform(5, 18)  # working at a stand
                if self.next_route:
                    self.route_name, self.next_route = self.next_route, None
                    pts = self.routes[self.route_name]
                    near = min(range(len(pts)), key=lambda i: math.hypot(pts[i][1] - self.x, pts[i][2] - self.z))  # noqa: B023
                    self.leg = (near + 1) % len(pts)
                else:
                    self.leg = (self.leg + 1) % len(pts)
            else:
                self.x += dx / dist * stepm
                self.z += dz / dist * stepm
        if self.every("pos", t, 1.0):
            out.append(("position", self.reading(ts_ms, [round(self.x, 2), round(self.z, 2)], "m")))
        return out


@dataclass
class TruckTelematics(Model):
    """Telematics on a box truck: speed, cargo door, cargo temperature, harsh events. Position is the truck's own
    position in the twin (a real unit would report GNSS), so it is not published."""
    speed: float = 0.0
    door: bool = False
    cargo_c: float = 0.0
    target: float = 0.0
    next_speed: float = 0.0
    next_event: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.cargo_c = float(self.d.get("sim", {}).get("cargo_c", 17.0))
        self.next_event = self.rng.uniform(90, 200)

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        out: Out = []
        if t >= self.next_speed:
            self.target = self.rng.choice([0.0, 0.0, 8.0, 14.0, 22.0])
            self.next_speed = t + self.rng.uniform(10, 40)
        self.speed += (self.target - self.speed) * min(1.0, dt / 4.0)
        self.cargo_c += (self.rng.gauss(0, 0.02) - (self.cargo_c - 17.0) * 0.002) * dt
        if self.every("door", t, 45.0):
            self.door = self.speed < 1.0 and self.rng.random() < 0.3  # only opened when stopped
            out.append(("door_open", self.reading(ts_ms, self.door)))
        if t >= self.next_event:
            self.next_event = t + self.rng.uniform(120, 300)
            out.append(("harsh_event", self.reading(ts_ms, self.rng.choice(["hard_brake", "hard_accel", "impact"]))))
        if self.every("fast", t, 2.0):
            out.append(("speed_kmh", self.reading(ts_ms, round(max(0.0, self.speed + self.rng.gauss(0, 0.2)), 1), "km/h")))
            out.append(("cargo_temp_c", self.reading(ts_ms, round(self.cargo_c, 2), "°C")))
        return out


@dataclass
class DockBay(Model):
    """Dock bay: a vehicle is parked at the door (ToF occupancy), the door opens while it is there."""
    occupied: bool = False
    next_change: float = 0.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        out: Out = []
        if t >= self.next_change:
            self.occupied = not self.occupied
            self.next_change = t + (self.rng.uniform(90, 200) if self.occupied else self.rng.uniform(40, 120))
            out += [("occupied", self.reading(ts_ms, self.occupied)),
                    ("door_position", self.reading(ts_ms, "open" if self.occupied else "closed")),
                    ("leveler", self.reading(ts_ms, "deployed" if self.occupied else "stowed")),
                    ("dock_light", self.reading(ts_ms, self.occupied))]
        if self.every("hb", t, 30.0):
            out += [("occupied", self.reading(ts_ms, self.occupied)),
                    ("door_position", self.reading(ts_ms, "open" if self.occupied else "closed"))]
        return out


@dataclass
class ConveyorMonitor(Model):
    jam: bool = False
    jam_until: float = 0.0

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action == "jam":
            self.jam, self.jam_until = True, t + 25.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        if self.jam and t >= self.jam_until:
            self.jam = False
        if self.every("fast", t, 2.0):
            run = not self.jam
            cur = (7.5 + self.rng.gauss(0, 0.25)) if run else (13.5 + self.rng.gauss(0, 0.3))  # a jam stalls the motor: current climbs
            speed = (0.55 + self.rng.gauss(0, 0.01)) if run else 0.0
            return [("motor_current_a", self.reading(ts_ms, round(cur, 2), "A")),
                    ("belt_speed_m_s", self.reading(ts_ms, round(max(0.0, speed), 3), "m/s")),
                    ("jam", self.reading(ts_ms, self.jam))]
        return []


@dataclass
class CompressorMonitor(Model):
    """Screw compressor between 6.5 and 7.5 bar: loaded while pressure rises, unloaded while it falls."""
    bar: float = 7.0
    loaded: bool = True
    hours: float = 1240.0
    leak: float = 0.0  # extra air demand (bar/s), set by the scenario

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action == "leak":
            self.leak = 0.02
        elif action == "clear":
            self.leak = 0.0

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        rate = 0.05 if self.loaded else -0.03
        self.bar += (rate - self.leak) * dt
        if self.bar >= 7.5:
            self.loaded = False
        elif self.bar <= 6.5 and self.leak < 0.04:
            self.loaded = True
        self.bar = max(3.0, self.bar)
        self.hours += dt / 3600.0 if self.loaded else 0.0
        if self.every("fast", t, 2.0):
            cur = (46.0 if self.loaded else 13.0) + self.rng.gauss(0, 0.6)
            return [("pressure_bar", self.reading(ts_ms, round(self.bar + self.rng.gauss(0, 0.01), 2), "bar")),
                    ("current_a", self.reading(ts_ms, round(cur, 1), "A")),
                    ("run_hours", self.reading(ts_ms, round(self.hours, 2), "h")),
                    ("dew_point_c", self.reading(ts_ms, round(-22.0 + self.rng.gauss(0, 0.3), 1), "°C"))]
        return []


@dataclass
class HelmetClip(Model):
    worn: bool = True

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        out: Out = []
        if self.every("worn", t, 30.0):
            out.append(("worn", self.reading(ts_ms, self.worn)))
        if self.every("impact", t, 240.0) and self.rng.random() < 0.15:
            out.append(("impact_g", self.reading(ts_ms, round(self.rng.uniform(6, 14), 1), "g")))
        return out


@dataclass
class GasDetector(Model):
    """Fixed CO / O2 detector. "leak" ramps CO up past the alarm threshold, "clear" lets it fall again."""
    co: float = 1.5
    o2: float = 20.9
    leaking: bool = False
    alarm_ppm: float = 35.0

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action == "leak":
            self.leaking = True
        elif action == "clear":
            self.leaking = False

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        goal = 90.0 if self.leaking else 1.5
        self.co += (goal - self.co) * min(1.0, dt / (12.0 if self.leaking else 25.0))
        self.o2 = 20.9 - (self.co / 90.0) * 0.4 + self.rng.gauss(0, 0.01)
        if self.every("gas", t, 2.0):
            alarm = self.co >= self.alarm_ppm
            return [("co_ppm", self.reading(ts_ms, round(max(0.0, self.co + self.rng.gauss(0, 0.2)), 1), "ppm")),
                    ("o2_pct", self.reading(ts_ms, round(self.o2, 2), "%")),
                    ("alarm", self.reading(ts_ms, alarm))]
        return []


@dataclass
class LeakSensor(Model):
    wet: bool = False

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action in ("leak", "clear"):
            self.wet = action == "leak"
            self._due.pop("hb", None)

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        return [("wet", self.reading(ts_ms, self.wet))] if self.every("hb", t, 30.0) else []


@dataclass
class TankLevel(Model):
    """Day tank: a pump refills it when it falls below 30 %, draw-off is steady."""
    level: float = 72.0
    pumping: bool = False

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        self.level += (1.1 if self.pumping else -0.12) * dt / 10.0
        if self.level <= 30.0:
            self.pumping = True
        elif self.level >= 90.0:
            self.pumping = False
        if self.every("lvl", t, 10.0):
            return [("level_pct", self.reading(ts_ms, round(self.level + self.rng.gauss(0, 0.15), 1), "%")),
                    ("pump_on", self.reading(ts_ms, self.pumping))]
        return []


@dataclass
class FirePanel(Model):
    """Dry contacts read from an existing fire panel. We only read; we never raise or silence the real panel."""
    alarm: bool = False
    trouble: bool = False

    def command(self, action: str, t: float, ts_ms: int) -> None:
        if action in ("alarm", "reset"):
            self.alarm = action == "alarm"
            self._due.pop("hb", None)

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        if self.every("hb", t, 10.0):
            return [("alarm", self.reading(ts_ms, self.alarm)), ("trouble", self.reading(ts_ms, self.trouble))]
        return []


@dataclass
class PowerMeter(Model):
    """DIN-rail meter on a feeder: power follows a base load plus a slow wave and noise."""
    kwh: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.base_kw = float(self.d.get("sim", {}).get("base_kw", 18.0))
        self.kwh = float(self.d.get("sim", {}).get("kwh", 5200.0))

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        kw = self.base_kw * (1 + 0.15 * math.sin(t / 90.0)) + self.rng.gauss(0, 0.2)
        self.kwh += kw * dt / 3600.0
        if self.every("pw", t, 5.0):
            return [("power_kw", self.reading(ts_ms, round(kw, 2), "kW")), ("energy_kwh", self.reading(ts_ms, round(self.kwh, 2), "kWh")),
                    ("voltage_v", self.reading(ts_ms, round(400.0 + self.rng.gauss(0, 1.2), 1), "V"))]
        return []


@dataclass
class AssetTag(Model):
    find_until: float = -1.0

    def command(self, action: str, t: float, ts_ms: int, data: Payload | None = None) -> None:
        if action == "find_me":
            self.find_until = t + float((data or {}).get("seconds", 10))
            self._due.pop("hb", None)

    def step(self, t: float, dt: float, ts_ms: int) -> Out:
        super().step(t, dt, ts_ms)
        finding = t < self.find_until
        if self.every("hb", t, 20.0 if not finding else 1.0):
            return [("find_me", self.reading(ts_ms, finding))]
        return []


MODELS: dict[str, type[Model]] = {"badge": Badge, "machine_monitor": MachineMonitor, "env_sensor": EnvSensor, "door_sensor": DoorSensor,
                                  "occupancy_sensor": Occupancy, "air_quality": AirQuality, "truck_telematics": TruckTelematics,
                                  "dock_bay": DockBay, "conveyor_monitor": ConveyorMonitor, "compressor_monitor": CompressorMonitor,
                                  "helmet_clip": HelmetClip, "gas_detector": GasDetector, "leak_sensor": LeakSensor,
                                  "tank_level": TankLevel, "fire_panel": FirePanel, "power_meter": PowerMeter, "asset_tag": AssetTag}


def make(d: dict[str, Any], rng: random.Random) -> Model:
    return MODELS.get(d["type"], Model)(d, rng)
