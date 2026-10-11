"""Logistics (R3): truck schedules, gate, weighbridge, yard queue, paperwork; raw material reorder; finished-goods
orders; opportunity charging in breaks; inventory; KPIs from events. Used by auto mode (planner.py) and the engine.

A truck's visit: off site → arrival (its schedule slot + a random delay, or, for the supplier, the order's lead
time) → gate check-in → weighbridge (gross weight in = tare + what it carries) → yard queue → dock (forklifts unload
or load it, pallet by pallet) → paperwork → weighbridge out (gross weight out) → gone. Every step is logged with its
time, and the KPIs (dock-to-stock, turnaround, on-time dispatch, schedule adherence, forklift utilisation) are
computed from that log. Weights come from the pallets actually on board, so the weighbridge ticket always matches the
cargo. Times are simulation seconds (world.time); handling times are divided by PACE like the forklifts' own.
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

from .world import PACE, Entity, World, logistics_params, pallet_kg

STAGES = ("offsite", "gate", "weighbridge", "queue", "dock", "paperwork", "departing")
KEEP = 200


@dataclass
class Visit:
    truck: str
    stage: str = "offsite"
    stage_until: float = 0.0
    slot_t: float | None = None          # world time of its schedule slot (None: on demand)
    arrive_t: float | None = None        # world time it actually arrives
    arrived_t: float | None = None
    docked_t: float | None = None
    gross_in_kg: float | None = None
    gross_out_kg: float | None = None
    pallets_in: int = 0
    pallets_out: int = 0


@dataclass
class Order:
    id: str
    pallets: int
    created_t: float
    due_t: float
    shipped: int = 0
    done_t: float | None = None

    @property
    def on_time(self) -> bool | None:
        return None if self.done_t is None else self.done_t <= self.due_t


@dataclass
class Logistics:
    world: World
    rng: random.Random
    hour_of_day: Callable[[], float]
    visits: dict[str, Visit] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    tickets: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=20))
    samples: dict[str, deque[float]] = field(default_factory=lambda: {k: deque(maxlen=KEEP) for k in ("dock_to_stock", "turnaround", "arrival_delay")})
    docked_at_t: dict[str, float] = field(default_factory=dict)      # truck -> when it docked (this visit)
    pallet_truck: dict[str, str] = field(default_factory=dict)       # inbound pallet -> the truck it came on
    busy_s: float = 0.0
    avail_s: float = 0.0
    raw_on_order: bool = False
    next_order_t: float | None = None
    _n_order: int = 0
    notes: list[str] = field(default_factory=list)                  # human-readable events for the engine's log
    dirty: bool = True

    def __post_init__(self) -> None:
        p = logistics_params()
        self.p = p
        self.raw_truck = str(p.v("logistics.raw.truck"))
        for t in self.world.of_kind("truck"):
            v = Visit(t.id)
            if t.state == "docked":
                v.stage, v.arrived_t, v.docked_t = "dock", self.world.time, self.world.time
                self.docked_at_t[t.id] = self.world.time
            elif t.state == "arriving":
                v.stage, v.arrived_t = "queue", self.world.time  # already through the gate in the seed
            self.visits[t.id] = v

    # ------------------------------------------------------------------ draws

    def _draw(self, path: str) -> float:
        lf = self.p.leaf(path)
        a = lf.value
        r = self.rng
        if lf.dist == "lognormal":
            return r.lognormvariate(math.log(float(a["median"])), float(a["sigma_log"]))
        if lf.dist == "exponential":
            return r.expovariate(1 / float(a["mean"]))
        if lf.dist == "uniform":
            return r.uniform(float(a["low"]), float(a["high"]))
        if lf.dist == "normal":
            return r.gauss(float(a["mean"]), float(a["sigma"]))
        raise ValueError(lf.dist)

    def _handling(self, path: str) -> float:
        """A handling time (minutes in the params) in world seconds at the warehouse's PACE."""
        return self._draw(path) * 60 / PACE

    # ------------------------------------------------------------------ schedule

    def _next_slot(self, truck: str, now_t: float) -> float | None:
        sched = self.p.v("logistics.schedule.trucks").get(truck)
        if not sched:
            return None
        h = self.hour_of_day()
        period, offset = float(sched["period_h"]) * 3600, float(sched["offset_min"]) * 60
        since_midnight = h * 3600
        k = math.ceil((since_midnight - offset) / period)
        slot_since_midnight = offset + k * period
        if slot_since_midnight - since_midnight < 60:
            slot_since_midnight += period
        return now_t + (slot_since_midnight - since_midnight) / PACE

    # ------------------------------------------------------------------ tick

    def tick(self, dt: float, shift_phase: str | None = None) -> None:
        w = self.world
        now = w.time
        self.world.opportunity = shift_phase == "break"
        self._consume_log()
        for f in w.of_kind("forklift"):
            if f.meta.get("area") == "raw" or f.source == "device":
                continue
            self.avail_s += dt
            if f.state in ("driving", "carrying", "picking", "loading"):
                self.busy_s += dt
        for t in w.of_kind("truck"):
            v = self.visits.setdefault(t.id, Visit(t.id))
            if t.state == "gone" and v.stage not in ("offsite",):
                v.stage = "offsite"
                v.arrive_t = None
            if v.stage == "offsite" and t.state == "gone" and v.arrive_t is None:
                self._plan_arrival(t, v, now)
            if v.stage == "offsite" and v.arrive_t is not None and now >= v.arrive_t:
                self._arrive(t, v, now)
            elif v.stage == "gate" and now >= v.stage_until:
                v.stage, v.stage_until = "weighbridge", now + self._handling("logistics.gate.weighbridge_min")
                self.dirty = True
            elif v.stage == "weighbridge" and now >= v.stage_until:
                v.gross_in_kg = self.gross_kg(t)
                v.pallets_in = len(t.cargo or [])
                self._ticket(t, "in", v.gross_in_kg, now)
                v.stage = "queue"
                self.dirty = True
            elif v.stage == "queue" and t.docked_at is not None:
                v.stage, v.docked_t = "dock", now
            elif v.stage == "paperwork" and now >= v.stage_until:
                v.stage = "departing"
                self.dirty = True
        self._orders(now)
        self._reorder(now)

    def _plan_arrival(self, t: Entity, v: Visit, now: float) -> None:
        if t.id == self.raw_truck:
            return  # the supplier only comes when raw material is ordered (_reorder)
        slot = self._next_slot(t.id, now)
        if slot is None:
            return
        delay = self._draw("logistics.schedule.delay_min") * 60 / PACE
        v.slot_t, v.arrive_t = slot, slot + delay
        self.dirty = True

    def _arrive(self, t: Entity, v: Visit, now: float) -> None:
        if t.id == self.raw_truck:
            made = self.world.load_raw_cargo(t.id, int(t.capacity or 4))
            t.inbound = True
            self.raw_on_order = False
            self.notes.append(f"{t.id} arrives with {len(made)} raw material pallets (ordered at the reorder point)")
        t.state = "arriving"
        v.stage, v.arrived_t, v.stage_until = "gate", now, now + self._handling("logistics.gate.checkin_min")
        if v.slot_t is not None:
            self.samples["arrival_delay"].append((now - v.slot_t) * PACE / 60)
        self.notes.append(f"{t.id} at the gate for check-in")
        self.dirty = True

    def ready_for_dock(self, t: Entity) -> bool:
        v = self.visits.get(t.id)
        return v is not None and v.stage == "queue"

    def request_departure(self, t: Entity) -> bool:
        """The planner wants this docked truck to leave. Starts the paperwork; True once it may drive off."""
        v = self.visits.get(t.id)
        if v is None:
            return True
        now = self.world.time
        if v.stage == "dock":
            v.stage, v.stage_until = "paperwork", now + self._handling("logistics.gate.paperwork_min")
            self.notes.append(f"{t.id}: paperwork before departure")
            self.dirty = True
            return False
        return v.stage == "departing"

    def departed(self, t: Entity) -> None:
        """Called when the depart command is accepted: the truck crosses the weighbridge on its way out."""
        v = self.visits.get(t.id)
        if v is None:
            return
        now = self.world.time
        v.gross_out_kg, v.pallets_out = self.gross_kg(t), len(t.cargo or [])
        self._ticket(t, "out", v.gross_out_kg, now)
        if v.arrived_t is not None:
            self.samples["turnaround"].append((now - v.arrived_t) * PACE / 60)
        v.stage, v.arrive_t, v.slot_t = "offsite", None, None
        self.dirty = True

    # ------------------------------------------------------------------ weights

    def gross_kg(self, t: Entity) -> float:
        tare = float(self.p.v("logistics.trucks.tare_kg").get(t.id, 0))
        return tare + sum(pallet_kg(self.world.entities.get(pid)) for pid in (t.cargo or []))

    def _ticket(self, t: Entity, direction: str, kg: float, now: float) -> None:
        self.tickets.appendleft({"truck": t.id, "direction": direction, "gross_kg": round(kg), "tare_kg": round(float(self.p.v("logistics.trucks.tare_kg").get(t.id, 0))),
                                 "pallets": len(t.cargo or []), "t": now, "wall_ms": int(time.time() * 1000)})
        self.notes.append(f"Weighbridge {direction}: {t.id} {kg:,.0f} kg gross ({len(t.cargo or [])} pallets)")

    # ------------------------------------------------------------------ events from the world

    def _consume_log(self) -> None:
        w = self.world
        for kind, d in w.log:
            if kind == "truck_docked":
                self.docked_at_t[d["truck"]] = d["t"]
                t = w.entities.get(d["truck"])
                if t is not None and t.inbound:
                    for pid in d["pallets"]:
                        self.pallet_truck[pid] = d["truck"]
            elif kind == "pallet_dropped" and d["node_type"] == "rack_slot":
                truck = self.pallet_truck.pop(d["pallet"], None)
                if truck is not None and truck in self.docked_at_t:
                    self.samples["dock_to_stock"].append((d["t"] - self.docked_at_t[truck]) * PACE / 60)
                    self.dirty = True
            elif kind == "truck_gone":
                self._ship(d["delivered"], d["t"])
        w.log.clear()

    # ------------------------------------------------------------------ orders

    def _orders(self, now: float) -> None:
        if self.next_order_t is None:
            self.next_order_t = now + self._draw("logistics.orders.interarrival_min") * 60 / PACE
        if now >= self.next_order_t:
            self._n_order += 1
            n = int(self._draw("logistics.orders.pallets"))
            due = now + float(self.p.v("logistics.orders.due_h")) * 3600 / PACE
            self.orders.append(Order(f"SO-{self._n_order:04d}", n, now, due))
            self.notes.append(f"Order SO-{self._n_order:04d}: {n} pallet{'s' if n > 1 else ''} of finished goods")
            self.next_order_t = now + self._draw("logistics.orders.interarrival_min") * 60 / PACE
            del self.orders[:-KEEP]
            self.dirty = True

    def open_orders(self) -> list[Order]:
        return [o for o in self.orders if o.done_t is None]

    def fg_wanted(self) -> int:
        return sum(o.pallets - o.shipped for o in self.open_orders())

    def _ship(self, delivered: list[str], now: float) -> None:
        n = len(delivered)
        for o in self.open_orders():
            if n <= 0:
                break
            take = min(n, o.pallets - o.shipped)
            o.shipped += take
            n -= take
            if o.shipped >= o.pallets:
                o.done_t = now
                self.notes.append(f"{o.id} dispatched {'on time' if o.on_time else 'late'}")
        self.dirty = True

    # ------------------------------------------------------------------ raw material

    def raw_position(self) -> int:
        """Raw pallets on hand or on the way: raw store + press infeed + on forklifts + on the supplier's inbound truck."""
        w = self.world
        n = sum(1 for p in w.of_kind("pallet") if p.id.startswith("RM-") and (p.node is not None or (p.holder or "").startswith("FL-")))
        t = w.entities.get(self.raw_truck)
        if t is not None and t.inbound and t.state != "gone":
            n += len(t.cargo or [])
        return n

    def _reorder(self, now: float) -> None:
        t = self.world.entities.get(self.raw_truck)
        v = self.visits.get(self.raw_truck)
        if t is None or v is None or self.raw_on_order or t.state != "gone":
            return
        rop = int(self.p.f("logistics.raw.reorder_point_pallets"))
        pos = self.raw_position()
        if pos <= rop:
            self.raw_on_order = True
            lead = self._draw("logistics.raw.lead_time_min")
            v.arrive_t, v.slot_t = now + lead * 60 / PACE, None
            self.notes.append(f"Raw material at {pos} pallets (reorder point {rop}): {t.id} called off, due in about {lead:.0f} min")
            self.dirty = True

    # ------------------------------------------------------------------ inventory and KPIs

    def inventory(self) -> dict[str, dict[str, int]]:
        """Pallets by SKU group and where they are. Counted from the world's pallets, so never negative."""
        w = self.world
        out: dict[str, dict[str, int]] = {}
        for p in w.of_kind("pallet"):
            group = "RM" if p.id.startswith("RM-") else "FG" if p.id.startswith("FG-") else "SKU"
            if p.holder is not None:
                where = "on_truck" if p.holder.startswith("TR-") else "on_forklift"
            else:
                n = w.graph.nodes.get(p.node or "")
                where = "rack" if n is not None and n.type == "rack_slot" else (p.node or "unknown").lower()
            g = out.setdefault(group, {})
            g[where] = g.get(where, 0) + 1
        return out

    def kpis(self) -> dict[str, Any]:
        def mean(k: str) -> float | None:
            s = self.samples[k]
            return None if not s else round(sum(s) / len(s), 1)
        done = [o for o in self.orders if o.done_t is not None]
        win = float(self.p.v("logistics.schedule.on_time_window_min"))
        delays = self.samples["arrival_delay"]
        return {"dock_to_stock_min": mean("dock_to_stock"), "turnaround_min": mean("turnaround"),
                "on_time_dispatch": None if not done else round(sum(1 for o in done if o.on_time) / len(done), 3),
                "orders_shipped": len(done), "orders_open": len(self.open_orders()),
                "arrivals_on_schedule": None if not delays else round(sum(1 for d in delays if abs(d) <= win) / len(delays), 3),
                "forklift_utilisation": None if self.avail_s <= 0 else round(self.busy_s / self.avail_s, 3)}

    def wire(self) -> dict[str, Any]:
        w = self.world
        trucks = []
        for t in w.of_kind("truck"):
            v = self.visits.get(t.id, Visit(t.id))
            trucks.append({"id": t.id, "stage": v.stage, "state": t.state, "pallets": len(t.cargo or []),
                           "eta_min": None if v.arrive_t is None or v.stage != "offsite" else round(max(0.0, v.arrive_t - w.time) * PACE / 60, 1),
                           "gross_in_kg": None if v.gross_in_kg is None else round(v.gross_in_kg), "gross_out_kg": None if v.gross_out_kg is None else round(v.gross_out_kg)})
        rop = int(self.p.f("logistics.raw.reorder_point_pallets"))
        return {"kpis": self.kpis(), "trucks": trucks, "inventory": self.inventory(),
                "orders": [{"id": o.id, "pallets": o.pallets, "shipped": o.shipped, "due_in_min": round((o.due_t - w.time) * PACE / 60, 1),
                            "done": o.done_t is not None, "on_time": o.on_time} for o in self.orders[-12:]][::-1],
                "tickets": [{k: v for k, v in tk.items() if k != "t"} for tk in self.tickets][:10],
                "raw": {"position": self.raw_position(), "reorder_point": rop, "on_order": self.raw_on_order},
                "batteries": [{"id": f.id, "pct": round(f.battery or 0, 1), "ah_used": round(f.ah_used, 2), "ah_charged": round(f.ah_charged, 2),
                               "charging": f.state == "charging", "reason": f.charge_reason} for f in w.of_kind("forklift")],
                "pace": PACE}
