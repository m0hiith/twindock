"""People wearing simulated badges (true positions and badge events). Numbers in params/people.yaml.

A worker walks their named route (layout node coordinates, looped) at walking pace, keeps to the walkway beside a
forklift aisle, and pauses at work stands (WALK_* nodes). Commands: route (switch at the next node), goto (walk the
given walkway path to a point, e.g. the muster point), fall / still (lie still), cancel, sos, checkin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..core import Model

Route = list[tuple[str, float, float, bool]]  # (node id, x, z, on a forklift lane)


@dataclass
class Walker:
    badge: str
    routes: dict[str, Route]
    speed: float
    checkin_s: float
    route_name: str = "default"
    leg: int = 0
    x: float = 0.0
    z: float = 0.0
    pause_until: float = 0.0
    next_route: str | None = None
    goto: tuple[float, float] | None = None
    path: list[tuple[float, float]] = field(default_factory=list)
    still_until: float = -1.0
    skip_checkin: bool = False
    next_checkin: float = 0.0
    last_buzz: str | None = None
    events: list[str] = field(default_factory=list)  # fall / sos / cancel / checkin, reported by the badge at once

    @property
    def moving(self) -> bool:
        return self.goto is not None or len(self.routes.get(self.route_name, [])) > 1


class People(Model):
    key = "people"
    title = "People (workers with badges)"
    equations = (
        "Position moves towards the next route node at walking speed: Δs = v × dt.",
        "Along a forklift aisle the worker keeps to the walkway, offset sideways from the lane centre line.",
        "At a work stand the worker pauses for a drawn time.",
        "Evacuation: walk the given walkway path to the muster point at evacuation pace (walking speed × factor).",
        "Lone-worker check-in: the badge's double press every check-in period, unless the worker forgets (demo).",
    )
    writes = ("people_in_zone",)
    params_prefix = ("people",)

    def __init__(self, cfg: dict[str, Any], layout_nodes: dict[str, dict[str, Any]]) -> None:
        self.cfg = cfg
        self.walkers: dict[str, Walker] = {}
        self._layout_nodes = layout_nodes

    def bind(self, core: Any) -> None:
        super().bind(core)
        p = core.p
        workers = {w["badge"]: w for w in self.cfg.get("workers", [])}
        for d in self.cfg["devices"]:
            if d["type"] != "badge" or d["source"] != "sim":
                continue
            w = workers.get(d["id"])
            routes: dict[str, Route] = {}
            if w is not None:
                nodes = self._layout_nodes
                routes = {name: [(nid, float(nodes[nid]["x"]), float(nodes[nid]["z"]), bool(nodes[nid]["kinds"])) for nid in ids]
                          for name, ids in w["routes"].items()}
            wk = Walker(d["id"], routes, p.f("people.walk_speed_mps"), float(d.get("sim", {}).get("checkin_s", 0)))
            pts = routes.get("default") or [("", float(d["x"]), float(d["z"]), False)]
            _, wk.x, wk.z, _ = pts[0]
            wk.leg = 1 % len(pts)
            wk.next_checkin = wk.checkin_s
            self.walkers[d["id"]] = wk

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        w = self.walkers.get(target)
        if w is None:
            return False
        t, p = self.core.t, self.core.p
        if action == "route" and data.get("route") in w.routes:
            w.next_route, w.goto = str(data["route"]), None
        elif action == "goto" and "x" in data and "z" in data:
            w.goto, w.still_until = (float(data["x"]), float(data["z"])), -1.0
            w.path = [(float(a), float(b)) for a, b in data.get("path", [])]
        elif action == "buzz":
            w.last_buzz = str(data.get("route", "alert"))
        elif action == "fall":
            w.events.append("fall")  # free fall, impact, then the worker lies still until they cancel
            w.still_until = t + p.f("people.fall_lie_still_s")
        elif action == "still":
            w.still_until = t + float(data.get("seconds", p.f("people.still_default_s")))
        elif action == "cancel":
            w.events.append("cancel")
            w.still_until = -1.0
        elif action in ("sos", "checkin"):
            w.events.append(action)
        elif action == "skip_checkin":
            w.skip_checkin = bool(data.get("on", True))
        else:
            return action == "route"  # an unknown route name is ignored, not an error
        self.core.record(f"{target} {action}", f"{action} command")
        return True

    def step(self, dt: float) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        offset = p.f("people.walkway_offset_m")
        for w in self.walkers.values():
            pts = w.routes.get(w.route_name)
            if t < w.still_until:
                pts = None
            elif w.goto is not None:
                pts = None
                gx, gz = w.path[0] if w.path else w.goto
                dx, dz = gx - w.x, gz - w.z
                dist = math.hypot(dx, dz)
                stepm = w.speed * p.f("people.evacuation_pace_factor") * dt
                if dist > p.f("people.arrive_within_m"):
                    w.x += dx / dist * min(stepm, dist)
                    w.z += dz / dist * min(stepm, dist)
                elif w.path:
                    w.path.pop(0)
            if pts and len(pts) > 1 and t >= w.pause_until:
                name, tx, tz, lane = pts[w.leg]
                _, px, pz, prev_lane = pts[w.leg - 1]
                if lane and prev_lane:
                    lx, lz = tx - px, tz - pz
                    ll = math.hypot(lx, lz) or 1.0
                    tx, tz = tx - lz / ll * offset, tz + lx / ll * offset
                dx, dz = tx - w.x, tz - w.z
                dist = math.hypot(dx, dz)
                stepm = w.speed * dt
                if dist <= stepm:
                    w.x, w.z = tx, tz
                    if name.startswith("WALK_") and name != "WALK_STAFF_DOOR":
                        w.pause_until = t + core.rng.draw("people.work_stand_pause_s", f"{w.badge}.pause")
                    if w.next_route:
                        w.route_name, w.next_route = w.next_route, None
                        pts = w.routes[w.route_name]
                        near = min(range(len(pts)), key=lambda i: math.hypot(pts[i][1] - w.x, pts[i][2] - w.z))  # noqa: B023
                        w.leg = (near + 1) % len(pts)
                    else:
                        w.leg = (w.leg + 1) % len(pts)
                else:
                    w.x += dx / dist * stepm
                    w.z += dz / dist * stepm
            if w.checkin_s and not w.skip_checkin and t >= w.next_checkin:
                w.events.append("checkin")
                w.next_checkin = t + w.checkin_s
