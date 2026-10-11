"""Rooms, doors, air, gas, fire panels, leaks, effluent quality, asset tags and helmets (true state).

Every number is in params/environment.yaml. Randomness is only where the real world is random (when people open a
door, when a room is occupied, small drifts in a room's air), through named distributions and streams.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..core import Model


@dataclass
class Room:
    zone: str
    kind: str          # cold | conditioned | open (follows the weather and its own heat)
    temp_c: float = 0.0
    rh_pct: float = 0.0
    co2_ppm: float = 0.0
    pm25: float = 0.0
    door_open: bool = False


def sat_vp_kpa(t_c: float, magnus: dict[str, float]) -> float:
    """Saturation vapour pressure (Magnus formula, kPa) with the coefficients from params."""
    return float(magnus["e0_kpa"]) * math.exp(float(magnus["b"]) * t_c / (float(magnus["c_c"]) + t_c))


class Rooms(Model):
    key = "rooms"
    title = "Rooms: temperature, humidity, CO₂ and particles"
    equations = (
        "Open halls (not air-conditioned): dT/dt = (T_outdoor + k_zone × heat released in the zone (kW) − T) / τ_hall. "
        "Everything a zone's machines, compressors and lights draw ends up as heat in it.",
        "Air-conditioned rooms relax to their setpoint (τ_ac); the cold room to its setpoint, or towards the hall while its door is open.",
        "Outdoor humidity follows the day (driest when warmest). An open hall holds the outdoor moisture: "
        "RH_room = RH_outdoor × e_s(T_outdoor) / e_s(T_room) (Magnus formula), so a hotter hall is drier; conditioned rooms sit at their RH.",
        "A small random walk (σ √dt) stands for draughts and loads the model doesn't track.",
        "CO₂ relaxes to the room's level with τ_co2 and drifts; particles likewise.",
        "Cold room refrigeration: duty = base + gain × (T − setpoint), between 0 and 1; electrical load = rated kW × duty.",
    )
    reads = ("flags.door_open", "flags.outdoor_c", "power_kw")
    writes = ("power_kw", "flags.outdoor_rh")
    params_prefix = ("rooms",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.rooms: dict[str, Room] = {}
        for d in cfg["devices"]:
            if d["type"] in ("env_sensor", "air_quality") and d["zone_id"] not in self.rooms:
                self.rooms[d["zone_id"]] = Room(d["zone_id"], "cold" if "COLD" in d["zone_id"] else "open")

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        cond = set(p.v("rooms.conditioned_zones"))
        out = self._outdoor()
        for r in self.rooms.values():
            if r.kind != "cold" and r.zone in cond:
                r.kind = "conditioned"
            base = {"cold": p.f("rooms.cold.setpoint_c"), "conditioned": p.f("rooms.conditioned.setpoint_c")}.get(r.kind, out[0])
            r.temp_c = base + core.rng.draw("rooms.initial_offset_c", f"{r.zone}.init")
            r.rh_pct = {"cold": p.f("rooms.cold.rh_pct"), "conditioned": p.f("rooms.conditioned.rh_pct")}.get(r.kind, out[1])
            r.co2_ppm = p.f("rooms.co2.level_ppm")
            r.pm25 = p.f("rooms.pm25.level_ugm3")

    def _outdoor(self) -> tuple[float, float]:
        """(temperature, relative humidity) outdoors now."""
        p = self.core.p
        h = self.core.hour_of_day()
        t = float(self.core.q.flags.get("outdoor_c", p.f("weather.mean_c")))
        rh = p.f("rooms.outdoor_rh.mean_pct") - p.f("rooms.outdoor_rh.amplitude_pct") * math.cos(2 * math.pi * (h - p.f("weather.warmest_h")) / 24)
        return t, rh

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        doors = core.q.flags.get("door_open_zones", set())
        sq = math.sqrt(dt)
        t_out, rh_out = self._outdoor()
        core.q.flags["outdoor_rh"] = rh_out
        heat: dict[str, float] = {}
        for name, kw in core.q.power_kw.items():
            z = core.q.power_zone.get(name)
            if z is not None:
                heat[z] = heat.get(z, 0.0) + kw
        k_by_zone = p.v("rooms.open.k_c_per_kw")
        hall = self.rooms.get(str(p.v("rooms.cold.next_to")))
        for r in self.rooms.values():
            r.door_open = r.zone in doors
            if r.kind == "cold":
                around = hall.temp_c if hall is not None else t_out
                if r.door_open:
                    r.temp_c += (around - r.temp_c) * dt / p.f("rooms.tau_door_s")
                else:
                    r.temp_c += (p.f("rooms.cold.setpoint_c") - r.temp_c) * dt / p.f("rooms.tau_cool_s")
                rh_target = p.f("rooms.cold.rh_pct")
            elif r.kind == "conditioned":
                r.temp_c += (p.f("rooms.conditioned.setpoint_c") - r.temp_c) * dt / p.f("rooms.conditioned.tau_s")
                rh_target = p.f("rooms.conditioned.rh_pct")
            else:
                k = float(k_by_zone.get(r.zone, k_by_zone["default"]))
                target = t_out + k * heat.get(r.zone, 0.0)
                r.temp_c += (target - r.temp_c) * dt / p.f("rooms.open.tau_s")
                mg = p.v("rooms.magnus")
                rh_target = min(100.0, rh_out * sat_vp_kpa(t_out, mg) / sat_vp_kpa(r.temp_c, mg))
            r.temp_c += core.rng.gauss(f"{r.zone}.temp", p.f("rooms.temp_walk_c_per_sqrt_s")) * sq
            r.rh_pct += (rh_target - r.rh_pct) * dt / p.f("rooms.tau_rh_s") + core.rng.gauss(f"{r.zone}.rh", p.f("rooms.rh_walk_pct_per_sqrt_s")) * sq
            r.rh_pct = min(100.0, max(0.0, r.rh_pct))
            r.co2_ppm += (p.f("rooms.co2.level_ppm") - r.co2_ppm) * dt / p.f("rooms.co2.tau_s") + core.rng.gauss(f"{r.zone}.co2", p.f("rooms.co2.walk_ppm_per_sqrt_s")) * sq
            r.pm25 = max(p.f("rooms.pm25.floor_ugm3"), r.pm25 + (p.f("rooms.pm25.level_ugm3") - r.pm25) * dt / p.f("rooms.pm25.tau_s")
                         + core.rng.gauss(f"{r.zone}.pm", p.f("rooms.pm25.walk_ugm3_per_sqrt_s")) * sq)
            if r.kind == "cold":
                on = core.q.powered(r.zone)
                duty = min(1.0, max(0.0, p.f("rooms.refrigeration.base_duty") + p.f("rooms.refrigeration.gain_per_c") * (r.temp_c - p.f("rooms.cold.setpoint_c"))))
                name = f"Refrigeration {r.zone}"
                core.q.power_kw[name] = p.f("rooms.refrigeration.rated_kw") * duty if on else 0.0
                core.q.power_zone[name] = r.zone
                core.q.power_kind[name] = "motor"


class Doors(Model):
    key = "doors"
    title = "Doors (people walking through, fire door holds, cold room door alarm)"
    equations = (
        "Each door alternates open and closed; open and closed times are drawn from their distributions.",
        "A demo command can hold a door open for a given time; door_close shuts it now.",
        "Interlock: on a fire alarm the magnetic holds release and every fire door closes (and stays closed until the alarm clears).",
        "The cold room door sounds its local alarm once it has been open longer than its limit.",
    )
    reads = ("flags.fire_alarm",)
    writes = ("flags.door_open_zones", "flags.cold_door_alarm")
    params_prefix = ("doors",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.doors = {d["id"]: {"zone": d["zone_id"], "open": False, "next": 0.0, "forced_until": -1.0, "opened_at": None}
                      for d in cfg["devices"] if d["type"] == "door_sensor"}
        self.changed: set[str] = set()
        self.fire = False
        self.cold_alarm = False

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        dr = self.doors.get(target)
        if dr is None:
            return False
        t = self.core.t
        if action == "door_open":
            secs = float(data.get("seconds", self.core.p.f("doors.default_hold_s")))
            dr.update(open=True, forced_until=t + secs, next=t + secs, opened_at=t)
        elif action == "door_close":
            dr.update(open=False, forced_until=-1.0, next=t + self.core.rng.draw("doors.closed_s", f"{target}.door"))
        else:
            return False
        self.changed.add(target)
        self.core.record(f"{target} {action}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        core, t = self.core, self.core.t
        fire = bool(core.q.flags.get("fire_alarm"))
        fire_doors = set(core.p.v("doors.fire_doors"))
        if fire != self.fire:
            self.fire = fire
            core.record("fire door holds released" if fire else "fire door holds back on", "interlock: fire alarm" if fire else "fire alarm reset")
        alarm = False
        for did, dr in self.doors.items():
            if fire and did in fire_doors:
                if dr["open"]:
                    dr["open"], dr["next"], dr["forced_until"] = False, t, -1.0
                    self.changed.add(did)
                continue
            if t >= dr["next"] and t >= dr["forced_until"]:
                dr["open"] = not dr["open"]
                dr["next"] = t + core.rng.draw("doors.open_s" if dr["open"] else "doors.closed_s", f"{did}.door")
                dr["opened_at"] = t if dr["open"] else None
                self.changed.add(did)
            if dr["open"] and dr.get("opened_at") is None:
                dr["opened_at"] = t
            if "COLD" in dr["zone"] and dr["open"] and t - (dr.get("opened_at") or t) >= core.p.f("doors.cold_door_alarm_s"):
                alarm = True
        if alarm != self.cold_alarm:
            self.cold_alarm = alarm
            core.record("cold room door alarm sounding" if alarm else "cold room door alarm silent",
                        f"door open longer than {core.p.f('doors.cold_door_alarm_s'):.0f} s" if alarm else "door closed")
        core.q.flags["cold_door_alarm"] = alarm
        core.q.flags["door_open_zones"] = {dr["zone"] for dr in self.doors.values() if dr["open"]}


class Occupancy(Model):
    key = "occupancy"
    title = "Room occupancy"
    equations = ("Every drawn interval a room is occupied with probability p_occupied (meeting rooms, offices).",)
    params_prefix = ("occupancy",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.rooms = {d["id"]: {"occupied": True, "next": 0.0} for d in cfg["devices"] if d["type"] == "occupancy_sensor"}
        self.changed: set[str] = set()

    def step(self, dt: float) -> None:
        t = self.core.t
        for did, r in self.rooms.items():
            if t >= r["next"]:
                r["occupied"] = bool(self.core.rng.draw("occupancy.occupied", f"{did}.occ"))
                r["next"] = t + self.core.rng.draw("occupancy.interval_s", f"{did}.occ")
                self.changed.add(did)


class Gas(Model):
    key = "gas"
    title = "Gas (CO and O₂) at the fixed detectors"
    equations = (
        "CO relaxes towards the leak level while a leak is on (τ_rise) and back to background after (τ_fall).",
        "Interlock: a detector in alarm runs its zone's extract fan at full speed: the decay is faster (τ_vent) and the fan draws its kW.",
        "O₂ is displaced in proportion: O₂ = 20.9 % − dilution × CO / leak level.",
    )
    writes = ("flags.gas_alarm_zones", "power_kw")
    params_prefix = ("gas",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.points = {d["id"]: {"zone": d["zone_id"], "co": 0.0, "o2": 0.0, "leaking": False} for d in cfg["devices"] if d["type"] == "gas_detector"}

    def bind(self, core: Any) -> None:
        super().bind(core)
        for g in self.points.values():
            g["co"], g["o2"] = core.p.f("gas.co_background_ppm"), core.p.f("gas.o2_air_pct")

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        g = self.points.get(target)
        if g is None or action not in ("leak", "clear"):
            return False
        g["leaking"] = action == "leak"
        self.core.record(f"{target} gas {'leak' if g['leaking'] else 'cleared'}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        core, p = self.core, self.core.p
        alarm_zones: set[str] = set()
        for did, g in self.points.items():
            vent = g.get("vent", False)
            goal = p.f("gas.co_leak_ppm") * (p.f("gas.vent_dilution") if vent else 1.0) if g["leaking"] else p.f("gas.co_background_ppm")
            tau = p.f("gas.tau_rise_s") if g["leaking"] else (p.f("gas.tau_vent_s") if vent else p.f("gas.tau_fall_s"))
            g["co"] += (goal - g["co"]) * min(1.0, dt / tau)
            g["o2"] = p.f("gas.o2_air_pct") - (g["co"] / p.f("gas.co_leak_ppm")) * p.f("gas.o2_dilution_pct")
            alarm = self.alarm(did)
            if alarm:
                alarm_zones.add(g["zone"])
            if alarm != vent and (alarm or g["co"] < p.f("gas.vent_off_ppm")):
                g["vent"] = alarm
                core.record(f"{g['zone']} extract fan {'full speed' if alarm else 'back to normal'}",
                            f"interlock: {did} {'in alarm' if alarm else 'clear'}")
            name = f"Extract fan {did}"
            core.q.power_kw[name] = p.f("gas.fan_kw") if g.get("vent") else p.f("gas.fan_idle_kw")
            core.q.power_zone[name] = g["zone"]
            core.q.power_kind[name] = "motor"
        core.q.flags["gas_alarm_zones"] = alarm_zones

    def alarm(self, did: str) -> bool:
        return float(self.points[did]["co"]) >= self.core.p.f("gas.alarm_ppm")


class FirePanels(Model):
    key = "fire"
    title = "Fire panel contacts"
    equations = ("Alarm and trouble are contacts read from the certified fire panel; they change only on the panel (demo command).",)
    writes = ("flags.fire_alarm",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.panels = {d["id"]: {"alarm": False, "trouble": False} for d in cfg["devices"] if d["type"] == "fire_panel"}
        self.changed: set[str] = set()

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        fp = self.panels.get(target)
        if fp is None or action not in ("alarm", "reset"):
            return False
        fp["alarm"] = action == "alarm"
        self.changed.add(target)
        self.core.record(f"{target} fire {action}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        self.core.q.flags["fire_alarm"] = any(fp["alarm"] for fp in self.panels.values())


class Leaks(Model):
    key = "leaks"
    title = "Water leak probes"
    equations = ("A probe is wet while water is present (demo command leak / clear).",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.wet = {d["id"]: False for d in cfg["devices"] if d["type"] == "leak_sensor"}
        self.changed: set[str] = set()

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        if target not in self.wet or action not in ("leak", "clear"):
            return False
        self.wet[target] = action == "leak"
        self.changed.add(target)
        self.core.record(f"{target} {'wet' if self.wet[target] else 'dry'}", f"{action} command")
        return True


class WaterQuality(Model):
    key = "effluent"
    title = "Effluent treatment quality (pH, turbidity)"
    equations = (
        "Inflow: raw effluent, rough by nature. Outflow: inside the treated band.",
        "pH and turbidity relax to their level with τ; an upset moves the outflow's level out of band until cleared.",
        "A hydraulically overloaded ETP (equalisation tank at overflow) carries solids over: outflow turbidity rises.",
    )
    params_prefix = ("effluent",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.probes = {d["id"]: {"inflow": bool(d.get("sim", {}).get("inflow", False)), "ph": 0.0, "ntu": 0.0, "upset": False}
                       for d in cfg["devices"] if d["type"] == "water_quality"}

    def level(self, w: dict[str, Any]) -> tuple[float, float]:
        p = self.core.p
        if w["inflow"]:
            return p.f("effluent.inflow.ph"), p.f("effluent.inflow.turbidity_ntu")
        if w["upset"]:
            return p.f("effluent.upset.ph"), p.f("effluent.upset.turbidity_ntu")
        if self.core.q.flags.get("etp_overload"):
            return p.f("effluent.outflow.ph"), p.f("effluent.overload.turbidity_ntu")  # hydraulic overload: solids carry over
        return p.f("effluent.outflow.ph"), p.f("effluent.outflow.turbidity_ntu")

    def bind(self, core: Any) -> None:
        super().bind(core)
        for w in self.probes.values():
            w["ph"], w["ntu"] = self.level(w)

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        w = self.probes.get(target)
        if w is None:
            return False
        if action in ("upset", "leak"):
            w["upset"] = True
        elif action in ("clear", "restore"):
            w["upset"] = False
        else:
            return False
        self.core.record(f"{target} {'upset' if w['upset'] else 'normal'}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        p = self.core.p
        k = min(1.0, dt / p.f("effluent.tau_s"))
        for did, w in self.probes.items():
            ph, ntu = self.level(w)
            w["ph"] += (ph - w["ph"]) * k
            w["ntu"] = max(0.0, w["ntu"] + (ntu - w["ntu"]) * k)


class AssetTags(Model):
    key = "tags"
    title = "Pallet asset tags (find-me)"
    equations = ("find_me lights and beeps the tag for the requested seconds.",)
    params_prefix = ("tags",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.until = {d["id"]: -1.0 for d in cfg["devices"] if d["type"] == "asset_tag"}
        self.changed: set[str] = set()

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        if target not in self.until or action != "find_me":
            return False
        self.until[target] = self.core.t + float(data.get("seconds", self.core.p.f("tags.find_me_s")))
        self.changed.add(target)
        self.core.record(f"{target} find me", "find_me command")
        return True

    def finding(self, did: str) -> bool:
        return self.core.t < self.until[did]


class Helmets(Model):
    key = "helmets"
    title = "Smart helmet clips"
    equations = ("Worn while on the head. Small knocks happen at a low, documented rate (a bump on a rack or a door frame).",)
    params_prefix = ("helmets",)

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.clips = {d["id"]: {"worn": True, "next_knock": 0.0, "impact": None} for d in cfg["devices"] if d["type"] == "helmet_clip"}

    def bind(self, core: Any) -> None:
        super().bind(core)
        for did, c in self.clips.items():
            c["next_knock"] = core.rng.draw("helmets.time_between_knocks_s", f"{did}.knock")

    def step(self, dt: float) -> None:
        t = self.core.t
        for did, c in self.clips.items():
            if t >= c["next_knock"]:
                c["impact"] = self.core.rng.draw("helmets.knock_g", f"{did}.knock")
                c["next_knock"] = t + self.core.rng.draw("helmets.time_between_knocks_s", f"{did}.knock")
                self.core.record(f"{did} knock {c['impact']:.1f} g", "random bump (documented rate)")
