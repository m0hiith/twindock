"""The backend's single source of truth: world + gateway + shared selection + auto mode.

All inputs (client intents, MQTT messages, ticks) go through Engine methods, which mutate state
and append outgoing messages to self.out. The async layer (main.py) only moves bytes: it feeds
inputs in and sends whatever is in self.out. That keeps every rule testable without sockets.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import TypeAdapter

from . import planner
from .ble_tracker import BleConfig, BleTracker, ZoneChange
from .contract import CLIENT_TYPES, first_error, mqtt_validator, validator
from .devices import DeviceRegistry, load_sites, parse_site_topic
from .production import Production
from .rules import Rules, load_rules
from .routing import PedGraph, evacuation_routes
from .safety import Safety, Today, heat_index_c
from .simclock import SPEEDS, SimClock
from .gateway import GatewayStore
from .graph import Graph
from .hardware import (EXPOSED_BUTTONS, LED_CONFIRM_TIMEOUT_MS, RULE_LED_RETRY_MS, RULE_LEDS,
                       SHORT_PRESS_MAX_MS)
from .models import (AckAlert, SafetyCommand, ScenarioCommand, AlertsUpdate, BleTracks, ButtonState, ClientMessage, CommandAck, DeviceUpdate, Event, GatewayUpdate, Layout, LedCommand,
                     MachineCommand, MoveUnit, PendingLed, ProductionUpdate, RawMqtt, SafetyUpdate, SelectionChanged,
                     SelectUnit, SetAutoMode, SetSimSpeed, SimClockMsg, Timed, UnitUpdate, WarmStart, WorldSnapshot)
from .world import Entity, World

TOPIC_PREFIX = "twin/gateway/"
CMD_LED_TOPIC = "twin/gateway/cmd/led"
AUTO_PERIOD_S = 1.0  # auto mode re-plans once a second; faster adds nothing visible
DEVICE_FLUSH_S = 0.5  # device_update at most 2 Hz: sim sensors report every 1-10 s, ages tick in the UI
PRODUCTION_FLUSH_S = 1.0  # production_update at most 1 Hz: machine monitors report once a second
SAFETY_EVAL_S = 0.25     # proximity check 4x a second: a forklift at demo pace covers ~1.4 m in that time
SAFETY_FLUSH_S = 0.5     # safety_update at most 2 Hz
RULES_EVAL_S = 0.5       # rules 2x a second: fast enough for 1.5 m proximity at demo pace, cheap
RULES_EVAL_FF_S = 2.0    # during the warm start nobody watches; alerts still raise and resolve, just less often
SIM_CLOCK_FLUSH_S = 5.0  # sim_clock every 5 s (and on change), so a screen's clock never drifts far at x20
SEVERITY_LEVEL = {"info": "info", "warning": "warn", "critical": "error"}


@dataclass
class WsOut:
    to: str | None  # client id, or None for everyone
    msg: dict[str, Any]


@dataclass
class MqttOut:
    topic: str
    payload: dict[str, Any]


def wall_ms() -> int:
    return int(time.time() * 1000)


_client_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


class Engine:
    def __init__(self, layout: Layout, clock: Callable[[], int] = wall_ms, ble_config: BleConfig | None = None,
                 sites: dict[str, Any] | None = None) -> None:
        self.layout = layout
        self.clock = clock
        # The simulation clock when the backend runs one (main.py); tests pass a plain callable.
        self.sim_clock: SimClock | None = clock if isinstance(clock, SimClock) else None
        self.warm_start: WarmStart | None = None
        self.fast_forward = False  # warm start: no clients yet, so skip building WebSocket diffs
        self._clock_acc = 0.0
        # Site twin: sim devices live in their own registry, which has no path to self.gw.
        self.devices = DeviceRegistry(sites if sites is not None else load_sites())
        self._dev_last: dict[str, dict[str, Any]] = {}
        self._dev_acc = 0.0
        self._prod_acc = 0.0
        self._prod_last: dict[str, Any] | None = None
        self._site_cmd_counter = 0
        self.devices.layout_nodes = {n.id: (n.x, n.z) for n in layout.nodes}
        cfg = self.devices.cfg
        self.safety = Safety.build(cfg["safety"], cfg.get("workers", []), privacy=cfg.get("privacy"), sites=cfg["sites"],
                                   muster_points=cfg.get("muster_points"))
        self._worker_of_badge = {w["badge"]: w["id"] for w in cfg.get("workers", [])}
        self._worker_of_device = {d["id"]: d["attached_to"] for d in cfg["devices"]
                                  if d.get("attached_to") in {w["id"] for w in cfg.get("workers", [])}}
        self._safety_acc = 0.0
        self._safety_flush_acc = 0.0
        self._safety_last: dict[str, Any] | None = None
        self.rules = Rules(load_rules())
        self._rules_acc = 0.0
        self.ped = PedGraph(layout)
        self._routes: list[dict[str, Any]] = []
        self._routes_key: tuple[Any, ...] | None = None
        self._fire_evac = False
        self._energy: dict[str, dict[str, Any]] = {}
        # Grid import from the incomer's kWh register: (time, kWh) over the last 15 min for the demand charge, today's
        # 15-min peak, and today's cost on the time-of-day tariff. All from meter readings, nothing modelled here.
        self._import_kwh: deque[tuple[int, float]] = deque()
        self._demand = {"day": "", "peak_kw": None, "cost": 0.0, "kwh": 0.0, "last": None}
        self._energy_acc = 0.0
        self._gw_was_online = False
        graph = Graph(layout)
        self.world = World(layout, graph)
        forklift_nodes = {n.id for n in layout.nodes if "forklift" in n.kinds}
        self.ble = BleTracker(ble_config if ble_config is not None else BleConfig.load(valid_nodes=forklift_nodes))
        self._device_goal: dict[str, str] = {}   # forklift -> zone node its tag says it is in
        self._device_sent: dict[str, str] = {}   # forklift -> goal already turned into a move
        self.gw = GatewayStore()
        self.selected: str | None = None
        self.auto_mode = False
        self.mqtt_connected = False
        self.sim_attached = False  # the site simulator runs inside the backend (no broker; see embedded_sim.py)
        self.out: list[WsOut | MqttOut] = []
        self._seq = 0
        self._last_wire: dict[str, dict[str, Any]] = {}
        self._auto_acc = 0.0
        self._truck_cargo: dict[str, int] = {}
        self._led_cmd_counter = 0
        self._rule_retry_after: dict[str, int] = {}
        self._auto_mode_dirty = False
        # Auto mode's dice. TWINDOCK_AUTO_SEED makes a run repeatable (tests, debugging).
        seed = os.environ.get("TWINDOCK_AUTO_SEED")
        self.rng = random.Random(int(seed) if seed else None)
        self.production = self._new_production()
        self._seed_site_units()
        self._seed_workers()

    # ------------------------------------------------------------------ site twin units (FAC-01)

    def _line(self) -> dict[str, Any]:
        return dict((self.layout.model_extra or {}).get("production_line") or {"machines": []})

    def _new_production(self) -> Production:
        return Production(self.devices.cfg["production"], self._line()["machines"], self.devices.cfg["devices"])

    def _seed_site_units(self) -> None:
        """Machines are units (selectable, shown in the 3D line). Their state only ever comes from
        their machine monitor's readings; with no fresh data it is "no_data"."""
        for m in self._line()["machines"]:
            pm = self.production.machines.get(m["id"])
            self.world.add_entity(Entity(m["id"], "machine", "no_data", m["x"], m["z"], 0.0, source="sim",
                                         label=f"{m['id']} {m['label']}",
                                         meta={"task": "Waiting for machine monitor", "kind": m["kind"],
                                               "device": pm.device_id if pm else ""}))

    def _seed_workers(self) -> None:
        """Workers are units at their badge's position. Without a fresh position: state no_data."""
        for w in self.devices.cfg.get("workers", []):
            d = self.devices.defs[w["badge"]]
            self.world.add_entity(Entity(w["id"], "worker", "no_data", d["x"], d["z"], 0.0, source="sim",
                                         label=f"{w['id']} · {w['role'].replace('_', ' ')}",
                                         meta={"task": "No data from badge", "role": w["role"], "badge": w["badge"]}))

    def _tick_safety(self, dt: float) -> None:
        self._safety_acc += dt
        if self._safety_acc < SAFETY_EVAL_S:
            return
        self._safety_acc = 0.0
        now = self.clock()
        fresh = {w.badge: self.devices.wire_device(w.badge, self.gw, now, self.ble)["status"] == "online"
                 for w in self.safety.workers.values()}
        forklifts = [(f.id, f.x, f.z, f.speed, f.heading) for f in self.world.of_kind("forklift")]
        gas, heat, fire = self._zone_hazards(now)
        self._fire_response(fire, now)
        for level, text, uid in self.safety.evaluate(now, forklifts, fresh, self.devices.zone_by_id, gas, heat):
            self.event(level, text, "safety", uid)
        self._update_routes(gas | fire)
        self._badge_actions()
        warned = {w.near.forklift for w in self.safety.workers.values() if w.near}
        for f in self.world.of_kind("forklift"):
            # The forklift flashes its beacon while a pedestrian is too close (shown on its 3D model).
            if f.id in warned:
                f.meta["pedestrian_warning"] = True
            else:
                f.meta.pop("pedestrian_warning", None)
        for w in self.safety.workers.values():
            e = self.world.entities.get(w.id)
            if e is None:
                continue
            if not w.fresh or w.x is None or w.z is None:
                e.state, e.meta["task"] = "no_data", ("Off shift / not tracked" if w.shift_start_ms is None else "No data from badge")
                continue
            e.x, e.z, e.heading = w.x, w.z, w.heading
            e.state = "walking" if w.moving else "working"
            zone = self.devices.zone_by_id.get(w.zone_id or "")
            where = zone["name"] if zone else "outside the zones"
            e.meta["task"] = ("SOS" if w.sos else f"Man down ({where})" if w.man_down else
                              "Possible fall: waiting for the worker to cancel" if w.prealert else
                              f"Evacuate ({w.evacuate})" if w.evacuate else
                              f"Near moving {w.near.forklift} ({w.near.distance_m:.1f} m)" if w.near else
                              f"In restricted {where}" if w.restricted else
                              f"Check-in overdue · {where}" if w.lone_level else
                              f"{'Walking' if w.moving else 'Working'} · {where}")
        self._safety_flush_acc += SAFETY_EVAL_S
        if self._safety_flush_acc >= SAFETY_FLUSH_S:
            self._safety_flush_acc = 0.0
            self._send_safety()

    def _zone_hazards(self, now: int) -> tuple[set[str], dict[str, float], set[str]]:
        """Zones with a gas detector in alarm, the worst heat index per zone, and zones whose fire panel bridge reports
        an alarm, from fresh SIM device readings."""
        gas: set[str] = set()
        fire: set[str] = set()
        heat: dict[str, float] = {}
        for did, st in self.devices.sim.items():
            d = self.devices.defs[did]
            if st.last_seen_ms is None or now - st.last_seen_ms > 15_000:
                continue
            if d["type"] == "gas_detector" and st.readings.get("alarm") and st.readings["alarm"].value is True:
                gas.add(d["zone_id"])
            if d["type"] == "fire_panel" and st.readings.get("alarm") and st.readings["alarm"].value is True:
                fire.add(d["zone_id"])
            t, h = st.readings.get("temperature"), st.readings.get("humidity")
            if d["type"] == "env_sensor" and t is not None and h is not None:
                hi = heat_index_c(float(t.value), float(h.value))
                heat[d["zone_id"]] = max(hi, heat.get(d["zone_id"], -99.0))
        return gas, heat, fire

    def _fire_response(self, fire: set[str], now: int) -> None:
        """A fire panel bridge reports an alarm: start the evacuation (advice to badges and screens). Nothing is closed,
        locked or silenced: the certified fire system does that, we only read it. Ending it is a person's decision."""
        if fire and not self._fire_evac and self.safety.evacuation is None:
            zn = self.devices.zone_by_id.get(sorted(fire)[0], {}).get("name", "the campus")
            self.safety.start_evacuation(now, f"fire alarm: {zn}", "Fire panel bridge")
            self._fire_evac = True
            self.event("warn", f"Fire panel alarm in {zn}: evacuation started (advice only; the fire system is the certified one)", "safety")
        elif not fire:
            self._fire_evac = False

    def _update_routes(self, hazard_zones: set[str]) -> None:
        """While an evacuation runs or a gas alarm is on: for every zone with people (and the hazard zones), the walking route to
        the nearest muster point that is not beside the hazard."""
        if self.safety.evacuation is None and not self.safety.gas_zones:
            if self._routes:
                self._routes, self._routes_key = [], None
            return
        zc = {z: n for z, n in self.safety.wire(self.clock())["zone_counts"].items() if n}
        zones = sorted(set(zc) | hazard_zones | set(self.safety.gas_zones))
        key = (tuple(zones), tuple(sorted(hazard_zones)))
        if key == self._routes_key:
            return
        self._routes_key = key
        hz = []
        for z in hazard_zones | set(self.safety.gas_zones):
            c = self._zone_centroid(z)
            if c:
                hz.append(c)
        self._routes = evacuation_routes(self.ped, self.devices.zone_by_id, self.safety.muster_points, zones, hz)

    def _badge_actions(self) -> None:
        """Buzz / evacuate / resume commands for badges. Only simulated badges can be commanded; a real badge
        would get the same action over its own radio, which doesn't exist yet."""
        for badge, action, extra in self.safety.take_badge_actions():
            d = self.devices.defs.get(badge)
            if d is None or d["source"] != "sim" or not self.sim_reachable:
                continue
            if action == "buzz" and extra.get("route") == "evacuate":
                m = self._nearest_muster(badge)
                if m is not None:
                    self._site_command(badge, "goto", {"x": m["x"], "z": m["z"], "path": self._walk_path(badge, m)})
                    continue
            if action == "resume":
                self._site_command(badge, "route", {"route": "default"})
            else:
                self._site_command(badge, action, extra)

    def _nearest_muster(self, badge: str) -> dict[str, Any] | None:
        wid = self._worker_of_badge.get(badge)
        w = self.safety.workers.get(wid or "")
        pts = self.safety.muster_points
        if not pts:
            return None
        hz = [c for c in (self._zone_centroid(z) for z in [*self.safety.gas_zones, *self._fire_zones()]) if c]
        safe = [m for m in pts if all(math.dist((m["x"], m["z"]), h) >= 40.0 for h in hz)] or pts
        if w is None or w.x is None or w.z is None:
            return safe[0]
        return min(safe, key=lambda m: (m["x"] - w.x) ** 2 + (m["z"] - w.z) ** 2)  # type: ignore[operator]

    def _fire_zones(self) -> list[str]:
        now = self.clock()
        return [d["zone_id"] for did, st in self.devices.sim.items() if (d := self.devices.defs[did])["type"] == "fire_panel" and st.last_seen_ms is not None
                and now - st.last_seen_ms <= 15_000 and st.readings.get("alarm") is not None and st.readings["alarm"].value is True]

    def _walk_path(self, badge: str, muster: dict[str, Any]) -> list[list[float]]:
        """Walkway waypoints from where the worker is to the muster point: people use walkways and marked crossings only."""
        w = self.safety.workers.get(self._worker_of_badge.get(badge, ""))
        if w is None or w.x is None or w.z is None or muster["node"] not in self.ped.nodes:
            return []
        start = self.ped.nearest(w.x, w.z)
        dist, prev = self.ped.dijkstra(start)
        if muster["node"] not in dist:
            return []
        return [[self.ped.nodes[n][0], self.ped.nodes[n][1]] for n in self.ped.path(prev, start, muster["node"])][:80]

    def _zone_centroid(self, zone_id: str | None) -> tuple[float, float] | None:
        z = self.devices.zone_by_id.get(zone_id or "")
        if z is None:
            return None
        pts = z["polygon"]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def _hide_worker(self, wid: str) -> tuple[float, float] | None | bool:
        """Privacy: None when the worker's location may be shown; else the zone centroid to show instead
        (False when they are not in any zone)."""
        w = self.safety.workers.get(wid)
        if w is None or self.safety.location_visible(w):
            return None
        return self._zone_centroid(w.zone_id) or False

    # ------------------------------------------------------------------ monitoring centre (K4)

    def _tick_energy(self) -> None:
        """Per power meter: the kWh register at the start of today, and yesterday's total once a day has passed.
        In memory only, so after a restart "yesterday" is unknown until the next midnight: never invented."""
        now = self.clock()
        day = time.strftime("%Y-%m-%d", time.localtime(now / 1000))
        for did, st in self.devices.sim.items():
            if self.devices.defs[did]["type"] != "power_meter":
                continue
            r = st.readings.get("energy_kwh")
            if r is None or st.last_seen_ms is None or now - st.last_seen_ms > 15_000:
                continue
            e = self._energy.get(did)
            if e is None:
                self._energy[did] = {"day": day, "start": float(r.value), "yesterday": None, "since_ms": now}
            elif e["day"] != day:
                e.update(yesterday=float(r.value) - e["start"], day=day, start=float(r.value))
        self._tick_demand(now, day)

    def _tariff(self, now_ms: int) -> dict[str, Any] | None:
        t = (self.devices.cfg.get("utilities") or {}).get("tariff")
        if not t:
            return None
        lt = time.localtime(now_ms / 1000)
        h = lt.tm_hour + lt.tm_min / 60
        for b in t["bands"]:
            a, z = b["from_h"], b["to_h"]
            if (a <= h < z) if a < z else (h >= a or h < z):
                return {**b, "currency": t["currency"]}
        return None

    def _tick_demand(self, now: int, day: str) -> None:
        """15-minute demand (what utilities bill as maximum demand) and today's energy cost, from the incomer's
        kWh register: demand = ΔkWh over the last 15 min ÷ 0.25 h; cost = Σ ΔkWh × the tariff rate at that time."""
        u = self.devices.cfg.get("utilities") or {}
        st = self.devices.sim.get(u.get("incomer", ""))
        r = st.readings.get("energy_kwh") if st else None
        if r is None or st is None or st.last_seen_ms is None or now - st.last_seen_ms > 15_000:
            return
        kwh = float(r.value)
        d = self._demand
        if d["day"] != day:
            d.update(day=day, peak_kw=None, cost=0.0, kwh=0.0)
        if d["last"] is not None and kwh >= d["last"]:
            band = self._tariff(now)
            d["kwh"] += kwh - d["last"]
            d["cost"] += (kwh - d["last"]) * (band["rate"] if band else 0.0)
        d["last"] = kwh
        q = self._import_kwh
        q.append((now, kwh))
        while q and now - q[0][0] > 15 * 60_000:
            q.popleft()
        span_h = (q[-1][0] - q[0][0]) / 3_600_000
        if span_h * 60 >= 5:  # at least 5 min of register history before quoting a demand figure
            dem = (q[-1][1] - q[0][1]) / span_h
            d["kw15"] = dem
            d["peak_kw"] = dem if d["peak_kw"] is None else max(d["peak_kw"], dem)

    # ------------------------------------------------------------------ campus power (F3)

    @staticmethod
    def _sun(now_ms: int) -> float:
        lt = time.localtime(now_ms / 1000)
        h = lt.tm_hour + lt.tm_min / 60
        return 0.0 if h <= 6 or h >= 18 else math.sin(math.pi * (h - 6) / 12)

    def power_summary(self) -> dict[str, Any]:
        """kW by building from the feeder meters, the incomer (grid import), the rooftop solar meter, the generator and
        its controller, the incomer's power factor, 15-minute demand, today's energy cost, and energy per unit made.
        Every number is a (SIM) meter reading or arithmetic on readings; solar is computed only when no solar meter reports."""
        u = self.devices.cfg.get("utilities")
        if not u:
            return {"available": False}
        now = self.clock()

        def fresh(did: str | None) -> Any:
            st = self.devices.sim.get(did or "")
            return st if st is not None and st.last_seen_ms is not None and now - st.last_seen_ms <= 15_000 else None

        def reading(did: str | None, ch: str) -> Any:
            st = fresh(did)
            r = st.readings.get(ch) if st else None
            return None if r is None else r.value

        def kw(mid: str) -> float | None:
            v = reading(mid, "power_kw")
            return None if v is None else float(v)

        inc, gen = kw(u["incomer"]), kw(u["generator"])
        volts = reading(u["incomer"], "voltage_v")
        grid_ok = None if volts is None else float(volts) > 300
        solar_meas = kw(u.get("solar_meter", ""))
        if solar_meas is not None:
            solar = solar_meas
            solar_note = "Measured by the rooftop solar meter (inverter AC output, SIM). A zero-export limiter curtails the inverters so the site never exports."
        else:
            solar = sum(s["kwp"] for s in u["solar"]) * 0.8 * self._sun(now) if grid_ok else 0.0
            solar_note = "Computed from the time of day and the design size (360 kWp); not measured (no solar meter reporting)."
        zones = []
        for mid, zid in u["feeders"].items():
            zones.append({"meter": mid, "zone_id": zid, "name": self.devices.zone_by_id.get(zid, {}).get("name", zid), "kw": kw(mid)})
        metered = sum(z["kw"] or 0.0 for z in zones)
        demand = (inc or 0.0) + solar + (gen or 0.0) if grid_ok else (gen or 0.0)
        tank = self.devices.sim.get(u.get("diesel_tank", "TL-02"))
        diesel = tank.readings.get("level_pct") if tank else None
        prod_meter = next((m for m, z in u["feeders"].items() if z == "FAC01_PRODUCTION"), None)
        e = self._energy.get(prod_meter or "")
        st = self.devices.sim.get(prod_meter or "")
        kwh_today = (float(st.readings["energy_kwh"].value) - e["start"]) if e and st and "energy_kwh" in st.readings else None
        fin = self.production.machines.get(self.production.finished_by)
        units = fin.good if fin else 0
        gs = u.get("genset")
        gen_state = reading(gs, "engine_state")
        if gen_state is None and grid_ok is not None:
            gen_state = "running" if (gen or 0) > 1 else ("starting" if grid_ok is False else "off")
        genset = None if fresh(gs) is None else {k: reading(gs, k) for k in ("engine_state", "rpm", "coolant_c", "fuel_lph", "load_kw", "transfer", "mains_ok")}
        pf = reading(u["incomer"], "power_factor")
        band = self._tariff(now)
        d = self._demand
        return {
            "available": True, "sim": True, "grid_ok": grid_ok, "grid_kw": inc, "generator_kw": gen, "generator_state": gen_state if grid_ok is not None else None,
            "genset": genset, "solar_kw": round(solar, 1), "solar_measured": solar_meas is not None, "solar_note": solar_note,
            "demand_kw": None if grid_ok is None else round(demand, 1), "by_zone": zones, "other_kw": None if inc is None else round(max(0.0, (inc + solar) - metered), 1),
            "solar_share": None if not grid_ok or demand <= 0 else round(min(1.0, solar / demand), 3), "peak_kw": u["peak_kw"],
            "peak_exceeded": bool(inc is not None and inc > u["peak_kw"]), "diesel_pct": None if diesel is None else float(diesel.value),
            "power_factor": None if pf is None else float(pf),
            "demand_15min_kw": None if "kw15" not in d else round(d["kw15"], 1), "demand_15min_peak_kw": None if d["peak_kw"] is None else round(d["peak_kw"], 1),
            "tariff": None if band is None else {"label": band["label"], "rate": band["rate"], "currency": band["currency"]},
            "import_kwh_today": round(d["kwh"], 2), "cost_today": round(d["cost"], 2),
            "units_today": units, "production_kwh_today": None if kwh_today is None else round(kwh_today, 2),
            "kwh_per_unit": None if not kwh_today or units <= 0 else round(kwh_today / units, 3),
            "kwh_per_unit_note": "Production feeder energy since the backend started, divided by units made in the same time.",
        }

    def monitor_summary(self) -> dict[str, Any]:
        now = self.clock()
        kw = today = None
        yesterday = None
        since = None
        u = self.devices.cfg.get("utilities") or {}
        supply = {u.get("incomer"), u.get("solar_meter"), u.get("generator")} - {None}
        for did, e in self._energy.items():
            if supply and did not in supply:
                continue  # campus energy is what came in (grid + solar + generator); feeders are already inside it
            st = self.devices.sim[did]
            r, p = st.readings.get("energy_kwh"), st.readings.get("power_kw")
            if p is not None and st.last_seen_ms is not None and now - st.last_seen_ms <= 15_000:
                kw = (kw or 0.0) + float(p.value)
            if r is not None:
                today = (today or 0.0) + float(r.value) - e["start"]
            if e["yesterday"] is not None:
                yesterday = (yesterday or 0.0) + e["yesterday"]
            since = e["since_ms"] if since is None else min(since, e["since_ms"])
        return {"power": self.power_summary(), "energy": {"kw_now": None if kw is None else round(kw, 2), "today_kwh": None if today is None else round(today, 2),
                           "yesterday_kwh": None if yesterday is None else round(yesterday, 1), "counting_since_ms": since,
                           "source": "sim", "meters": sorted(d for d in self._energy if not supply or d in supply)},
                "incidents": self.rules.incidents(now),
                "evacuation_last": None if self.safety.last_evacuation is None else {
                    "started_ms": self.safety.last_evacuation.started_ms, "ended_ms": self.safety.last_evacuation.ended_ms,
                    "reason": self.safety.last_evacuation.reason, "by": self.safety.last_evacuation.by,
                    "on_site": len(self.safety.last_evacuation.on_site)},
                "safety_today": self.safety.wire(now)["today"]}

    # ------------------------------------------------------------------ rules and alerts (S6)

    def _facts(self) -> dict[str, list[dict[str, Any]]]:
        """Plain facts per subject for backend/rules/*.yaml. Only data that actually arrived is a fact."""
        now = self.clock()
        fresh = self._fresh()
        machines = []
        for mid, pm in self.production.machines.items():
            e = self.world.entities.get(mid)
            ok = fresh.get(pm.device_id, False)
            machines.append({"id": mid, "unit_id": mid, "label": pm.label, "label_lower": pm.label.lower(),
                             "state": pm.state if ok else None, "abnormal": pm.base.abnormal if ok else None,
                             "z_score": pm.base.z, "vibration_rms": pm.vibration_rms,
                             "fault_text": (pm.last_fault or {}).get("text"), "site_id": "FAC-01",
                             "x": e.x if e else None, "z": e.z if e else None})
        workers = []
        for w in self.safety.workers.values():
            # SOS and man-down stay facts even if the badge goes quiet: that is exactly when help is needed.
            if not w.fresh and not (w.sos or w.man_down or w.prealert or w.evacuate):
                continue
            zn = self.devices.zone_by_id.get(w.restricted or "")
            here = self.devices.zone_by_id.get(w.zone_id or w.last_zone_id or "")
            aider = self.safety.nearest_first_aider(w)
            workers.append({"id": w.id, "unit_id": w.id, "role_text": w.role.replace("_", " "),
                            "near_level": w.near.level if w.near else None,
                            "near_forklift": w.near.forklift if w.near else None,
                            "distance_m": w.near.distance_m if w.near else None,
                            "reversing_text": " (reversing)" if w.near and w.near.reversing else "",
                            "restricted_zone": w.restricted, "restricted_zone_name": zn["name"] if zn else None,
                            "zone_name": here["name"] if here else "an unknown zone",
                            "prealert": w.prealert.kind if w.prealert else None,
                            "prealert_left_s": max(0.0, (w.prealert.deadline_ms - now) / 1000) if w.prealert else None,
                            "man_down": w.man_down, "man_down_reason": {"fall": "fall not cancelled", "no_motion": "no movement"}.get(w.man_down or ""),
                            "sos": True if w.sos else None,
                            "first_aider_text": f"{aider[0]} ({aider[1]:.0f} m)" if aider else "none on site",
                            "zone_overtime_min": w.zone_overtime_min, "lone_level": w.lone_level, "evacuate": w.evacuate,
                            "site_id": here["site_id"] if here else "FAC-01", "x": w.x, "z": w.z})
        devices = []
        for d in self.devices.wire(self.gw, now, self.ble):
            if d["source"] != "sim":
                continue  # real devices have their own rules (gateway) on real data
            f: dict[str, Any] = {"id": d["id"], "device_id": d["id"], "type": d["type"], "label": d.get("label"),
                                 "status": d["status"], "zone_id": d["zone_id"], "source": d["source"],
                                 "zone_name": self.devices.zone_by_id.get(d["zone_id"], {}).get("name"),
                                 "fault": d.get("fault"), "site_id": d["site_id"], "x": d["x"], "z": d["z"]}
            if d["status"] in ("online", "fault"):  # a stale reading is not a current condition
                for ch, r in d["readings"].items():
                    f.setdefault(ch, r["value"])
                if isinstance(f.get("temperature"), (int, float)) and isinstance(f.get("humidity"), (int, float)):
                    f["heat_index"] = round(heat_index_c(float(f["temperature"]), float(f["humidity"])), 1)
            devices.append(f)
        g = self.layout.gateway
        gateway = [{"id": g.id, "unit_id": g.id, "device_id": g.id, "online": self.gw.online,
                    "was_online": self._gw_was_online, "site_id": "WH-01", "x": g.x, "z": g.z}]
        out = self.world.graph.nodes.get(self.production.outbound_node)
        line = [{"id": "FAC-01 line", "pallets_waiting": self.production.pallets_waiting, "site_id": "FAC-01",
                 "x": out.x if out else None, "z": out.z if out else None}]
        p = self.power_summary()
        inc_dev = self.devices.defs.get((self.devices.cfg.get("utilities") or {}).get("incomer", ""), {})
        site: list[dict[str, Any]] = []
        if p.get("available"):
            lost = 0
            if p["grid_ok"] is False:  # mains devices that stopped reporting while the grid is down (critical zones keep their power)
                lost = sum(1 for d in self.devices.wire(self.gw, now, self.ble) if d["source"] == "sim" and d["protocol"] == "wifi" and d["status"] in ("stale", "offline")
                           and d["zone_id"] not in self.devices.cfg["utilities"]["critical_zones"])
            site.append({"id": "campus", "device_id": inc_dev.get("id"), "grid_ok": p["grid_ok"], "generator_state": p["generator_state"],
                         "generator_kw": p["generator_kw"], "grid_kw": p["grid_kw"], "peak_kw": p["peak_kw"],
                         "peak_exceeded": True if p["peak_exceeded"] else None, "diesel_pct": p["diesel_pct"], "lost_power_devices": lost or None,
                         "site_id": inc_dev.get("site_id", "FAC-01"), "x": inc_dev.get("x"), "z": inc_dev.get("z")})
        return {"machine": machines, "worker": workers, "device": devices, "gateway": gateway, "line": line, "site": site}

    def _tick_rules(self, dt: float) -> None:
        self._energy_acc += dt
        if self._energy_acc >= 5.0:
            self._energy_acc = 0.0
            self._tick_energy()
        self._rules_acc += dt
        if self._rules_acc < (RULES_EVAL_FF_S if self.fast_forward else RULES_EVAL_S):
            return
        self._rules_acc = 0.0
        if self.gw.online:
            self._gw_was_online = True
        raised, resolved = self.rules.evaluate(self._facts(), self.clock())
        for a in raised:
            self.event(SEVERITY_LEVEL[a.severity], a.message, "rules", a.target.get("unit_id"))
        for a in resolved:
            self.event("info", f"Resolved: {a.message}", "rules", a.target.get("unit_id"))
        if raised or resolved:
            self._send_alerts()

    def _send_alerts(self, to: str | None = None) -> None:
        self._send(AlertsUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), **self.rules.wire()), to)

    def _ack_alert(self, client_id: str, m: AckAlert) -> None:
        reason = self.rules.acknowledge(m.alert_id, m.by.strip() or client_id, self.clock())
        self._ack(client_id, m.cmd_id, "ack_alert", reason is None, reason)
        if reason is None:
            self.event("info", f"{m.alert_id} acknowledged by {m.by.strip() or client_id}", client_id)
            self._send_alerts()

    def _send_safety(self, to: str | None = None) -> None:
        w = {**self.safety.wire(self.clock()), "routes": self._routes}
        if to is None and w == self._safety_last:
            return
        if to is None:
            self._safety_last = w
        self._send(SafetyUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), **w), to)

    def _fresh(self) -> dict[str, bool]:
        now = self.clock()
        return {m.device_id: self.devices.wire_device(m.device_id, self.gw, now, self.ble)["status"] == "online"
                for m in self.production.machines.values()}

    def _tick_production(self, dt: float) -> None:
        now = self.clock()
        fresh = self._fresh()
        self.production.tick(now, fresh)
        task = {"running": "Running", "idle": "Idle, waiting for material", "fault": "Fault",
                "maintenance": "Under maintenance", "no_data": "No data from machine monitor"}
        for mid, pm in self.production.machines.items():
            e = self.world.entities.get(mid)
            if e is None:
                continue
            e.state = self.production.machine_state(mid, fresh.get(pm.device_id, False))
            t = task[e.state]
            if e.state == "fault" and pm.last_fault:
                t = f"Fault: {pm.last_fault['text']}"
            elif e.state == "running" and pm.base.abnormal:
                t = "Running · abnormal vibration"
            e.meta["task"] = t
        # Finished units become pallets at the factory outbound spot (forklifts take them away).
        out = self.production.outbound_node
        while self.production.pallets_waiting > 0 and out in self.world.graph.nodes:
            n = self.production.pallets_made + 1
            pid = self.world.spawn_pallet(out, {"sku": f"FG-{n:04d}", "contents":
                                                f"Assembled units, {self.production.units_per_pallet} cartons",
                                                "origin": "FAC-01 line (simulated)"})
            if pid is None:
                break  # outbound full: the outbound_backlog rule raises the alert
            self.production.pallets_waiting -= 1
            self.production.pallets_made += 1
            self.event("info", f"{pid} finished on the FAC-01 line, waiting at {self.world.node_label(out)}",
                       "production", pid)
        self._prod_acc += dt
        if self._prod_acc >= PRODUCTION_FLUSH_S:
            self._prod_acc = 0.0
            self._send_production()

    def _send_production(self, to: str | None = None) -> None:
        w = self.production.wire(self._fresh())
        if to is None and w == self._prod_last:
            return
        if to is None:
            self._prod_last = w
        self._send(ProductionUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), **w), to)

    # ------------------------------------------------------------------ output helpers

    def drain(self) -> list[WsOut | MqttOut]:
        out, self.out = self.out, []
        return out

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _send(self, msg: Any, to: str | None = None) -> None:
        self.out.append(WsOut(to, msg.model_dump(mode="json")))

    def event(self, level: str, text: str, source: str = "system", unit_id: str | None = None,
              to: str | None = None) -> None:
        self._send(Event(seq=self._next_seq(), server_ts_ms=self.clock(), level=level,  # type: ignore[arg-type]
                         source=source, text=text, unit_id=unit_id), to)

    def _ack(self, to: str, cmd_id: str, command: str, ok: bool, reason: str | None = None,
             path: list[str] | None = None) -> None:
        self._send(CommandAck(cmd_id=cmd_id, command=command, ok=ok, reason=reason, path=path), to)  # type: ignore[arg-type]

    def _gateway_update(self, raw: RawMqtt | None = None) -> None:
        self._send(GatewayUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), gateway=self.gw.wire(), raw=raw))

    def _all_units(self) -> list[Any]:
        out = []
        for e in self.world.entities.values():
            u = self.world.to_unit(e)
            if e.kind == "worker" and e.state != "no_data":
                hide = self._hide_worker(e.id)
                if hide is not None:
                    # Zone counts only: the worker is shown in their zone, not at their position.
                    cx, cz = hide if hide else (u.x, u.z)
                    zone = self.devices.zone_by_id.get(self.safety.workers[e.id].zone_id or "")
                    u = u.model_copy(update={"x": round(cx, 1), "z": round(cz, 1), "heading_rad": 0.0, "state": "private",
                                             "task": f"In {zone['name']}" if zone else "On site"})
            out.append(u)
        return out

    def _masked_devices(self, devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Badge positions follow the same privacy rule as the workers wearing them."""
        out = []
        for d in devices:
            wid = self._worker_of_badge.get(d["id"])
            hide = self._hide_worker(wid) if (wid and d["source"] == "sim") else None
            if hide is not None:
                d = {**d, "readings": {k: v for k, v in d["readings"].items() if k != "position"}}
                if hide:
                    d["x"], d["z"] = round(hide[0], 1), round(hide[1], 1)
            out.append(d)
        return out

    def snapshot(self) -> WorldSnapshot:
        units = self._all_units()
        self._last_wire = {u.id: u.model_dump(mode="json") for u in units}
        now = self.clock()
        devices = self._masked_devices(self.devices.wire(self.gw, now, self.ble))
        self._dev_last = {d["id"]: d for d in devices}
        return WorldSnapshot(seq=self._next_seq(), server_ts_ms=now, layout_version=self.layout.version,
                             auto_mode=self.auto_mode, selected_unit_id=self.selected, units=units,
                             gateway=self.gw.wire(), sites=self.devices.sites, devices=devices)

    def _flush_devices(self) -> None:
        now = self.clock()
        changed = []
        for d in self._masked_devices(self.devices.wire(self.gw, now, self.ble)):
            if self._dev_last.get(d["id"]) != d:
                self._dev_last[d["id"]] = d
                changed.append(d)
        if changed:
            self._send(DeviceUpdate(seq=self._next_seq(), server_ts_ms=now, devices=changed))

    def _flush_units(self) -> None:
        changed = []
        for u in self._all_units():
            d = u.model_dump(mode="json")
            if self._last_wire.get(u.id) != d:
                self._last_wire[u.id] = d
                changed.append(u)
        removed = list(dict.fromkeys(self.world.removed))
        self.world.removed.clear()
        for rid in removed:
            self._last_wire.pop(rid, None)
        if changed or removed or self._auto_mode_dirty:
            self._send(UnitUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), units=changed,
                                  removed=removed or None,
                                  auto_mode=self.auto_mode if self._auto_mode_dirty else None))
            self._auto_mode_dirty = False

    def _drain_world_events(self) -> None:
        for level, text, unit_id in self.world.events:
            self.event(level, text, "system", unit_id)
        self.world.events.clear()

    # ------------------------------------------------------------------ lifecycle

    def speed_locked(self) -> str | None:
        if self.sim_clock is None:
            return "No simulation clock in this backend"
        if self.gw.online:
            return "The real board is online: board data always runs on real time"
        return None

    def _send_sim_clock(self, to: str | None = None) -> None:
        if self.sim_clock is None:
            return
        self._send(SimClockMsg(seq=self._next_seq(), server_ts_ms=self.clock(), sim_ms=self.sim_clock.sim_ms,
                               speed=self.sim_clock.speed, speeds=list(SPEEDS), warm_start=self.warm_start,  # type: ignore[arg-type]
                               speed_locked=self.speed_locked()), to)

    def _set_sim_speed(self, client_id: str, m: SetSimSpeed) -> None:
        locked = self.speed_locked()
        if self.sim_clock is None or (locked and m.speed != 1):
            self._ack(client_id, m.cmd_id, "set_sim_speed", False, locked)
            return
        self.sim_clock.speed = m.speed
        self._ack(client_id, m.cmd_id, "set_sim_speed", True)
        self.event("info", f"Simulation speed x{m.speed}" + (" (real time)" if m.speed == 1 else ""), client_id)
        self._send_sim_clock()

    def on_connect(self, client_id: str) -> None:
        self._send(self.snapshot(), client_id)  # always the first message on a connection
        self._send_sim_clock(client_id)
        self._send_ble_tracks(client_id)
        self._send_production(client_id)
        self._send_safety(client_id)
        self._send_alerts(client_id)

    def reset(self) -> None:
        """Restore the seed world. Gateway state is real device data and is kept."""
        self.world.reset()
        self.production = self._new_production()
        self._prod_last = None
        self._seed_site_units()
        self._seed_workers()
        # Every forklift is back at its seed spot and manual; tags re-acquire after stable_s.
        self.ble.forget_zones()
        self._device_goal.clear()
        self._device_sent.clear()
        self.selected = None
        self.auto_mode = False
        self._truck_cargo.clear()
        self._send(self.snapshot())
        self.event("info", "World reset to the seed layout")
        self._sync_rule_leds()

    @property
    def sim_reachable(self) -> bool:
        """Site commands reach the simulator: through the broker, or directly when it runs embedded."""
        return self.mqtt_connected or self.sim_attached

    def set_mqtt_connected(self, connected: bool) -> None:
        if connected == self.mqtt_connected:
            return
        self.mqtt_connected = connected
        self.event("info" if connected else "warn",
                   "Connected to the MQTT broker" if connected else "Lost the MQTT broker, reconnecting", "gateway")
        if connected:
            self._sync_rule_leds()

    def tick(self, dt: float) -> None:
        w = self.world
        w.tick(dt)
        planner.track_idle(w, self._truck_cargo)
        if self.auto_mode:
            self._auto_acc += dt
            if self._auto_acc >= AUTO_PERIOD_S:
                self._auto_acc = 0.0
                for note in planner.auto_step(w, self.rng):
                    self.event("info", note, "auto")
        else:
            for u in w.entities.values():
                if u.source == "auto" and not u.moving and not u.busy and u.action is None:
                    u.source = "manual"

        now = self.clock()
        lost = self.ble.expire(now)
        for t in lost:
            self._release_device(t.unit_id, f"Tag {t.name} not seen for {self.ble.config.lost_after_s:g} s")
        if lost:
            self._send_ble_tracks()
        for uid, goal in self._device_goal.items():
            if self._device_sent.get(uid) != goal:
                self._drive_device(uid)  # was busy finishing a pick or load when the zone changed
        if self.gw.refresh_online(now):
            self._on_online_changed()
        for name, st in self.gw.leds.items():
            if st.pending and now - st.pending.sent_ms > LED_CONFIRM_TIMEOUT_MS:
                st.pending = None
                if name in RULE_LEDS:
                    self._rule_retry_after[name] = now + RULE_LED_RETRY_MS
                self.event("warn", f"{name}: no confirmation from the board within "
                           f"{LED_CONFIRM_TIMEOUT_MS // 1000} s", "gateway")
                self._gateway_update()
        self._sync_rule_leds()
        self._tick_production(dt)
        self._tick_safety(dt)
        self._tick_rules(dt)
        self._drain_world_events()
        if self.sim_clock is not None:
            if self.sim_clock.speed != 1 and self.gw.online:
                self.sim_clock.speed = 1
                self.event("warn", "The real board came online: simulation back to real time (x1)", "sim")
                self._send_sim_clock()
            self._clock_acc += dt
            if self._clock_acc >= SIM_CLOCK_FLUSH_S * self.sim_clock.speed:
                self._clock_acc = 0.0
                self._send_sim_clock()
        if self.fast_forward:
            return
        self._flush_units()
        self._dev_acc += dt
        if self._dev_acc >= DEVICE_FLUSH_S:
            self._dev_acc = 0.0
            self._flush_devices()

    def _on_online_changed(self) -> None:
        self.world.gateway_state = "online" if self.gw.online else ("offline" if self.gw.last_status_ms else "waiting")
        self.world.entities[self.layout.gateway.id].state = self.world.gateway_state
        if self.gw.online:
            self.event("info", "Board online", "gateway")
            self._rule_retry_after.clear()
            self._gateway_update()
            self._sync_rule_leds()  # the board may have rebooted with the LED off
            return
        else:
            self.event("warn", "Board offline: no status for 15 s", "gateway")
        self._gateway_update()

    # ------------------------------------------------------------------ LEDs

    def _send_led(self, led: str, on: bool) -> None:
        # Server-generated id: short (fits the firmware's buffer, schema max 36) and never client text.
        self._led_cmd_counter += 1
        cmd_id = f"L{self._led_cmd_counter:06d}"
        payload = {"led": led, "on": on, "cmd_id": cmd_id}
        err = first_error(mqtt_validator("cmd_led"), payload)
        assert err is None, err
        self.out.append(MqttOut(CMD_LED_TOPIC, payload))
        self.gw.leds[led].pending = PendingLed(cmd_id=cmd_id, on=on, sent_ms=self.clock())
        self._gateway_update()

    def _sync_rule_leds(self) -> None:
        """LED0 follows Bay 1. Sends a command only when the confirmed state differs."""
        if "LED0" not in self.gw.leds or not self.gw.online or not self.mqtt_connected:
            return
        if self.clock() < self._rule_retry_after.get("LED0", 0):
            return
        desired = self.world.bay1_occupied()
        st = self.gw.leds["LED0"]
        if st.pending is not None:
            if st.pending.on == desired:
                return
        elif st.on == desired:
            return
        self._send_led("LED0", desired)

    # ------------------------------------------------------------------ MQTT in

    def on_mqtt(self, topic: str, payload: bytes, retained: bool = False) -> None:
        if not topic.startswith(TOPIC_PREFIX):
            self._on_site_mqtt(topic, payload)
            return
        if topic.startswith(TOPIC_PREFIX + "cmd/"):
            return  # our own commands echo back through the twin/gateway/# subscription
        rest = topic[len(TOPIC_PREFIX):]
        sensor_name = None
        if rest.startswith("sensor/"):
            kind, sensor_name = "sensor", rest[len("sensor/"):]
        elif rest in ("hello", "status", "button", "led", "ble"):
            kind = rest
        else:
            self.event("warn", f"Ignored unknown topic {topic}", "gateway")
            return
        now = self.clock()
        if not payload:
            if kind == "hello":  # retained hello cleared (mosquitto_pub -r -n)
                self.gw.hello = None
                self.gw.leds, self.gw.buttons, self.gw.sensors = {}, {}, {}
                self._gateway_update(RawMqtt(topic=topic, payload=None, received_ms=now))
            return
        try:
            data = json.loads(payload)
        except ValueError:
            self.event("warn", f"Dropped {topic}: not JSON", "gateway")
            return
        err = first_error(mqtt_validator(kind), data)
        if err:
            self.event("warn", f"Dropped invalid {topic}: {err}", "gateway")
            return
        if kind != "hello" and self.gw.hello is None:
            self.event("warn", f"Dropped {topic}: no hello from the board yet", "gateway")
            return

        self.gw.last_seen_ms = now
        if kind == "hello":
            ignored = self.gw.set_hello(data, now, retained)
            if ignored:
                self.event("warn", f"Board reports {', '.join(ignored)}, not in HARDWARE.md; ignored", "gateway")
        elif kind == "status":
            if data.get("replay"):
                self.gw.replays_received += 1
            else:
                self.gw.status = Timed(data=data, received_ms=now)
                if "wifi_rssi_dbm" in data:
                    self.devices.record_real(self.layout.gateway.id, "wifi_rssi_dbm", now, data["wifi_rssi_dbm"])
            self.gw.last_status_ms = now
            if self.gw.refresh_online(now):
                self._on_online_changed()
        elif kind == "button":
            name = data["button"]
            if name not in self.gw.buttons_available:
                self.event("warn", f"Dropped {name}: not an exposed button", "gateway")
                return
            prev = self.gw.buttons.get(name)
            self.gw.buttons[name] = ButtonState(state=data["state"], received_ms=now, ts_ms=data["ts_ms"])
            if data["state"] == "released" and prev is not None and prev.state == "pressed":
                held = data["ts_ms"] - prev.ts_ms  # both board clock, so network jitter doesn't count
                if 0 <= held <= SHORT_PRESS_MAX_MS:
                    self._gateway_update(RawMqtt(topic=topic, payload=data, received_ms=now))
                    self.on_short_press(name)
                    self._sync_rule_leds()
                    self._drain_world_events()
                    self._flush_units()
                    return
        elif kind == "led":
            name = data["led"]
            st = self.gw.leds.get(name)
            if st is None:
                self.event("warn", f"Dropped {name}: not an exposed LED", "gateway")
                return
            st.on, st.received_ms = data["on"], now
            p = st.pending
            if p and (data.get("cmd_id") == p.cmd_id or (data.get("cmd_id") is None and data["on"] == p.on)):
                st.pending = None
        elif kind == "ble":
            self.gw.ble = Timed(data=data, received_ms=now)
            self._apply_ble(self.ble.update(data["sightings"], now))
            self._send_ble_tracks()
        elif kind == "sensor":
            assert sensor_name is not None
            if sensor_name not in self.gw.sensors_available:
                self.event("warn", f"Dropped sensor {sensor_name}: not in hello or HARDWARE.md", "gateway")
                return
            self.gw.sensors[sensor_name] = Timed(data=data, received_ms=now)

        self._gateway_update(RawMqtt(topic=topic, payload=data, received_ms=now))
        if kind == "hello":
            self._sync_rule_leds()

    def on_site_payload(self, topic: str, data: dict[str, Any]) -> None:
        """A simulator message delivered in-process (embedded simulator): same path as MQTT, minus the JSON bytes."""
        self._on_site_mqtt(topic, data)

    def _on_site_mqtt(self, topic: str, payload: bytes | dict[str, Any]) -> None:
        """twin/<site>/<device>/<channel> from the simulator. Only the device registry is touched:
        never self.gw, never an LED, never MQTT out."""
        if not topic.startswith("twin/"):
            return
        if "/cmd/" in topic:
            return  # our own simulation commands echo back through twin/#
        now = self.clock()
        notes, changed = self.devices.on_mqtt(topic, payload, now)
        for n in notes:
            self.event(n.level, n.text, "sim")
        parsed = parse_site_topic(topic)
        if changed and parsed and parsed[2] == "position":
            wk = next((w for w in self.safety.workers.values() if w.badge == changed), None)
            st = self.devices.sim.get(changed)
            if wk and st and st.x is not None and st.z is not None:
                self.safety.set_position(wk.id, st.x, st.z, self.devices.zone_at(st.x, st.z, parsed[0]), now)
        if changed and parsed and parsed[2] in ("fall", "sos", "cancel", "checkin") and changed in self._worker_of_badge:
            r = self.devices.sim[changed].readings.get(parsed[2])
            if r is not None and r.received_ms == now:
                self.safety.on_badge(self._worker_of_badge[changed], parsed[2], r.value, now)
        if changed and parsed and parsed[2] == "worn" and changed in self._worker_of_device:
            r = self.devices.sim[changed].readings.get("worn")
            self.safety.set_helmet(self._worker_of_device[changed], bool(r.value) if r is not None else None)
        if changed and parsed and changed in self.production.by_device:
            r = self.devices.sim[changed].readings.get(parsed[2])
            if r is not None and r.received_ms == now:
                for level, text, mid in self.production.on_reading(changed, parsed[2], r.value, now):
                    self.event(level, text, "production", mid)

    def _site_command(self, device_id: str, action: str, extra: dict[str, Any] | None = None) -> str:
        """Command to a SIMULATED device via tools/site_sim.py. Never the real board."""
        d = self.devices.defs[device_id]
        assert d["source"] == "sim" and device_id not in self.devices.real_ids, "site commands are for sim devices only"
        self._site_cmd_counter += 1
        payload = {"cmd_id": f"S{self._site_cmd_counter:06d}", **(extra or {})}
        err = first_error(mqtt_validator("site_cmd"), payload)
        assert err is None, err
        self.out.append(MqttOut(f"twin/{d['site_id']}/{device_id}/cmd/{action}", payload))
        return str(payload["cmd_id"])

    # ------------------------------------------------------------------ BLE tags -> live forklifts

    def _send_ble_tracks(self, to: str | None = None) -> None:
        self._send(BleTracks(seq=self._next_seq(), server_ts_ms=self.clock(), **self.ble.wire()), to)

    def _apply_ble(self, changes: list[ZoneChange]) -> None:
        w = self.world
        for c in changes:
            u = w.entities.get(c.unit_id or "")
            if u is None or u.kind != "forklift":
                if c.tag in self.devices.real_tags:
                    continue  # a real badge (TD-BADGE-xx): shown as its own LIVE device, not a forklift
                if c.first:
                    self.event("warn", f"Tag {c.tag} has no matching forklift", "gateway")
                continue
            if c.zone is None:
                if u.source == "device":
                    self.event("info", f"{u.id}: tag {c.tag} is beyond the calibrated zones, holding position",
                               "gateway", u.id)
                continue
            label = w.node_label(c.zone)
            if u.source != "device":
                u.source = "device"  # from now on only the tag moves it, even if it is mid-pick
                self.event("info", f"{u.id} is now tracked by tag {c.tag} ({label})", "gateway", u.id)
            else:
                self.event("info", f"{u.id}: tag {c.tag} moved to {label}", "gateway", u.id)
            self._device_goal[u.id] = c.zone
            self._drive_device(u.id)

    def _drive_device(self, uid: str) -> None:
        u = self.world.entities[uid]
        goal = self._device_goal[uid]
        if u.busy:
            return  # finish the pallet handling first; tick() retries
        self._device_sent[uid] = goal
        if u.target == goal or (u.node == goal and not u.moving):
            return
        r = self.world.command(uid, goal, "goto", source="device")
        if not r.ok:
            self.event("warn", f"{uid}: can't follow tag to {self.world.node_label(goal)}: {r.reason}", "gateway", uid)

    def _release_device(self, uid: str | None, why: str) -> None:
        u = self.world.entities.get(uid or "")
        self._device_goal.pop(uid or "", None)
        self._device_sent.pop(uid or "", None)
        if u is not None and u.source == "device":
            u.source = "manual"
            self.event("warn", f"{why}; {u.id} is back under manual control", "gateway", u.id)

    # ------------------------------------------------------------------ physical buttons

    def on_short_press(self, button: str) -> None:
        assert button in EXPOSED_BUTTONS
        w = self.world
        forklifts = sorted(f.id for f in w.of_kind("forklift"))
        if button == "BTN1":
            if self.selected in forklifts:
                nxt = forklifts[(forklifts.index(self.selected) + 1) % len(forklifts)]
            else:
                nxt = forklifts[0]
            self.selected = nxt
            self._send(SelectionChanged(seq=self._next_seq(), selected_unit_id=nxt, by="BTN1"))
            self.event("info", f"Selected {nxt}", "BTN1", nxt)
            return
        # BTN0: the selected forklift runs the next step of its task list.
        if self.selected not in forklifts:
            self.event("warn", "BTN0: no forklift selected (press BTN1 to select one)", "BTN0")
            return
        f = w.entities[self.selected or ""]
        if f.source == "device":
            self.event("warn", f"BTN0: {f.id} is tracked by the board", "BTN0", f.id)
            return
        if f.moving or f.busy:
            self.event("warn", f"BTN0: {f.id} is busy ({f.state})", "BTN0", f.id)
            return
        ok, text = planner.run_next_step(w, f, "manual")
        self.event("info" if ok else "warn", text, "BTN0", f.id)

    # ------------------------------------------------------------------ client intents

    def handle_client(self, client_id: str, text: str) -> None:
        try:
            data = json.loads(text)
        except ValueError:
            self.event("error", "Message is not JSON", client_id, to=client_id)
            return
        mtype = data.get("type") if isinstance(data, dict) else None
        if mtype not in CLIENT_TYPES:
            self.event("error", f"Unknown message type {mtype!r}", client_id, to=client_id)
            return
        err = first_error(validator(f"ws/{mtype}"), data)
        if err:
            cmd_id = data.get("cmd_id")
            if isinstance(cmd_id, str) and 0 < len(cmd_id) <= 64:
                self._ack(client_id, cmd_id, mtype, False, f"Invalid message: {err}")
            else:
                self.event("error", f"Invalid {mtype}: {err}", client_id, to=client_id)
            return
        msg = _client_adapter.validate_python(data)
        if isinstance(msg, MoveUnit):
            self._move(client_id, msg)
        elif isinstance(msg, SelectUnit):
            self._select(client_id, msg)
        elif isinstance(msg, LedCommand):
            self._led_command(client_id, msg)
        elif isinstance(msg, ScenarioCommand):
            self._scenario(client_id, msg)
        elif isinstance(msg, AckAlert):
            self._ack_alert(client_id, msg)
        elif isinstance(msg, SafetyCommand):
            self._safety_command(client_id, msg)
        elif isinstance(msg, MachineCommand):
            self._machine_command(client_id, msg)
        elif isinstance(msg, SetSimSpeed):
            self._set_sim_speed(client_id, msg)
        elif isinstance(msg, SetAutoMode):
            self.auto_mode = msg.enabled
            self._auto_mode_dirty = True
            self._ack(client_id, msg.cmd_id, "set_auto_mode", True)
            self.event("info", f"Auto mode {'on' if msg.enabled else 'off'}", client_id)
        self._sync_rule_leds()
        self._drain_world_events()
        self._flush_units()

    def _machine_command(self, client_id: str, m: MachineCommand) -> None:
        pm = self.production.machines.get(m.machine_id)
        if pm is None:
            self._ack(client_id, m.cmd_id, "machine_command", False, f"{m.machine_id} is not a machine")
            return
        if not self.sim_reachable:
            self._ack(client_id, m.cmd_id, "machine_command", False, "Not connected to the MQTT broker")
            return
        self._site_command(pm.device_id, m.action)
        self._ack(client_id, m.cmd_id, "machine_command", True)
        text = {"degrade": "slowly rising vibration injected (simulation)", "restore": "vibration restored (simulation)",
                "maintenance": "maintenance started (simulation)"}[m.action]
        self.event("info", f"{pm.id} {pm.label.lower()}: {text}", client_id, pm.id)

    def _safety_command(self, client_id: str, m: SafetyCommand) -> None:
        now = self.clock()
        by = (m.by or "").strip() or client_id
        reason: str | None = None
        if m.action == "start_evacuation":
            reason = self.safety.start_evacuation(now, (m.reason or "").strip() or "evacuation drill", by)
            text = f"Evacuation started by {by}: {(m.reason or '').strip() or 'evacuation drill'}"
        elif m.action == "end_evacuation":
            hc = self.safety.headcount()
            reason = self.safety.end_evacuation(now)
            text = f"Evacuation ended by {by}" + (f" ({hc['accounted']} of {hc['on_site']} accounted for)" if hc else "")
        else:
            w = self.safety.workers.get(m.worker_id or "")
            if w is None:
                return self._ack(client_id, m.cmd_id, "safety_command", False, f"Unknown worker {m.worker_id}")
            if m.action == "clear_incident":
                reason = self.safety.clear_incident(w.id, now)
                text = f"{w.id}: incident closed by {by}"
            else:
                # Demo: drive the worker's SIMULATED badge. Never possible for a real badge.
                if self.devices.defs[w.badge]["source"] != "sim":
                    return self._ack(client_id, m.cmd_id, "safety_command", False, f"{w.badge} is not a simulated badge")
                if not self.sim_reachable:
                    return self._ack(client_id, m.cmd_id, "safety_command", False, "Not connected to the MQTT broker")
                act = m.action.removeprefix("sim_")
                self._site_command(w.badge, act, {"seconds": 120} if act == "still" else None)
                text = f"Demo: {w.id}'s badge simulates {'a fall' if act == 'fall' else act.replace('_', ' ')} (simulation)"
        self._ack(client_id, m.cmd_id, "safety_command", reason is None, reason)
        if reason is None:
            self.event("warn" if m.action == "start_evacuation" else "info", text, client_id, m.worker_id)
            self._badge_actions()
            self._send_safety()

    # ------------------------------------------------------------------ demo scenario runner (S10)

    def _scenario(self, client_id: str, m: ScenarioCommand) -> None:
        """One demo beat on cue. Beats only drive the simulator and the movement engine."""
        def fail(reason: str) -> None:
            self._ack(client_id, m.cmd_id, "scenario_command", False, reason)
        if m.beat != "reset" and not self.sim_reachable:
            return fail("Not connected to the MQTT broker (the simulator listens there)")
        text = ""
        if m.beat == "degrade":
            self._site_command("MM-01", "degrade")
            text = "Demo: slowly rising vibration injected on M-01 (simulation)"
        elif m.beat == "near_miss":
            # WK-02 walks the outbound lane while a forklift drives in to collect: a near miss.
            candidates = [f for f in self.world.of_kind("forklift")
                          if f.source != "device" and not f.moving and not f.busy and not f.carrying]
            if not candidates:
                return fail("No free forklift (all busy, carrying or tracked by the board)")
            f = min(candidates, key=lambda e: abs(e.x - 95) + abs(e.z - 15))
            pallets = self.world.pallets_at(self.production.outbound_node)
            r = self.world.command(f.id, self.production.outbound_node, "pick" if pallets else "goto",
                                   pallets[0].id if pallets else None, source="manual")
            if not r.ok:
                return fail(r.reason or f"{f.id} can't drive to the factory outbound")
            self._site_command("BG-02", "route", {"route": "outbound"})
            text = f"Demo: {f.id} drives to the factory outbound while WK-02 walks the outbound lane"
        elif m.beat == "visitor":
            self._site_command("BG-04", "route", {"route": "press_visit"})
            text = "Demo: the visitor (WK-04) heads for the press area (simulation)"
        elif m.beat == "cold_door":
            self._site_command("DR-01", "door_open", {"seconds": 150})
            text = "Demo: cold room door held open for 150 s (simulation)"
        elif m.beat == "stale":
            self._site_command("AQ-01", "silence", {"on": True})
            text = "Demo: AQ-01 stops reporting (it goes stale after 15 s, offline after 60 s)"
        elif m.beat == "grid_failure":
            self._site_command("PM-04", "grid_failure")
            text = "Demo: grid failure at the substation incomer; the generator starts and critical zones stay on (simulation)"
        elif m.beat == "gas_leak":
            self._site_command("GD-04", "leak")
            text = "Demo: gas leak in the hazardous materials store (simulation)"
        elif m.beat == "fire_alarm":
            self._site_command("FP-01", "alarm")
            text = "Demo: the warehouse fire panel bridge reports an alarm (simulation)"
        elif m.beat == "compressor_fault":
            self._site_command("CP-01", "fault")
            text = "Demo: the compressor trips, air pressure will fall (simulation)"
        elif m.beat == "reset":
            self.reset()
            self._fire_evac = True  # the panel is still in alarm for a moment: don't start a new evacuation until it has cleared
            self.safety.today = Today()
            now = self.clock()
            self.safety.end_evacuation(now)
            for wk in self.safety.workers.values():
                self.safety.clear_incident(wk.id, now)
            if self.sim_reachable:
                for dev, action, extra in (("MM-01", "restore", None), ("MM-02", "restore", None),
                                           ("BG-02", "route", {"route": "default"}),
                                           ("BG-04", "route", {"route": "default"}),
                                           ("DR-01", "door_close", None), ("AQ-01", "silence", {"on": False}),
                                           ("PM-04", "grid_restore", None), ("GD-04", "clear", None), ("FP-01", "reset", None),
                                           ("CP-01", "restore", None)):
                    self._site_command(dev, action, extra)
            text = "Demo reset: seed world, simulator back to normal"
        self._ack(client_id, m.cmd_id, "scenario_command", True)
        self.event("info", text, client_id)

    def _move(self, client_id: str, m: MoveUnit) -> None:
        r = self.world.command(m.unit_id, m.target_node, m.action, m.pallet_id, source="manual", dry_run=m.dry_run)
        self._ack(client_id, m.cmd_id, "move_unit", r.ok, r.reason, r.path)

    def _select(self, client_id: str, m: SelectUnit) -> None:
        if m.unit_id is not None and m.unit_id not in self.world.entities and m.unit_id not in self.devices.defs:
            self._ack(client_id, m.cmd_id, "select_unit", False, f"Unknown unit {m.unit_id}")
            return
        self._ack(client_id, m.cmd_id, "select_unit", True)
        if m.unit_id != self.selected:
            self.selected = m.unit_id
            self._send(SelectionChanged(seq=self._next_seq(), selected_unit_id=m.unit_id, by=client_id))

    def _led_command(self, client_id: str, m: LedCommand) -> None:
        def reject(reason: str) -> None:
            self._ack(client_id, m.cmd_id, "led_command", False, reason)
        if self.gw.hello is None:
            return reject("Waiting for device")
        if m.led not in self.gw.leds:
            return reject(f"{m.led} is not on this board")
        if m.led in RULE_LEDS:
            return reject(f"{m.led} is automatic: {RULE_LEDS[m.led]}")
        if not self.mqtt_connected:
            return reject("Not connected to the MQTT broker")
        if not self.gw.online:
            return reject("Board is offline")
        self._send_led(m.led, m.on)
        self._ack(client_id, m.cmd_id, "led_command", True)
