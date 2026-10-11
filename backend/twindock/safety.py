"""Worker safety from badges (S3, extended in FACTORY_PROMPTS.md K3).

Every input arrives through the same few calls, whatever the badge is: a simulated badge
(tools/site_sim.py) or a real one would both feed `set_position`, `on_badge` and `set_helmet`.

- Proximity: a badge within `warn_m` of a MOVING forklift raises a warning, below `crit_m` it is
  critical. In the forklift's direction of travel the radius grows (`ahead_factor`), and much more
  when the forklift is reversing (`reverse_factor`): the driver can't see behind. Hysteresis as before.
- Fall / man-down: a `fall` message from the badge (free fall then impact), or no movement for
  `man_down_still_s`, starts a pre-alert. The worker can cancel it on the badge within `fall_cancel_s`;
  otherwise it becomes a critical "man down" with location.
- SOS: a long press raises a critical alert with location and the nearest first-aider.
- Restricted zones (role-based, S3) and zone time limits (`time_limit_min` on hot or gas-risk zones).
- Gas: a gas detector in alarm puts every badge in its zone and in adjacent zones into "evacuate".
  Heat: the heat index per zone (from env nodes) drives rest-break buzzes; no worker is named.
- Lone worker: alone in a zone marked `lone_worker`, a worker must check in every `checkin_min`;
  overdue is a warning, `lone_escalate_min` later critical.
- PPE: zones listing "helmet" need the worker's helmet clip to report worn. Missing: a buzz on the
  badge only. It is never stored, counted per worker or shown with the worker's id: a reminder, not a record.
- Evacuation: started from the monitoring page (or a gas alarm). Muster points count arrivals; the
  headcount lists who is unaccounted for with their last known zone.
- Shift: a shift starts at the first on-site position (check-in) and ends after `checkout_after_min`
  without data. Hours and break reminders are only served to the worker and the supervisor
  (GET /api/safety/me/<id>, /api/safety/shift), never broadcast.
- Privacy by design: positions outside every site's bounds are dropped (no off-site tracking), and
  off-shift nobody is tracked. A worker's position and zone go to screens only while that worker has
  an active safety condition or an evacuation is running; otherwise screens get zone counts only.
  Incident history is kept for `retention_days`. Workers are identified by id and role, never by name.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

DAY_MS = 86_400_000


@dataclass
class Near:
    forklift: str
    distance_m: float
    level: str  # "warning" | "critical"
    reversing: bool = False


@dataclass
class PreAlert:
    kind: str  # "fall" | "no_motion"
    since_ms: int
    deadline_ms: int


@dataclass
class WorkerState:
    id: str
    role: str
    badge: str
    first_aider: bool = False
    x: float | None = None
    z: float | None = None
    zone_id: str | None = None
    fresh: bool = False
    data_ms: int | None = None
    moving: bool = False
    near: Near | None = None
    restricted: str | None = None  # zone id the worker shouldn't be in
    heading: float = 0.0
    # K3
    still_since_ms: int | None = None
    prealert: PreAlert | None = None
    man_down: str | None = None  # "fall" | "no_motion" once escalated
    man_down_ms: int | None = None
    sos_ms: int | None = None
    zone_since_ms: int | None = None
    zone_overtime_min: float | None = None
    evacuate: str | None = None  # reason, while the worker must leave (gas nearby, or an evacuation)
    lone_checkin_ms: int | None = None
    lone_level: str | None = None
    helmet_worn: bool | None = None  # None: no helmet clip data
    ppe_missing: str | None = None
    shift_start_ms: int | None = None
    last_break_ms: int | None = None
    break_zone_since_ms: int | None = None
    mustered: str | None = None  # muster point id during an evacuation
    last_zone_id: str | None = None

    @property
    def sos(self) -> bool:
        return self.sos_ms is not None


@dataclass
class Today:
    warnings: int = 0
    criticals: int = 0
    restricted: int = 0
    closest_m: float | None = None
    closest: dict[str, Any] | None = None
    falls: int = 0
    falls_cancelled: int = 0
    sos: int = 0
    last_fall_ms: int | None = None
    last_sos_ms: int | None = None


@dataclass
class Evacuation:
    started_ms: int
    reason: str
    by: str
    on_site: list[str]  # workers on shift when it started: the headcount
    ended_ms: int | None = None


def heat_index_c(t_c: float, rh: float) -> float:
    """NOAA heat index (Rothfusz regression, with the simple formula below 80 °F), in °C."""
    t = t_c * 9 / 5 + 32
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (simple + t) / 2 < 80:
        hi = simple
    else:
        hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh - 0.00683783 * t * t
              - 0.05481717 * rh * rh + 0.00122874 * t * t * rh + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t - 95)) / 17)
        elif rh > 85 and 80 <= t <= 87:
            hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return (hi - 32) * 5 / 9


def _bbox(poly: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in poly]
    zs = [p[1] for p in poly]
    return min(xs), min(zs), max(xs), max(zs)


def zones_adjacent(a: dict[str, Any], b: dict[str, Any], gap_m: float) -> bool:
    """Two zones are adjacent when their bounding boxes are within gap_m of each other (they touch or face
    each other across an aisle). Good enough for evacuation advice; exact geometry is not needed."""
    ax0, az0, ax1, az1 = _bbox(a["polygon"])
    bx0, bz0, bx1, bz1 = _bbox(b["polygon"])
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    dz = max(0.0, max(az0, bz0) - min(az1, bz1))
    return math.hypot(dx, dz) <= gap_m


@dataclass
class Safety:
    cfg: dict[str, Any]
    workers: dict[str, WorkerState] = field(default_factory=dict)
    today: Today = field(default_factory=Today)
    privacy: dict[str, Any] = field(default_factory=dict)
    sites: list[dict[str, Any]] = field(default_factory=list)
    muster_points: list[dict[str, Any]] = field(default_factory=list)
    evacuation: Evacuation | None = None
    last_evacuation: Evacuation | None = None
    history: list[dict[str, Any]] = field(default_factory=list)  # per-worker incidents, kept retention_days
    gas_zones: list[str] = field(default_factory=list)  # zones with a gas alarm right now
    heat_zones: dict[str, float] = field(default_factory=dict)  # zone -> heat index at or above the threshold
    ppe_reminders: int = 0
    hazard_zone_ids: frozenset[str] = field(default_factory=frozenset)
    badge_actions: list[tuple[str, str, dict[str, Any]]] = field(default_factory=list)  # (badge, action, extra) for the engine
    _fork_last: dict[str, tuple[float, float]] = field(default_factory=dict)
    _fork_motion: dict[str, tuple[float, float]] = field(default_factory=dict)
    _buzzed: dict[tuple[str, str], int] = field(default_factory=dict)

    @classmethod
    def build(cls, cfg: dict[str, Any], workers: list[dict[str, Any]], privacy: dict[str, Any] | None = None,
              sites: list[dict[str, Any]] | None = None, muster_points: list[dict[str, Any]] | None = None) -> Safety:
        s = cls(cfg, {w["id"]: WorkerState(w["id"], w["role"], w["badge"], bool(w.get("first_aider"))) for w in workers},
                privacy=privacy or {}, sites=sites or [], muster_points=muster_points or [])
        s.hazard_zone_ids = frozenset(z["id"] for site in s.sites for z in site.get("zones", []) if z.get("hazard") == "high")
        return s

    def c(self, key: str, default: float) -> float:
        return float(self.cfg.get(key, default))

    # ------------------------------------------------------------------ inputs

    def on_site(self, x: float, z: float) -> bool:
        if not self.sites:
            return True
        return any(s["bounds"]["x"][0] <= x <= s["bounds"]["x"][1] and s["bounds"]["z"][0] <= z <= s["bounds"]["z"][1] for s in self.sites)

    def set_position(self, wid: str, x: float, z: float, zone: dict[str, Any] | None, now: int) -> None:
        w = self.workers[wid]
        if not self.on_site(x, z):
            # Off site: we don't track it. Forget the last position rather than keep a stale one.
            w.x = w.z = None
            w.zone_id = None
            return
        if w.shift_start_ms is None:
            w.shift_start_ms = now  # check-in: first position on site
            w.last_break_ms = now
            w.still_since_ms = now
        if w.data_ms is not None and now - w.data_ms > 10_000:
            w.still_since_ms = now  # the badge was silent for a while: "not moving" is counted from its first new position, not from before
        if w.x is not None and w.z is not None:
            dx, dz = x - w.x, z - w.z
            w.moving = math.hypot(dx, dz) > 0.3
            if w.moving:
                w.heading = math.atan2(dz, dx)
                w.still_since_ms = now
        w.x, w.z, w.data_ms = x, z, now
        zid = zone["id"] if zone else None
        if zid != w.zone_id:
            w.zone_since_ms = now
        w.zone_id = zid
        if zid:
            w.last_zone_id = zid

    def on_badge(self, wid: str, channel: str, value: Any, now: int) -> None:
        """A button or IMU event from the worker's badge."""
        w = self.workers[wid]
        if channel == "fall" and value and w.prealert is None and w.man_down is None:
            self._prealert(w, "fall", now)
        elif channel == "cancel" and value and w.prealert is not None:
            self._record(w, f"{'Fall' if w.prealert.kind == 'fall' else 'No-movement'} pre-alert cancelled by the worker", now)
            if w.prealert.kind == "fall":
                self.today.falls_cancelled += 1
            w.prealert = None
            w.still_since_ms = now  # pressing the button proves they can move
        elif channel == "sos" and value and w.sos_ms is None:
            w.sos_ms = now
            self.today.sos += 1
            self.today.last_sos_ms = now
            self._record(w, "SOS", now)
        elif channel == "checkin" and value:
            w.lone_checkin_ms = now
            w.lone_level = None

    def set_helmet(self, wid: str, worn: bool | None) -> None:
        self.workers[wid].helmet_worn = worn

    def clear_incident(self, wid: str, now: int) -> str | None:
        """Someone reached the worker: SOS and man-down end (from the monitoring page). Returns why it failed."""
        w = self.workers.get(wid)
        if w is None:
            return f"No worker {wid}"
        if not w.sos and w.man_down is None and w.prealert is None:
            return f"{wid} has no open SOS or man-down"
        w.sos_ms, w.man_down, w.man_down_ms, w.prealert = None, None, None, None
        w.still_since_ms = now
        self._record(w, "Incident closed on the monitoring page", now)
        return None

    # ------------------------------------------------------------------ evacuation

    def start_evacuation(self, now: int, reason: str, by: str) -> str | None:
        if self.evacuation is not None:
            return "An evacuation is already running"
        on_site = [w.id for w in self.workers.values() if w.shift_start_ms is not None]
        self.evacuation = Evacuation(now, reason, by, on_site)
        for w in self.workers.values():
            w.mustered = None
            self._buzz(w, "evacuate", now, force=True)
        return None

    def end_evacuation(self, now: int) -> str | None:
        if self.evacuation is None:
            return "No evacuation is running"
        self.evacuation.ended_ms = now
        self.last_evacuation, self.evacuation = self.evacuation, None
        for w in self.workers.values():
            w.mustered = None
            self.badge_actions.append((w.badge, "resume", {}))
        return None

    def headcount(self) -> dict[str, Any] | None:
        e = self.evacuation
        if e is None:
            return None
        accounted = [wid for wid in e.on_site if self.workers[wid].mustered]
        missing = [self.workers[wid] for wid in e.on_site if not self.workers[wid].mustered]
        return {"active": True, "started_ms": e.started_ms, "reason": e.reason, "by": e.by,
                "on_site": len(e.on_site), "accounted": len(accounted),
                "by_muster": {m["id"]: sum(1 for wid in accounted if self.workers[wid].mustered == m["id"]) for m in self.muster_points},
                "unaccounted": [{"id": w.id, "role": w.role, "last_zone_id": w.last_zone_id, "last_seen_ms": w.data_ms} for w in missing]}

    # ------------------------------------------------------------------ evaluation

    def evaluate(self, now: int, forklifts: list[tuple[Any, ...]], fresh: dict[str, bool], zones: dict[str, dict[str, Any]],
                 gas_alarm_zones: set[str] | None = None, heat_by_zone: dict[str, float] | None = None) -> list[tuple[str, str, str]]:
        """forklifts: (id, x, z, speed[, heading]). Updates every worker's state and today's counters.
        Alerts come from the rules engine (backend/rules/safety.yaml); badge buzzes are queued in
        `badge_actions`. The returned list is kept empty for callers that log observations."""
        self._forklift_motion(forklifts)
        gas = set(gas_alarm_zones or ())
        self.gas_zones = sorted(gas)
        hot = self.c("heat_index_c", 32.0)
        self.heat_zones = {z: round(v, 1) for z, v in (heat_by_zone or {}).items() if v >= hot}
        gap = self.c("adjacent_m", 6.0)
        evac_zones = {zid for zid in zones if zid in gas or any(zones_adjacent(zones[zid], zones[g], gap) for g in gas if g in zones)}
        self.ppe_reminders = 0
        for w in self.workers.values():
            w.fresh = fresh.get(w.badge, False)  # all first: rules below look at the other workers too
        for w in self.workers.values():
            self._shift(w, now, zones)
            if not w.fresh or w.x is None or w.z is None:
                w.near = None  # no current position: we can't claim anything either way
                w.restricted = None
                w.zone_overtime_min = None
                w.lone_level = None
                w.ppe_missing = None
                w.evacuate = (f"evacuation: {self.evacuation.reason}"
                              if self.evacuation and not w.mustered and w.id in self.evacuation.on_site else None)
                continue
            self._proximity(w, now, forklifts)
            self._restricted(w, zones)
            self._man_down(w, now)
            self._zone_time(w, now, zones)
            self._lone(w, now, zones)
            self._ppe(w, now, zones)
            self._muster(w)
            if self.evacuation is not None and not w.mustered and w.id in self.evacuation.on_site:
                w.evacuate = f"evacuation: {self.evacuation.reason}"
            elif self.evacuation is None and w.zone_id in evac_zones:
                w.evacuate = "gas alarm nearby"
                self._buzz(w, "evacuate", now)
            else:
                w.evacuate = None
            if w.zone_id in self.heat_zones:
                self._buzz(w, "rest", now, every_ms=int(self.c("heat_buzz_min", 20) * 60_000))
        self._prune(now)
        return []

    def _forklift_motion(self, forklifts: list[tuple[Any, ...]]) -> None:
        for f in forklifts:
            fid, fx, fz = f[0], float(f[1]), float(f[2])
            last = self._fork_last.get(fid)
            if last is not None and math.hypot(fx - last[0], fz - last[1]) > 0.02:
                self._fork_motion[fid] = (fx - last[0], fz - last[1])
            self._fork_last[fid] = (fx, fz)

    def _proximity(self, w: WorkerState, now: int, forklifts: list[tuple[Any, ...]]) -> None:
        warn, crit = self.c("warn_m", 3.0), self.c("crit_m", 1.5)
        moving_mps = self.c("moving_mps", 0.2)
        assert w.x is not None and w.z is not None
        best: tuple[float, float, str, bool] | None = None  # (distance / radius scale, distance, forklift, reversing)
        for f in forklifts:
            fid, fx, fz, speed = f[0], float(f[1]), float(f[2]), float(f[3])
            heading = float(f[4]) if len(f) > 4 else None
            if speed < moving_mps:
                continue
            dist = math.hypot(fx - w.x, fz - w.z)
            scale, reversing = 1.0, False
            mv = self._fork_motion.get(fid)
            if mv is not None and dist > 0:
                ml = math.hypot(*mv)
                ahead = ((w.x - fx) * mv[0] + (w.z - fz) * mv[1]) / (dist * ml)  # cos of the angle to the direction of travel
                if heading is not None:
                    reversing = mv[0] * math.cos(heading) + mv[1] * math.sin(heading) < 0
                if ahead > 0.5:  # within 60° of where the forklift is going
                    scale = self.c("reverse_factor", 2.0) if reversing else self.c("ahead_factor", 1.3)
            eff = dist / scale  # the scaled distance is compared with the normal thresholds
            if best is None or eff < best[0]:
                best = (eff, dist, fid, reversing)
        clear = warn + self.c("clear_margin_m", 0.5)
        if best is not None and (best[0] < warn or (w.near is not None and best[0] < clear)):
            eff, dist, fid, reversing = best
            level = "critical" if eff < crit else "warning"
            if w.near is None or (w.near.level == "warning" and level == "critical"):
                if level == "critical":
                    self.today.criticals += 1
                else:
                    self.today.warnings += 1
                self._buzz(w, "near", now, force=True)
            elif w.near.level == "critical" and level == "warning":
                level = "critical" if eff < crit + 0.3 else "warning"  # small hysteresis on the way down
            w.near = Near(fid, round(dist, 2), level, reversing)
            if self.today.closest_m is None or dist < self.today.closest_m:
                self.today.closest_m = round(dist, 2)
                self.today.closest = {"worker": w.id, "forklift": fid, "at_ms": now}
        elif w.near is not None:
            w.near = None

    def _restricted(self, w: WorkerState, zones: dict[str, dict[str, Any]]) -> None:
        zn = zones.get(w.zone_id or "")
        allowed = zn.get("restricted_roles") if zn else None
        if zn is not None and allowed is not None and w.role not in allowed:
            if w.restricted != zn["id"]:
                w.restricted = zn["id"]
                self.today.restricted += 1
        elif w.restricted is not None:
            w.restricted = None

    def _man_down(self, w: WorkerState, now: int) -> None:
        if w.prealert is not None and now >= w.prealert.deadline_ms:
            w.man_down, w.man_down_ms = w.prealert.kind, now
            self._record(w, "Man down (fall, not cancelled)" if w.prealert.kind == "fall" else "Man down (no movement)", now)
            w.prealert = None
        elif (w.prealert is None and w.man_down is None and w.still_since_ms is not None
              and now - w.still_since_ms >= self.c("man_down_still_s", 90) * 1000):
            self._prealert(w, "no_motion", now)
        if w.man_down == "no_motion" and w.moving:
            w.man_down, w.man_down_ms = None, None  # they got up and walked: nothing to rescue
            self._record(w, "Moving again after a no-movement alert", now)

    def _prealert(self, w: WorkerState, kind: str, now: int) -> None:
        w.prealert = PreAlert(kind, now, now + int(self.c("fall_cancel_s", 30) * 1000))
        if kind == "fall":
            self.today.falls += 1
            self.today.last_fall_ms = now
        self._record(w, "Possible fall: pre-alert on the badge" if kind == "fall" else "No movement: pre-alert on the badge", now)
        self._buzz(w, "prealert", now, force=True)

    def _zone_time(self, w: WorkerState, now: int, zones: dict[str, dict[str, Any]]) -> None:
        zn = zones.get(w.zone_id or "")
        limit = zn.get("time_limit_min") if zn else None
        if limit is not None and w.zone_since_ms is not None:
            over = (now - w.zone_since_ms) / 60_000 - float(limit)
            w.zone_overtime_min = round(over, 1) if over > 0 else None
        else:
            w.zone_overtime_min = None

    def _lone(self, w: WorkerState, now: int, zones: dict[str, dict[str, Any]]) -> None:
        zn = zones.get(w.zone_id or "")
        if not zn or not zn.get("lone_worker"):
            w.lone_level, w.lone_checkin_ms = None, None
            return
        others = any(o is not w and o.fresh and o.zone_id == w.zone_id for o in self.workers.values())
        if others:
            w.lone_level = None
            w.lone_checkin_ms = now  # not alone: the clock restarts when they are alone again
            return
        if w.lone_checkin_ms is None:
            w.lone_checkin_ms = w.zone_since_ms or now  # entering counts as the first check-in
        every = float(zn.get("checkin_min", self.c("lone_checkin_min", 10))) * 60_000
        late = now - w.lone_checkin_ms - every
        if late >= self.c("lone_escalate_min", 2) * 60_000:
            w.lone_level = "critical"
        elif late >= 0:
            if w.lone_level is None:
                self._buzz(w, "checkin", now, force=True)
            w.lone_level = "warning"
        else:
            w.lone_level = None

    def _ppe(self, w: WorkerState, now: int, zones: dict[str, dict[str, Any]]) -> None:
        zn = zones.get(w.zone_id or "")
        need = (zn or {}).get("ppe") or []
        w.ppe_missing = "helmet" if "helmet" in need and w.helmet_worn is not True else None
        if w.ppe_missing:
            self.ppe_reminders += 1
            self._buzz(w, "ppe", now, every_ms=10 * 60_000)  # a reminder at most every 10 min; nothing is recorded

    def _muster(self, w: WorkerState) -> None:
        if self.evacuation is None or w.mustered:
            return
        for m in self.muster_points:
            if math.hypot((w.x or 0) - m["x"], (w.z or 0) - m["z"]) <= float(m.get("radius_m", 6.0)):
                w.mustered = m["id"]
                return

    def _shift(self, w: WorkerState, now: int, zones: dict[str, dict[str, Any]]) -> None:
        if w.shift_start_ms is None:
            return
        if w.data_ms is not None and now - w.data_ms > self.c("checkout_after_min", 30) * 60_000:
            # Checked out: off shift we track nothing.
            w.shift_start_ms = w.last_break_ms = w.break_zone_since_ms = None
            w.x = w.z = None
            w.zone_id = None
            return
        kind = zones.get(w.zone_id or "", {}).get("kind")
        if w.fresh and kind in set(self.cfg.get("break_zone_kinds", ["office", "canteen"])):
            w.break_zone_since_ms = w.break_zone_since_ms or now
            if now - w.break_zone_since_ms >= self.c("break_min", 15) * 60_000:
                w.last_break_ms = now
        else:
            w.break_zone_since_ms = None

    # ------------------------------------------------------------------ helpers

    def _buzz(self, w: WorkerState, why: str, now: int, force: bool = False, every_ms: int = 60_000) -> None:
        key = (w.id, why)
        if force or now - self._buzzed.get(key, -10**12) >= every_ms:
            self._buzzed[key] = now
            self.badge_actions.append((w.badge, "buzz", {"route": why}))

    def _record(self, w: WorkerState, what: str, now: int) -> None:
        self.history.append({"worker": w.id, "at_ms": now, "what": what, "zone_id": w.zone_id})

    def _prune(self, now: int) -> None:
        keep = float(self.privacy.get("retention_days", 30)) * DAY_MS
        if self.history and now - self.history[0]["at_ms"] > keep:
            self.history = [h for h in self.history if now - h["at_ms"] <= keep]

    def take_badge_actions(self) -> list[tuple[str, str, dict[str, Any]]]:
        out, self.badge_actions = self.badge_actions, []
        return out

    def active(self, w: WorkerState) -> bool:
        """A worker with an open safety condition: the only time their location may be shown."""
        return bool(w.near or w.restricted or w.prealert or w.man_down or w.sos or w.zone_overtime_min
                    or w.lone_level or w.evacuate)

    def location_visible(self, w: WorkerState) -> bool:
        if self.privacy.get("location", "alerts_only") == "always":
            return True
        return self.active(w) or self.evacuation is not None

    def nearest_first_aider(self, w: WorkerState) -> tuple[str, float] | None:
        if w.x is None or w.z is None:
            return None
        best: tuple[str, float] | None = None
        for o in self.workers.values():
            if o is w or not o.first_aider or not o.fresh or o.x is None or o.z is None:
                continue
            d = math.hypot(o.x - w.x, o.z - w.z)
            if best is None or d < best[1]:
                best = (o.id, round(d, 1))
        return best

    def breaks_due(self, now: int) -> list[str]:
        after = self.c("break_after_h", 4) * 3_600_000
        return [w.id for w in self.workers.values()
                if w.shift_start_ms is not None and w.last_break_ms is not None and now - w.last_break_ms >= after]

    def personal(self, wid: str, now: int) -> dict[str, Any] | None:
        """A worker's own data (GET /api/safety/me/<id>): shift, breaks and their own incidents."""
        w = self.workers.get(wid)
        if w is None:
            return None
        return {"id": w.id, "role": w.role, "on_shift": w.shift_start_ms is not None, "shift_start_ms": w.shift_start_ms,
                "hours_on_shift": round((now - w.shift_start_ms) / 3_600_000, 2) if w.shift_start_ms else 0.0,
                "last_break_ms": w.last_break_ms, "break_due": wid in self.breaks_due(now),
                "zone_id": w.zone_id, "history": [h for h in self.history if h["worker"] == wid],
                "retention_days": self.privacy.get("retention_days", 30)}

    def wire(self, now: int | None = None) -> dict[str, Any]:
        counts: dict[str, int] = {}
        workers = []
        for w in self.workers.values():
            if w.fresh and w.zone_id:
                counts[w.zone_id] = counts.get(w.zone_id, 0) + 1
            show = self.location_visible(w)
            aider = self.nearest_first_aider(w) if (w.sos or w.man_down) else None
            workers.append({
                "id": w.id, "role": w.role, "badge_id": w.badge,
                "zone_id": w.zone_id if (w.fresh and show) else None,
                "x": w.x if show else None, "z": w.z if show else None, "fresh": w.fresh, "data_ms": w.data_ms,
                "near": None if w.near is None else {"forklift": w.near.forklift, "distance_m": w.near.distance_m,
                                                     "level": w.near.level, "reversing": w.near.reversing},
                "restricted_zone": w.restricted,
                "prealert": None if w.prealert is None else {"kind": w.prealert.kind, "deadline_ms": w.prealert.deadline_ms},
                "man_down": w.man_down, "sos_ms": w.sos_ms, "evacuate": w.evacuate, "lone": w.lone_level,
                "zone_overtime_min": w.zone_overtime_min, "first_aider": w.first_aider,
                "nearest_first_aider": None if aider is None else {"id": aider[0], "distance_m": aider[1]},
                "mustered": w.mustered, "location_shown": show,
            })
        t = self.today
        return {"workers": workers, "zone_counts": counts,
                "today": {"warnings": t.warnings, "criticals": t.criticals, "restricted": t.restricted,
                          "closest_m": t.closest_m, "closest": t.closest, "falls": t.falls, "falls_cancelled": t.falls_cancelled,
                          "sos": t.sos, "last_fall_ms": t.last_fall_ms, "last_sos_ms": t.last_sos_ms},
                "config": {"warn_m": self.cfg["warn_m"], "crit_m": self.cfg["crit_m"]},
                "evacuation": self.headcount(),
                "on_site": sum(1 for w in self.workers.values() if w.shift_start_ms is not None),
                "in_hazardous": sum(1 for w in self.workers.values() if w.fresh and w.zone_id in self.hazard_zone_ids),
                "gas_zones": self.gas_zones, "heat_zones": self.heat_zones, "ppe_reminders": self.ppe_reminders,
                "breaks_due": len(self.breaks_due(now)) if now is not None else 0,
                "privacy": {"location": self.privacy.get("location", "alerts_only"),
                            "retention_days": self.privacy.get("retention_days", 30)}}
