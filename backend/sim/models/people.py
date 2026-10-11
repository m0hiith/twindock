"""People wearing simulated badges (true positions and badge events). Numbers in params/people.yaml.

The roster (sites.json workers, `shift`) says who works which shift. A worker arrives through the gate a few
minutes before their shift, walks the walkways to their round, walks their round (pausing at work stands), goes to
the canteen in a meal break, and leaves through the gate after the shift; off shift their badge is in the gate rack,
switched off. Walking is on the pedestrian graph (walkways and marked crossings), at walking pace. Commands: route
(switch at the next node), goto (walk the given walkway path to a point: muster point, a work order's machine),
fall / still (lie still), cancel, sos, checkin. Falls and SOS happen on their own only at a very low documented rate.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any

from ..core import Model
from .production import shift_phase

Route = list[tuple[str, float, float, bool]]  # (node id, x, z, on a forklift lane)


@dataclass
class Walker:
    badge: str
    worker: str
    role: str
    shift: str | None
    routes: dict[str, Route]
    speed: float
    checkin_s: float
    status: str = "init"               # init (decided on the first step) | off_site | arriving | working | break | leaving
    route_name: str = "default"
    leg: int = 0
    x: float = 0.0
    z: float = 0.0
    pause_until: float = 0.0
    next_route: str | None = None
    goto: tuple[float, float] | None = None
    path: list[tuple[float, float]] = field(default_factory=list)
    walk: list[tuple[float, float]] = field(default_factory=list)  # walkway points of an arrival, break or departure walk
    still_until: float = -1.0
    skip_checkin: bool = False
    next_checkin: float = 0.0
    last_buzz: str | None = None
    events: list[str] = field(default_factory=list)  # fall / sos / cancel / checkin, reported by the badge at once

    @property
    def on_site(self) -> bool:
        return self.status not in ("off_site", "init")


class PedGraph:
    """The layout's pedestrian graph (nodes and lanes with no vehicle kinds): walkways and marked crossings."""

    def __init__(self, layout: dict[str, Any]) -> None:
        self.nodes = {n["id"]: (float(n["x"]), float(n["z"])) for n in layout["nodes"] if not n.get("kinds")}
        self.adj: dict[str, list[tuple[str, float]]] = {i: [] for i in self.nodes}
        for ln in layout["lanes"]:
            if ln.get("kinds") or ln["a"] not in self.nodes or ln["b"] not in self.nodes:
                continue
            d = math.dist(self.nodes[ln["a"]], self.nodes[ln["b"]])
            self.adj[ln["a"]].append((ln["b"], d))
            self.adj[ln["b"]].append((ln["a"], d))

    def nearest(self, x: float, z: float) -> str:
        return min(self.nodes, key=lambda i: (self.nodes[i][0] - x) ** 2 + (self.nodes[i][1] - z) ** 2)

    def route(self, a: tuple[float, float], b: tuple[float, float]) -> list[tuple[float, float]]:
        """Walkway points from near a to near b (ending exactly at b)."""
        s, g = self.nearest(*a), self.nearest(*b)
        dist, prev = {s: 0.0}, {}
        heap = [(0.0, s)]
        while heap:
            d, n = heapq.heappop(heap)
            if n == g:
                break
            if d > dist[n]:
                continue
            for m, w in self.adj[n]:
                if d + w < dist.get(m, math.inf):
                    dist[m], prev[m] = d + w, n
                    heapq.heappush(heap, (d + w, m))
        if g not in dist:
            return [b]
        seq = [g]
        while seq[-1] != s:
            seq.append(prev[seq[-1]])
        return [self.nodes[n] for n in reversed(seq)] + [b]


