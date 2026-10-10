"""Worker safety from badge positions (S3).

- Proximity: a badge within `warn_m` of a MOVING forklift (speed above `moving_mps`) raises a
  "pedestrian near forklift" warning, below `crit_m` it is critical. A parked forklift never
  triggers it. It clears once the distance is above warn_m + clear_margin_m or the forklift
  stops (hysteresis, so a worker walking along a lane doesn't make it flicker).
- Restricted zones: a zone with `restricted_roles` raises an alert when a badge whose worker
  has another role enters it; it clears when they leave.
- Privacy: workers are identified by id and role. Names are not sent to browsers at all (the
  demo has no sign-in, so nobody is an authorised user); nothing is stored beyond the event log.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Near:
    forklift: str
    distance_m: float
    level: str  # "warning" | "critical"


@dataclass
class WorkerState:
    id: str
    role: str
    badge: str
    x: float | None = None
    z: float | None = None
    zone_id: str | None = None
    fresh: bool = False
    data_ms: int | None = None
    moving: bool = False
    near: Near | None = None
    restricted: str | None = None  # zone id the worker shouldn't be in
    heading: float = 0.0


@dataclass
class Today:
    warnings: int = 0
    criticals: int = 0
    restricted: int = 0
    closest_m: float | None = None
    closest: dict[str, Any] | None = None


@dataclass
class Safety:
    cfg: dict[str, Any]
    workers: dict[str, WorkerState] = field(default_factory=dict)
    today: Today = field(default_factory=Today)

    @classmethod
    def build(cls, cfg: dict[str, Any], workers: list[dict[str, Any]]) -> Safety:
        return cls(cfg, {w["id"]: WorkerState(w["id"], w["role"], w["badge"]) for w in workers})

    def set_position(self, wid: str, x: float, z: float, zone: dict[str, Any] | None, now: int) -> None:
        w = self.workers[wid]
        if w.x is not None and w.z is not None:
            dx, dz = x - w.x, z - w.z
            w.moving = math.hypot(dx, dz) > 0.3
            if w.moving:
                w.heading = math.atan2(dz, dx)
        w.x, w.z, w.data_ms = x, z, now
        w.zone_id = zone["id"] if zone else None

    def evaluate(self, now: int, forklifts: list[tuple[str, float, float, float]], fresh: dict[str, bool],
                 zones: dict[str, dict[str, Any]]) -> list[tuple[str, str, str]]:
        """forklifts: (id, x, z, speed). Updates each worker's near/restricted state and today's counters.
        Alerts (and their events) come from the rules engine (backend/rules/safety.yaml); the returned
        list is always empty and kept for callers that log observations."""
        warn, crit = float(self.cfg["warn_m"]), float(self.cfg["crit_m"])
        clear = warn + float(self.cfg["clear_margin_m"])
        moving_mps = float(self.cfg["moving_mps"])
        ev: list[tuple[str, str, str]] = []
        for w in self.workers.values():
            w.fresh = fresh.get(w.badge, False)
            if not w.fresh or w.x is None or w.z is None:
                if w.near:
                    w.near = None  # no current position: we can't claim anything either way
                w.restricted = None
                continue
            # --- proximity to moving forklifts
            best: tuple[float, str] | None = None
            for fid, fx, fz, speed in forklifts:
                if speed < moving_mps:
                    continue
                dist = math.hypot(fx - w.x, fz - w.z)
                if best is None or dist < best[0]:
                    best = (dist, fid)
            if best is not None and (best[0] < warn or (w.near is not None and best[0] < clear)):
                dist, fid = best
                level = "critical" if dist < crit else "warning"
                if w.near is None or (w.near.level == "warning" and level == "critical"):
                    if level == "critical":
                        self.today.criticals += 1
                    else:
                        self.today.warnings += 1
                elif w.near.level == "critical" and level == "warning":
                    level = "critical" if dist < crit + 0.3 else "warning"  # small hysteresis on the way down
                w.near = Near(fid, round(dist, 2), level)
                if self.today.closest_m is None or dist < self.today.closest_m:
                    self.today.closest_m = round(dist, 2)
                    self.today.closest = {"worker": w.id, "forklift": fid, "at_ms": now}
            elif w.near is not None:
                w.near = None
            # --- restricted zones
            zn = zones.get(w.zone_id or "")
            allowed = zn.get("restricted_roles") if zn else None
            if allowed is not None and w.role not in allowed:
                if w.restricted != zn["id"]:  # type: ignore[index]
                    w.restricted = zn["id"]  # type: ignore[index]
                    self.today.restricted += 1
            elif w.restricted is not None:
                w.restricted = None
        return ev

    def wire(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        workers = []
        for w in self.workers.values():
            if w.fresh and w.zone_id:
                counts[w.zone_id] = counts.get(w.zone_id, 0) + 1
            workers.append({
                "id": w.id, "role": w.role, "badge_id": w.badge, "zone_id": w.zone_id if w.fresh else None,
                "x": w.x, "z": w.z, "fresh": w.fresh, "data_ms": w.data_ms,
                "near": None if w.near is None else {"forklift": w.near.forklift, "distance_m": w.near.distance_m,
                                                     "level": w.near.level},
                "restricted_zone": w.restricted,
            })
        t = self.today
        return {"workers": workers, "zone_counts": counts,
                "today": {"warnings": t.warnings, "criticals": t.criticals, "restricted": t.restricted,
                          "closest_m": t.closest_m, "closest": t.closest},
                "config": {"warn_m": self.cfg["warn_m"], "crit_m": self.cfg["crit_m"]}}
