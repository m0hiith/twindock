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
      "light": "sim-1.0", "air_quality": "sim-1.3"}

# Mains-powered devices report no battery; the rest start somewhere plausible.
MAINS = {"machine_monitor", "air_quality", "power_meter", "light", "gateway"}

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
            return [("temperature", self.reading(ts_ms, round(self.temp, 2), "°C")),
                    ("humidity", self.reading(ts_ms, round(self.hum, 1), "%RH"))]
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


MODELS: dict[str, type[Model]] = {"env_sensor": EnvSensor, "door_sensor": DoorSensor,
                                  "occupancy_sensor": Occupancy, "air_quality": AirQuality}


def make(d: dict[str, Any], rng: random.Random) -> Model:
    return MODELS.get(d["type"], Model)(d, rng)