class People(Model):
    key = "people"
    title = "People (shift roster, rounds, breaks, badges)"
    equations = (
        "Roster: a worker is on site from a few minutes before their shift until they have walked out after it; "
        "off shift their badge is in the gate rack, switched off.",
        "Walking: position moves towards the next point at walking speed (Δs = v × dt) along walkways and marked crossings; "
        "along a forklift aisle the worker keeps to the walkway beside it.",
        "Rounds: the worker loops their round, pausing at work stands for a drawn time.",
        "Meal break: the worker walks to the canteen and back; tea breaks are taken at the work area.",
        "Evacuation and work orders: walk the given walkway path to the target (evacuation at a brisker pace).",
        "Falls and SOS on their own: Bernoulli per step with a documented, very low rate per worked hour.",
        "Lone-worker check-in: the badge's double press every check-in period, unless the worker forgets (demo).",
    )
    writes = ("people_in_zone",)
    params_prefix = ("people",)

    def __init__(self, cfg: dict[str, Any], layout: dict[str, Any]) -> None:
        self.cfg = cfg
        self.walkers: dict[str, Walker] = {}
        self._layout_nodes = {n["id"]: n for n in layout["nodes"]}
        self.ped = PedGraph(layout)
        self._window: tuple[float, tuple[str, str, str | None, float]] | None = None

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
            wk = Walker(d["id"], w["id"] if w else d["id"], w["role"] if w else "", (w or {}).get("shift"), routes,
                        p.f("people.walk_speed_mps"), float(d.get("sim", {}).get("checkin_s", 0)))
            pts = routes.get("default") or [("", float(d["x"]), float(d["z"]), False)]
            _, wk.x, wk.z, _ = pts[0]
            wk.leg = 1 % len(pts)
            wk.next_checkin = wk.checkin_s
            self.walkers[d["id"]] = wk

    # ------------------------------------------------------------------ roster

    def _gate(self) -> tuple[float, float]:
        n = self._layout_nodes[str(self.core.p.v("people.gate_node"))]
        return float(n["x"]), float(n["z"])

    def _shift_window(self) -> tuple[str, str, str | None, float]:
        """(current shift, phase, next shift, minutes until the next shift starts); worked out once per step."""
        if self._window is not None and self._window[0] == self.core.t:
            return self._window[1]
        p = self.core.p
        h = self.core.hour_of_day()
        cur, phase = shift_phase(p, h)
        nxt, until = None, math.inf
        for sh in p.v("production.shifts.calendar"):
            m = ((float(sh["start_h"]) - h) % 24) * 60
            if 0 < m < until:
                nxt, until = str(sh["name"]), m
        self._window = (self.core.t, (cur, phase, nxt, until))
        return cur, phase, nxt, until

    def _on_duty(self, w: Walker) -> bool:
        if w.shift is None:
            return True
        cur, phase, nxt, until = self._shift_window()
        if cur == w.shift and phase != "closed":
            return True
        return nxt == w.shift and until <= self.core.p.f("people.arrive_before_min")

    def _meal_break(self) -> bool:
        p = self.core.p
        h = self.core.hour_of_day()
        if self._shift_window()[1] != "break":
            return False
        for sh in p.v("production.shifts.calendar"):
            for a, b in sh["breaks"]:
                if (h - a) % 24 < (b - a) % 24 and ((b - a) % 24) * 60 >= p.f("people.meal_break_min"):
                    return True
        return False

    def _route_start(self, w: Walker) -> tuple[float, float]:
        pts = w.routes.get(w.route_name) or w.routes.get("default")
        if not pts:
            return w.x, w.z
        near = min(range(len(pts)), key=lambda i: math.hypot(pts[i][1] - w.x, pts[i][2] - w.z))
        w.leg = (near + 1) % len(pts)
        return pts[near][1], pts[near][2]

    def _attendance(self, w: Walker) -> None:
        core = self.core
        duty = self._on_duty(w)
        if w.status == "off_site" and duty:
            w.x, w.z = self._gate()
            pts = w.routes.get("default")
            target = (pts[0][1], pts[0][2]) if pts else (w.x, w.z)
            w.walk, w.status, w.leg = self.ped.route((w.x, w.z), target), "arriving", 1 % max(1, len(pts or [None]))
            core.record(f"{w.worker} arrives for shift {w.shift}", "shift roster")
        elif w.status in ("working", "break") and not duty and w.goto is None:
            w.walk, w.status = self.ped.route((w.x, w.z), self._gate()), "leaving"
            core.record(f"{w.worker} leaves after shift {w.shift}", "shift roster")
        elif w.status == "working" and self._meal_break() and w.role not in self.core.p.v("people.stay_in_breaks_roles") and w.goto is None:
            canteen = self._layout_nodes[str(self.core.p.v("people.canteen_node"))]
            w.walk, w.status = self.ped.route((w.x, w.z), (float(canteen["x"]), float(canteen["z"]))), "break"
        elif w.status == "break" and not self._meal_break() and duty:
            w.walk, w.status = self.ped.route((w.x, w.z), self._route_start(w)), "working"

    # ------------------------------------------------------------------ commands

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
            w.walk = []
        elif action == "buzz":
            w.last_buzz = str(data.get("route", "alert"))
        elif action == "fall":
            w.events.append("fall")  # free fall, impact, then the worker lies still until they cancel or are helped
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

    # ------------------------------------------------------------------ step

    def _towards(self, w: Walker, gx: float, gz: float, stepm: float) -> bool:
        """Move towards (gx, gz); True when there."""
        dx, dz = gx - w.x, gz - w.z
        dist = math.hypot(dx, dz)
        if dist <= stepm:
            w.x, w.z = gx, gz
            return True
        w.x += dx / dist * stepm
        w.z += dz / dist * stepm
        return False

    def step(self, dt: float) -> None:
        core, p, t = self.core, self.core.p, self.core.t
        offset = p.f("people.walkway_offset_m")
        fall_p = p.f("people.fall_rate_per_h") * dt / 3600
        sos_p = p.f("people.sos_rate_per_h") * dt / 3600
        for w in self.walkers.values():
            if w.status == "init":
                # First step: whoever is on duty now is already at work; the others are off site.
                if self._on_duty(w):
                    w.status = "working"
                else:
                    w.status, (w.x, w.z) = "off_site", self._gate()
            if w.goto is None and t >= w.still_until:
                self._attendance(w)
            if not w.on_site:
                continue
            if t >= w.still_until and w.status == "working":
                if core.rng.chance(f"{w.badge}.fall", fall_p):
                    w.events.append("fall")
                    w.still_until = t + p.f("people.fall_lie_still_s")
                    core.record(f"{w.worker} fell", "rare slip/trip (documented rate per worked hour)")
                elif core.rng.chance(f"{w.badge}.sos", sos_p):
                    w.events.append("sos")
                    core.record(f"{w.worker} pressed SOS", "rare SOS (documented rate per worked hour)")
            if t < w.still_until:
                continue
            if w.goto is not None:
                gx, gz = w.path[0] if w.path else w.goto
                if self._towards(w, gx, gz, w.speed * p.f("people.evacuation_pace_factor") * dt) and w.path:
                    w.path.pop(0)
                continue
            if w.walk:
                if self._towards(w, *w.walk[0], w.speed * dt):
                    w.walk.pop(0)
                    if not w.walk:
                        if w.status == "leaving":
                            w.status = "off_site"
                        elif w.status == "arriving":
                            w.status = "working"
                continue
            if w.status == "break":
                continue  # at the canteen
            pts = w.routes.get(w.route_name)
            if pts and len(pts) > 1 and t >= w.pause_until:
                name, tx, tz, lane = pts[w.leg]
                _, px, pz, prev_lane = pts[w.leg - 1]
                if lane and prev_lane:
                    lx, lz = tx - px, tz - pz
                    ll = math.hypot(lx, lz) or 1.0
                    tx, tz = tx - lz / ll * offset, tz + lx / ll * offset
                if self._towards(w, tx, tz, w.speed * dt):
                    if name.startswith("WALK_") and name != "WALK_STAFF_DOOR":
                        w.pause_until = t + core.rng.draw("people.work_stand_pause_s", f"{w.badge}.pause")
                    if w.next_route:
                        w.route_name, w.next_route = w.next_route, None
                        pts = w.routes[w.route_name]
                        near = min(range(len(pts)), key=lambda i: math.hypot(pts[i][1] - w.x, pts[i][2] - w.z))  # noqa: B023
                        w.leg = (near + 1) % len(pts)
                    else:
                        w.leg = (w.leg + 1) % len(pts)
            if w.checkin_s and not w.skip_checkin and t >= w.next_checkin:
                w.events.append("checkin")
                w.next_checkin = t + w.checkin_s
