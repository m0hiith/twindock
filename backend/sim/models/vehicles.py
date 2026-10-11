"""Truck telematics and dock bays (true state). Numbers in params/vehicles.yaml."""

from __future__ import annotations

from typing import Any

from ..core import Model


class Telematics(Model):
    key = "telematics"
    title = "Truck telematics (speed, cargo door, cargo temperature, harsh events)"
    equations = (
        "Speed follows a target speed with a first-order lag (τ); the target changes at drawn intervals.",
        "Cargo temperature relaxes to the reefer setpoint (τ) with a small random walk.",
        "The cargo door can only open while the truck is stopped.",
        "Harsh events (hard brake, hard acceleration, impact) at drawn intervals.",
    )
    params_prefix = ("vehicles",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.trucks = {d["id"]: {"speed": 0.0, "target": 0.0, "next_speed": 0.0, "door": False, "cargo_c": 0.0,
                                 "setpoint": d.get("sim", {}).get("cargo_c"), "next_event": 0.0, "events": []}
                       for d in cfg["devices"] if d["type"] == "truck_telematics"}

    def bind(self, core: Any) -> None:
        super().bind(core)
        for did, tr in self.trucks.items():
            if tr["setpoint"] is None:
                tr["setpoint"] = core.p.f("vehicles.cargo.ambient_c")
            tr["cargo_c"] = float(tr["setpoint"])
            tr["next_event"] = core.rng.draw("vehicles.harsh_event_interval_s", f"{did}.harsh")

    def step(self, dt: float) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        for did, tr in self.trucks.items():
            if t >= tr["next_speed"]:
                speeds = list(p.v("vehicles.target_speeds_kmh"))
                tr["target"] = float(speeds[int(core.rng.stream(f"{did}.speed").random() * len(speeds))])
                tr["next_speed"] = t + core.rng.draw("vehicles.speed_change_s", f"{did}.speed")
            tr["speed"] += (tr["target"] - tr["speed"]) * min(1.0, dt / p.f("vehicles.speed_tau_s"))
            tr["cargo_c"] += (float(tr["setpoint"]) - tr["cargo_c"]) * dt / p.f("vehicles.cargo.tau_s") \
                + core.rng.gauss(f"{did}.cargo", p.f("vehicles.cargo.walk_c_per_sqrt_s")) * dt ** 0.5
            if tr["door"] and tr["speed"] >= p.f("vehicles.door.stopped_below_kmh"):
                tr["door"] = False
            if t >= tr["next_event"]:
                kinds = list(p.v("vehicles.harsh_event_kinds"))
                tr["events"].append(kinds[int(core.rng.stream(f"{did}.harsh").random() * len(kinds))])
                tr["next_event"] = t + core.rng.draw("vehicles.harsh_event_interval_s", f"{did}.harsh")

    def door_check(self, did: str) -> bool:
        """Called on the device's door report: the driver opens the door now and then while stopped."""
        tr = self.trucks[did]
        p = self.core.p
        tr["door"] = tr["speed"] < p.f("vehicles.door.stopped_below_kmh") and bool(self.core.rng.draw("vehicles.door.opened_when_stopped", f"{did}.door"))
        return bool(tr["door"])


class DockBays(Model):
    key = "docks"
    title = "Dock bays (trailer present, door, leveler, light)"
    equations = (
        "A bay is occupied for a drawn dwell, then free for a drawn gap; door, leveler and light follow occupancy.",
        "An occupied bay draws its leveler and lighting load.",
    )
    writes = ("power_kw",)
    params_prefix = ("docks",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.bays = {d["id"]: {"zone": d["zone_id"], "occupied": False, "next": 0.0} for d in cfg["devices"] if d["type"] == "dock_bay"}
        self.changed: set[str] = set()

    def step(self, dt: float) -> None:
        core, t = self.core, self.core.t
        for did, b in self.bays.items():
            if t >= b["next"]:
                b["occupied"] = not b["occupied"]
                b["next"] = t + core.rng.draw("docks.occupied_s" if b["occupied"] else "docks.free_s", f"{did}.bay")
                self.changed.add(did)
                core.record(f"{did} {'trailer in' if b['occupied'] else 'trailer out'}", "drawn dock dwell ended")
            core.q.power_kw[did] = core.p.f("docks.occupied_kw") if b["occupied"] else 0.0
            core.q.power_zone[did] = b["zone"]
            core.q.power_kind[did] = "motor"
