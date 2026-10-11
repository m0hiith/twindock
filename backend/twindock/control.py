"""Automatic actions and maintenance (R5): the twin reacts to what its devices report, like a plant's CMMS and BMS.

- Bearing work orders: a machine's vibration is abnormal against its baseline -> a work order and a recommendation
  to stop the machine for a bearing change. Stopping production is a person's decision: nothing happens until
  someone approves it on /control. Then the mechanical technician walks there (their simulated badge), the repair
  starts when they arrive (the machine goes to maintenance), and the baseline relearns afterwards.
- Leak work orders: during a break no machine uses air, so what the compressors deliver is what leaks. The twin
  measures that from the compressor monitors; above the limit it raises a leak-fix work order (no production stop,
  so it is dispatched at once).
- Compressor service: from the compressor's run-hour readings, every service interval. The other compressor
  covers, so it is dispatched at once unless the other one can't run.
- Peak demand: when the 15-minute demand nears the limit, the BMS is asked to shed non-critical loads (EV charging,
  some lighting); they are restored once demand has stayed low.
- Emergencies: a fire alarm raises a recommendation to call the fire brigade; a person decides.

Every automatic action is logged as cause -> action -> result. The plant's own interlocks (low air trips, gas
ventilation, fire door holds, the cold room door alarm) are the plant's PLCs: the simulator models them and /model
lists their causes; this module only acts through the same simulator commands a real integration would use.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

KEEP_ACTIONS = 60
KEEP_DONE = 40


@dataclass
class WorkOrder:
    id: str
    kind: str              # bearing | leak_fix | compressor_service
    asset: str             # machine id (M-01) or compressor device (CP-01)
    asset_label: str
    cause: str
    created_ms: int
    state: str = "open"    # awaiting_approval | dispatched | in_progress | done | dismissed | broke_down | waiting
    technician: str | None = None
    target: tuple[float, float] | None = None
    started_ms: int | None = None
    job_s: float = 0.0
    updated_ms: int = 0
    result: str | None = None
    saw_maintenance: bool = False

    def wire(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "asset_id": self.asset, "asset_label": self.asset_label, "state": self.state,
                "cause": self.cause, "created_ms": self.created_ms, "updated_ms": self.updated_ms, "technician": self.technician,
                "started_ms": self.started_ms, "job_s": self.job_s, "result": self.result}


@dataclass
class Recommendation:
    id: str
    kind: str              # stop_machine | emergency_call
    text: str
    created_ms: int
    wo_id: str | None = None
    subject: str | None = None

    def wire(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "text": self.text, "created_ms": self.created_ms, "wo_id": self.wo_id}


@dataclass
class Action:
    ts_ms: int
    cause: str
    action: str
    result: str | None = None

    def wire(self) -> dict[str, Any]:
        return {"ts_ms": self.ts_ms, "cause": self.cause, "action": self.action, "result": self.result}


@dataclass
class Control:
    cfg: dict[str, Any]
    wos: dict[str, WorkOrder] = field(default_factory=dict)
    recs: dict[str, Recommendation] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    shed: bool = False
    shed_low_since: int | None = None
    leak_estimate: float | None = None
    leak_measured_ms: int | None = None
    _break_flow: list[float] = field(default_factory=list)
    _break_seen: set[int] = field(default_factory=set)
    _last_service: dict[str, float] = field(default_factory=dict)
    _dismissed_until: dict[str, int] = field(default_factory=dict)
    _fire_rec: bool = False
    _n_wo: int = 0
    _n_rec: int = 0
    dirty: bool = True

    def __post_init__(self) -> None:
        self._last_service = {k: float(v) for k, v in (self.cfg.get("last_service_run_hours") or {}).items()}

    # ------------------------------------------------------------------ bookkeeping

    def log(self, now: int, cause: str, action: str, result: str | None = None) -> Action:
        a = Action(now, cause, action, result)
        self.actions.append(a)
        del self.actions[:-KEEP_ACTIONS]
        self.dirty = True
        return a

    def new_wo(self, now: int, kind: str, asset: str, label: str, cause: str) -> WorkOrder:
        self._n_wo += 1
        wo = WorkOrder(f"WO-{self._n_wo:04d}", kind, asset, label, cause, now, updated_ms=now)
        self.wos[wo.id] = wo
        done = [w for w in self.wos.values() if w.state in ("done", "dismissed")]
        for w in done[:-KEEP_DONE]:
            del self.wos[w.id]
        self.dirty = True
        return wo

    def new_rec(self, now: int, kind: str, text: str, wo_id: str | None = None, subject: str | None = None) -> Recommendation:
        self._n_rec += 1
        r = Recommendation(f"R-{self._n_rec:04d}", kind, text, now, wo_id, subject)
        self.recs[r.id] = r
        self.dirty = True
        return r

    def open_for(self, kind: str, asset: str) -> WorkOrder | None:
        return next((w for w in self.wos.values() if w.kind == kind and w.asset == asset and w.state not in ("done", "dismissed")), None)

    def wire(self) -> dict[str, Any]:
        order = {"awaiting_approval": 0, "in_progress": 1, "dispatched": 2, "waiting": 3, "broke_down": 4, "done": 5, "dismissed": 6}
        wos = sorted(self.wos.values(), key=lambda w: (order.get(w.state, 9), -w.created_ms))
        return {"work_orders": [w.wire() for w in wos], "recommendations": [r.wire() for r in self.recs.values()],
                "actions": [a.wire() for a in reversed(self.actions)][:30], "shed": self.shed,
                "leak_estimate_nm3_min": None if self.leak_estimate is None else round(self.leak_estimate, 3),
                "leak_measured_ms": self.leak_measured_ms}


class ControlLoop:
    """The engine-facing part: reads the engine's facts each second, decides, and acts through engine callbacks."""

    def __init__(self, engine: Any) -> None:
        self.e = engine
        self.cfg: dict[str, Any] = dict(engine.devices.cfg.get("cmms") or {})
        self.c = Control(self.cfg)
        self._acc = 0.0

    # ------------------------------------------------------------------ helpers over the engine

    def now(self) -> int:
        return int(self.e.clock())

    def fresh(self, did: str) -> Any:
        st = self.e.devices.sim.get(did)
        now = self.now()
        return st if st is not None and st.last_seen_ms is not None and now - st.last_seen_ms <= 15_000 else None

    def reading(self, did: str, ch: str) -> Any:
        st = self.fresh(did)
        r = st.readings.get(ch) if st else None
        return None if r is None else r.value

    def tech(self, role: str) -> Any:
        """The technician for this trade who is on site now (the roster has one per shift where the trade is staffed)."""
        ids = (self.cfg.get("technicians") or {}).get(role) or []
        ids = [ids] if isinstance(ids, str) else ids
        workers = [self.e.safety.workers[i] for i in ids if i in self.e.safety.workers]
        return next((w for w in workers if self.tech_ready(w)), workers[0] if workers else None)

    def tech_ready(self, w: Any) -> bool:
        return w is not None and self.fresh(w.badge) is not None and w.x is not None and self.e.sim_reachable

    def walk(self, w: Any, target: tuple[float, float]) -> None:
        self.e._site_command(w.badge, "goto", {"x": target[0], "z": target[1], "path": self.e._walk_to(w.badge, target)})

    # ------------------------------------------------------------------ tick

    def tick(self, dt: float) -> None:
        self._acc += dt
        if self._acc < float(self.cfg.get("eval_s", 1.0)):
            return
        self._acc = 0.0
        if not self.cfg:
            return
        now = self.now()
        self._bearings(now)
        self._leaks(now)
        self._compressor_service(now)
        self._progress(now)
        self._peak(now)
        self._emergency(now)

    # ------------------------------------------------------------------ bearing work orders

    def _bearings(self, now: int) -> None:
        c = self.c
        prod = self.e.production
        for mid, m in prod.machines.items():
            if not self.fresh(m.device_id):
                continue
            wo = c.open_for("bearing", mid)
            if wo is None and m.base.abnormal and now >= c._dismissed_until.get(mid, 0):
                cause = f"{mid} {m.label.lower()} vibration abnormal against its baseline (z {m.base.z:.1f}, {m.vibration_rms or 0:.2f} mm/s)"
                wo = c.new_wo(now, "bearing", mid, f"{mid} {m.label}", cause)
                wo.state = "awaiting_approval"
                mins = float(self.cfg.get("bearing_change_min", 25))
                rec = c.new_rec(now, "stop_machine", f"Stop {mid} {m.label.lower()} for a bearing change (about {mins:.0f} min). {cause}.", wo.id, mid)
                c.log(now, cause, f"work order {wo.id} raised; asking a person to approve stopping {mid} ({rec.id})")
                self.e.event("warn", f"{wo.id}: {mid} needs a bearing change; stopping it needs approval on /control", "control", mid)
            elif wo is not None and wo.state in ("awaiting_approval", "dispatched", "waiting") and m.state == "fault" \
                    and m.last_fault and m.last_fault.get("text") == self.cfg.get("bearing_failure_alarm", "Bearing failure"):
                wo.state, wo.updated_ms = "broke_down", now
                wo.result = f"The bearing failed before the repair: {mid} broke down at {m.vibration_rms or 0:.2f} mm/s"
                for r in [r for r in c.recs.values() if r.wo_id == wo.id]:
                    del c.recs[r.id]
                c.log(now, f"{mid} broke down: bearing failure", f"{wo.id} closed as a breakdown", wo.result)
                self._release(wo)

    # ------------------------------------------------------------------ leak work orders

    def _leaks(self, now: int) -> None:
        """Measure leaks in breaks: no machine uses air, so the compressors' delivery is the leak flow."""
        c = self.c
        prod = self.e.production
        fresh = [m for m in prod.machines.values() if self.fresh(m.device_id)]
        in_break = len(fresh) == len(prod.machines) and all(m.state == "planned_stop" for m in fresh)
        comps = [d for d, x in self.e.devices.defs.items() if x["type"] == "compressor_monitor"]
        flows = [self.reading(d, "flow_nm3_min") for d in comps]
        if in_break and all(f is not None for f in flows):
            c._break_flow.append(sum(float(f) for f in flows))
            return
        if not c._break_flow:
            return
        samples, c._break_flow = c._break_flow, []
        if len(samples) < int(self.cfg.get("leak_min_samples", 120)):
            return  # too short a break to average the compressors' load/unload cycles
        est = sum(samples) / len(samples)
        c.leak_estimate, c.leak_measured_ms = est, now
        c.dirty = True
        limit = float(self.cfg.get("leak_limit_nm3_min", 0.35))
        done = next((w for w in reversed(list(c.wos.values())) if w.kind == "leak_fix" and w.state == "done" and w.result and "next break" in w.result), None)
        if done is not None:
            done.result = f"Leaks measured at the next break: {est:.2f} Nm³/min"
            c.log(now, "break-time compressor delivery measured", "follow-up of " + done.id, done.result)
        if est > limit and c.open_for("leak_fix", "CP-01") is None:
            cause = f"compressors delivered {est:.2f} Nm³/min during the break with no machine running: leaks above {limit:.2f} Nm³/min"
            wo = c.new_wo(now, "leak_fix", "CP-01", "Compressed-air network", cause)
            c.log(now, cause, f"leak-fix work order {wo.id} raised and dispatched (no production stop)")
            self._dispatch(wo, now, "utilities", self._point_near_zone("FAC01_PRODUCTION"), float(self.cfg.get("leak_fix_min", 20)) * 60)

    # ------------------------------------------------------------------ compressor service

    def _compressor_service(self, now: int) -> None:
        c = self.c
        interval = float(self.cfg.get("compressor_service_interval_h", 2000))
        comps = [d for d, x in self.e.devices.defs.items() if x["type"] == "compressor_monitor"]
        for d in comps:
            hours = self.reading(d, "run_hours")
            if hours is None or d not in c._last_service:
                continue
            if float(hours) - c._last_service[d] < interval or c.open_for("compressor_service", d):
                continue
            others_ok = any(self.reading(o, "tripped") is False for o in comps if o != d)
            cause = f"{d} has run {float(hours) - c._last_service[d]:.0f} loaded hours since its last service (interval {interval:.0f} h)"
            wo = c.new_wo(now, "compressor_service", d, f"Compressor {d}", cause)
            if others_ok:
                c.log(now, cause, f"service work order {wo.id} raised and dispatched (the other compressor covers)")
                self._dispatch(wo, now, "utilities", self._device_point(d), float(self.cfg.get("compressor_service_min", 40)) * 60)
            else:
                wo.state = "waiting"
                c.log(now, cause, f"service work order {wo.id} raised; waiting: the other compressor can't take the load")

    # ------------------------------------------------------------------ dispatch and progress

    def _dispatch(self, wo: WorkOrder, now: int, role: str, target: tuple[float, float] | None, job_s: float) -> None:
        w = self.tech(role)
        wo.job_s, wo.target, wo.updated_ms = job_s, target, now
        if target is None or not self.tech_ready(w):
            wo.state = "waiting"
            self.c.log(now, f"{wo.id} ready to start", f"no {role} technician reachable: {wo.id} waits", None)
            return
        wo.technician, wo.state = w.id, "dispatched"
        self.walk(w, target)
        self.c.log(now, f"{wo.id} dispatched", f"{w.id} ({w.role.replace('_', ' ')}) walks to {wo.asset_label}")
        self.e.event("info", f"{wo.id}: {w.id} on the way to {wo.asset_label}", "control", wo.asset if wo.asset.startswith("M-") else None)

    def _release(self, wo: WorkOrder) -> None:
        w = self.e.safety.workers.get(wo.technician or "")
        if w is not None and self.e.sim_reachable and self.e.devices.defs.get(w.badge, {}).get("source") == "sim":
            self.e._site_command(w.badge, "route", {"route": "default"})

    def _progress(self, now: int) -> None:
        c = self.c
        arrive = float(self.cfg.get("arrive_m", 4.0))
        for wo in list(c.wos.values()):
            if wo.state == "waiting":
                role = "mechanical" if wo.kind == "bearing" else "utilities"
                if self.tech_ready(self.tech(role)) and (wo.kind != "compressor_service" or self._others_ok(wo.asset)):
                    self._dispatch(wo, now, role, wo.target or self._target_for(wo), wo.job_s or self._job_s(wo))
                continue
            if wo.state == "dispatched":
                w = self.e.safety.workers.get(wo.technician or "")
                if w is None or w.x is None or wo.target is None:
                    continue
                if math.dist((w.x, w.z), wo.target) <= arrive:
                    self._start(wo, now)
            elif wo.state == "in_progress":
                self._finish_if_done(wo, now)
            elif wo.state == "broke_down":
                m = self.e.production.machines.get(wo.asset)
                if m is not None and m.state not in ("fault", "maintenance") and self.fresh(m.device_id):
                    wo.state, wo.updated_ms = "done", now
                    m.base = self.e.production.new_baseline()
                    m.vib_recent.clear()
                    c.log(now, f"{wo.asset} repaired after the breakdown", f"{wo.id} closed; vibration baseline relearning", wo.result)
                    c.dirty = True

    def _others_ok(self, d: str) -> bool:
        return any(self.reading(o, "tripped") is False for o, x in self.e.devices.defs.items() if x["type"] == "compressor_monitor" and o != d)

    def _target_for(self, wo: WorkOrder) -> tuple[float, float] | None:
        if wo.kind == "bearing":
            return self._machine_point(wo.asset)
        if wo.kind == "leak_fix":
            return self._point_near_zone("FAC01_PRODUCTION")
        return self._device_point(wo.asset)

    def _job_s(self, wo: WorkOrder) -> float:
        key = {"bearing": "bearing_change_min", "leak_fix": "leak_fix_min", "compressor_service": "compressor_service_min"}[wo.kind]
        return float(self.cfg.get(key, 20)) * 60

    def _start(self, wo: WorkOrder, now: int) -> None:
        c = self.c
        wo.state, wo.started_ms, wo.updated_ms = "in_progress", now, now
        if wo.kind == "bearing":
            m = self.e.production.machines[wo.asset]
            wo.result = f"vibration before: {m.vibration_rms or 0:.2f} mm/s (baseline {m.base.stats.mean:.2f})"
            self.e._site_command(m.device_id, "repair", {"seconds": wo.job_s})
            c.log(now, f"{wo.technician} at {wo.asset}", f"{wo.asset} stopped for the bearing change ({wo.job_s / 60:.0f} min)")
        elif wo.kind == "compressor_service":
            self.e._site_command(wo.asset, "service", {"seconds": wo.job_s})
            c.log(now, f"{wo.technician} at {wo.asset}", f"{wo.asset} taken out for its service ({wo.job_s / 60:.0f} min); the other compressor covers")
        else:
            c.log(now, f"{wo.technician} in the production hall", f"leak survey and repair started ({wo.job_s / 60:.0f} min)")

    def _finish_if_done(self, wo: WorkOrder, now: int) -> None:
        c = self.c
        if wo.kind == "bearing":
            m = self.e.production.machines[wo.asset]
            if m.state == "maintenance":
                wo.saw_maintenance = True
                return
            if not wo.saw_maintenance or not self.fresh(m.device_id):
                return
            m.base = self.e.production.new_baseline()  # a new bearing: learn the machine's normal again
            m.vib_recent.clear()
            wo.result = f"{wo.result}; new bearing fitted, {wo.asset} back {m.state}; baseline relearning"
        else:
            if wo.started_ms is None or now - wo.started_ms < wo.job_s * 1000:
                return
            if wo.kind == "leak_fix":
                self.e._site_command("CP-01", "fix_leaks", None)
                wo.result = f"leaks repaired; before {c.leak_estimate or 0:.2f} Nm³/min; measured again at the next break"
            else:
                hours = self.reading(wo.asset, "run_hours")
                c._last_service[wo.asset] = float(hours) if hours is not None else c._last_service.get(wo.asset, 0.0)
                wo.result = f"{wo.asset} serviced at {c._last_service[wo.asset]:.0f} run hours"
        wo.state, wo.updated_ms = "done", now
        c.log(now, f"{wo.id} job finished", f"{wo.id} closed", wo.result)
        self.e.event("info", f"{wo.id} done: {wo.result}", "control", wo.asset if wo.asset.startswith("M-") else None)
        self._release(wo)

    # ------------------------------------------------------------------ peak demand

    def _peak(self, now: int) -> None:
        c = self.c
        p = self.e.power_summary()
        if not p.get("available"):
            return
        dem, limit = p.get("demand_15min_kw"), float(p["peak_kw"])
        incomer = (self.e.devices.cfg.get("utilities") or {}).get("incomer")
        if dem is None or not incomer or not self.e.sim_reachable:
            return
        if not c.shed and dem >= float(self.cfg.get("peak_shed_share", 0.95)) * limit:
            c.shed, c.shed_low_since = True, None
            self.e._site_command(incomer, "shed", {"on": True})
            c.log(now, f"15-minute demand {dem:.0f} kW, {dem / limit:.0%} of the {limit:.0f} kW limit",
                  "BMS asked to shed non-critical loads: EV charging and some lighting")
            self.e.event("warn", f"Peak demand {dem:.0f} kW: non-critical loads shed (EV charging, some lighting)", "control")
        elif c.shed:
            low = dem < float(self.cfg.get("peak_restore_share", 0.85)) * limit
            c.shed_low_since = (c.shed_low_since or now) if low else None
            if low and now - (c.shed_low_since or now) >= float(self.cfg.get("restore_after_min", 10)) * 60_000:
                c.shed, c.shed_low_since = False, None
                self.e._site_command(incomer, "shed", {"on": False})
                last = next((a for a in reversed(c.actions) if a.action.startswith("BMS asked to shed")), None)
                if last is not None and last.result is None:
                    last.result = f"demand fell to {dem:.0f} kW and stayed below {float(self.cfg.get('peak_restore_share', 0.85)):.0%} of the limit"
                c.log(now, f"15-minute demand back to {dem:.0f} kW", "shed loads restored")

    # ------------------------------------------------------------------ emergencies

    def _emergency(self, now: int) -> None:
        c = self.c
        fire = bool(self.e._fire_zones())
        if fire and not c._fire_rec:
            c._fire_rec = True
            zones = ", ".join(self.e.devices.zone_by_id.get(z, {}).get("name", z) for z in self.e._fire_zones())
            c.new_rec(now, "emergency_call", f"Fire alarm ({zones}): call the fire brigade (101). The evacuation advice has started; calling is a person's decision.")
            c.log(now, f"fire panel alarm in {zones}", "recommendation to call the fire brigade raised for a person to decide")
        elif not fire and c._fire_rec:
            c._fire_rec = False
            for r in [r for r in c.recs.values() if r.kind == "emergency_call"]:
                del c.recs[r.id]
            c.dirty = True

    # ------------------------------------------------------------------ a person's decision

    def decide(self, rec_id: str, decision: str, by: str) -> str | None:
        c = self.c
        r = c.recs.get(rec_id)
        if r is None:
            return f"No open recommendation {rec_id}"
        now = self.now()
        del c.recs[rec_id]
        c.dirty = True
        wo = c.wos.get(r.wo_id or "")
        if r.kind == "emergency_call":
            if decision == "approve":
                c.log(now, r.text, f"{by} confirmed calling the fire brigade (the twin only records the decision)")
            else:
                c.log(now, r.text, f"{by} decided not to call the fire brigade")
            return None
        if wo is None:
            return None
        if decision == "dismiss":
            wo.state, wo.updated_ms, wo.result = "dismissed", now, f"dismissed by {by}"
            c._dismissed_until[wo.asset] = now + int(float(self.cfg.get("dismiss_quiet_min", 30)) * 60_000)
            c.log(now, r.text, f"{by} dismissed {wo.id}; {wo.asset} keeps running")
            return None
        c.log(now, r.text, f"{by} approved stopping {wo.asset}")
        self._dispatch(wo, now, "mechanical", self._machine_point(wo.asset), float(self.cfg.get("bearing_change_min", 25)) * 60)
        return None

    # ------------------------------------------------------------------ places

    def _machine_point(self, mid: str) -> tuple[float, float] | None:
        u = self.e.world.entities.get(mid)
        return None if u is None else (u.x, u.z + float(self.cfg.get("work_offset_m", 2.5)))

    def _device_point(self, did: str) -> tuple[float, float] | None:
        d = self.e.devices.defs.get(did)
        return None if d is None else (float(d["x"]), float(d["z"]))

    def _point_near_zone(self, zone: str) -> tuple[float, float] | None:
        return self.e._zone_centroid(zone)

