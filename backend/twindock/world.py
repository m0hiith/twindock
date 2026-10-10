"""World state and movement engine.

Everything here is synchronous and driven by tick(dt), so it can be tested without a network or
a clock. The engine (engine.py) owns a World and turns its changes into WebSocket messages.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

from .graph import Graph
from .models import Action, Layout, Node, PlanStep, Source, Unit

# Demo pace: the whole motion model is played this many times faster than real life, so a demo
# doesn't wait half a minute for a truck to reverse into a bay. Speeds and turn rates scale by
# PACE, accelerations by PACE^2 and handling times by 1/PACE, so every move follows exactly the
# same path and speed curve as at real pace, just sooner. TWINDOCK_PACE=1 gives real speeds.
PACE = float(os.environ.get("TWINDOCK_PACE", "2.5"))

# Real-pace values: forklift 2.2 m/s and truck 3 m/s from CLAUDE.md. Accel/turn values are chosen
# to look plausible at isometric zoom: a forklift reaches top speed in under 2 s; a truck turns
# noticeably slower than a forklift.
SPEED = {"forklift": 2.2 * PACE, "truck": 3.0 * PACE}
TRUCK_REVERSE_SPEED = 1.2 * PACE   # backing into a bay is done slowly
ACCEL = 1.2 * PACE**2              # m/s^2, also used as the braking rate before the final node
TURN_RATE = {"forklift": 2.5 * PACE, "truck": 0.9 * PACE}  # rad/s
TURN_SLOW_ANGLE = 0.6              # rad; with a bigger heading error the unit crawls while it turns
TURN_SLOW_SPEED = 0.5 * PACE       # m/s
CREEP_SPEED = 0.3 * PACE           # m/s floor so braking never stalls just short of a node

PICK_S = 3.0 / PACE                # fork handling time for pick and drop
LOAD_S = 4.0 / PACE                # driving into the trailer, setting down, backing out
# Demo time scale: battery moves ~20x faster than a real shift so it visibly changes in a demo.
# Nonstop driving drains ~10 %/min, so drain stops at a floor: no forklift can be stranded at
# 0% mid-demo, however long it runs. Auto mode sends forklifts to charge below 25%.
CHARGE_PCT_PER_S = 1.5      # real: about an hour for a full charge
DRAIN_PCT_PER_M = 0.08
BATTERY_FLOOR_PCT = 15.0
FORK_OFFSET_M = 1.1         # carried pallet sits this far ahead of the forklift centre

BAY1_DOCK_NODE = "DOCK_1"   # LED0 rule: on while a truck is docked at Bay 1
FINISHED_PREFIX = "FG-"     # finished-goods pallets made by the FAC-01 line; delivered when their truck departs


def wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


@dataclass
class Step:
    node: str
    action: Action
    pallet_id: str | None = None


@dataclass
class Entity:
    id: str
    kind: str
    state: str
    x: float
    z: float
    heading: float = 0.0
    source: Source = "manual"
    label: str | None = None
    node: str | None = None
    meta: dict[str, str | float | bool] = field(default_factory=dict)
    # movers
    speed: float = 0.0
    path: list[str] = field(default_factory=list)   # remaining nodes, next one first
    prev_node: str | None = None                    # last node passed (for lane direction)
    target: str | None = None
    action: Action | None = None                    # what to do at target; kept until done
    action_left: float = 0.0                        # seconds of pick/drop/load remaining
    action_pallet: str | None = None
    idle_since: float = 0.0
    plan: list[Step] = field(default_factory=list)
    # forklifts
    battery: float | None = None
    carrying: str | None = None
    # trucks
    docked_at: str | None = None
    cargo: list[str] | None = None
    capacity: int = 0
    inbound: bool = False                           # cargo is to be unloaded, not delivered
    # pallets
    holder: str | None = None
    spot: int | None = None
    claimed_by: str | None = None
    # docks
    fixed_state: str | None = None                  # "maintenance" from the seed

    @property
    def moving(self) -> bool:
        return bool(self.path)

    @property
    def busy(self) -> bool:
        return self.action_left > 0


@dataclass
class MoveResult:
    ok: bool
    reason: str | None = None
    path: list[str] | None = None
    action: Action | None = None
    target: str | None = None
    pallet_id: str | None = None


def _fail(reason: str) -> MoveResult:
    return MoveResult(False, reason)


class World:
    def __init__(self, layout: Layout, graph: Graph) -> None:
        self.layout = layout
        self.graph = graph
        self.dock_by_node = {d.node: d for d in layout.docks}
        self.dock_by_bay = {d.bay_node: d for d in layout.docks}
        self.charger_by_node = {c.node: c for c in layout.chargers}
        self.events: list[tuple[str, str, str | None]] = []  # (level, text, unit_id), drained by the engine
        self.removed: list[str] = []  # unit ids that left the world (delivered pallets), drained by the engine
        self.entities: dict[str, Entity] = {}
        self.time = 0.0
        self.gateway_state = "waiting"
        self.reset()

    # ------------------------------------------------------------------ setup

    def reset(self) -> None:
        L, g = self.layout, self.graph
        self.time = 0.0
        self.events.clear()
        ents: dict[str, Entity] = {}
        for f in L.seed.forklifts:
            n = g.nodes[f.node]
            ents[f.id] = Entity(f.id, "forklift", "charging" if f.charging else "idle", n.x, n.z, f.heading_rad,
                                label=f.id, node=n.id, prev_node=n.id, meta=dict(f.meta), battery=f.battery_pct,
                                plan=[Step(s.node, s.action) for s in f.plan],
                                action="charge" if f.charging else None, target=n.id if f.charging else None)
        for t in L.seed.trucks:
            n = g.nodes[t.node]
            meta: dict[str, str | float | bool] = {**t.meta, "capacity": t.capacity}
            e = Entity(t.id, "truck", t.state, n.x, n.z, t.heading_rad, label=t.id, node=n.id, prev_node=n.id,
                       meta=meta, cargo=[], capacity=t.capacity, inbound=t.inbound)
            if t.state == "docked":
                e.docked_at = self.dock_by_bay[t.node].node
            ents[t.id] = e
        for p in L.seed.pallets:
            e = Entity(p.id, "pallet", "stored", 0, 0, label=p.meta.get("sku"), meta=dict(p.meta))
            if p.at in ents:
                truck = ents[p.at]
                assert truck.cargo is not None
                truck.cargo.append(p.id)
                e.holder = truck.id
            else:
                e.node = p.at
                e.spot = sum(1 for o in ents.values() if o.kind == "pallet" and o.node == p.at)
            ents[p.id] = e
        for d in L.docks:
            n = g.nodes[d.node]
            seeded = L.seed.dock_states.get(d.id)
            ents[d.id] = Entity(d.id, "dock", "available", n.x, n.z, math.pi / 2, label=d.label, node=n.id,
                                meta={"door": d.door, "bay_node": d.bay_node},
                                fixed_state="maintenance" if seeded == "maintenance" else None)
        for r in L.racks:
            extra = r.model_extra or {}
            ents[r.id] = Entity(r.id, "rack", "available", float(extra["x"]) + float(extra["w"]) / 2,
                                float(extra["z"]) + float(extra["d"]) / 2, label=f"Rack row {r.row}",
                                meta={"row": r.row, "slots": len(r.slots)})
        for c in L.chargers:
            n = g.nodes[c.node]
            ents[c.id] = Entity(c.id, "charger", "available", n.x, n.z, label=c.label, node=n.id)
        gw = L.gateway
        ents[gw.id] = Entity(gw.id, "gateway", self.gateway_state, gw.x, gw.z, source="device", label=gw.label,
                             meta={"ble_range_m": gw.ble_range_m})
        self.entities = ents
        self._update_derived()

    # ------------------------------------------------------------------ queries

    def of_kind(self, kind: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == kind]

    def node_label(self, node_id: str | None) -> str:
        if node_id is None:
            return "the aisle"
        n = self.graph.nodes[node_id]
        return n.label or "the aisle"

    def pallets_at(self, node_id: str) -> list[Entity]:
        ps = [e for e in self.entities.values() if e.kind == "pallet" and e.holder is None and e.node == node_id]
        return sorted(ps, key=lambda p: p.spot or 0)

    def truck_at_dock(self, dock_node: str) -> Entity | None:
        for t in self.of_kind("truck"):
            if t.docked_at == dock_node:
                return t
        return None

    def bay1_occupied(self) -> bool:
        return self.truck_at_dock(BAY1_DOCK_NODE) is not None

    def free_spots(self, node: Node, exclude: str | None = None) -> int:
        dropping = sum(1 for f in self.of_kind("forklift")
                       if f.id != exclude and f.action == "drop" and f.target == node.id)
        return len(node.spots) - len(self.pallets_at(node.id)) - dropping

    def truck_room(self, truck: Entity, exclude: str | None = None) -> int:
        assert truck.cargo is not None
        dock = truck.docked_at
        incoming = sum(1 for f in self.of_kind("forklift") if f.id != exclude and dock is not None and (
            (f.action == "load" and f.target == dock) or (f.plan and f.plan[0].action == "load" and f.plan[0].node == dock)))
        return truck.capacity - len(truck.cargo) - incoming

    def charger_taken_by(self, node_id: str, exclude: str) -> str | None:
        for f in self.of_kind("forklift"):
            if f.id == exclude:
                continue
            if (f.node == node_id and not f.moving) or (f.action == "charge" and f.target == node_id):
                return f.id
        return None

    def _start_node(self, u: Entity) -> str:
        if u.node is not None:
            return u.node
        return u.path[0]

    # ------------------------------------------------------------------ move validation

    def plan_move(self, unit_id: str, target: str, action: Action = "goto", pallet_id: str | None = None,
                  by_device: bool = False) -> MoveResult:
        """Validate a move and return the planned path. Never mutates state.
        by_device: the move comes from the unit's own BLE tag, the only thing that may move it."""
        u = self.entities.get(unit_id)
        if u is None:
            return _fail(f"Unknown unit {unit_id}")
        if u.kind not in ("forklift", "truck"):
            return _fail(f"{u.label or u.id} can't move")
        if u.source == "device" and not by_device:
            return _fail(f"{u.id} is tracked by the board; manual moves are disabled")
        node = self.graph.nodes.get(target)
        if node is None:
            return _fail(f"Unknown destination {target}")
        if u.busy:
            return _fail(f"{u.id} is busy ({u.state})")
        if u.kind == "truck":
            return self._plan_truck(u, node, action)
        return self._plan_forklift(u, node, action, pallet_id)

    def _route(self, u: Entity, goal: str, action: Action, pallet_id: str | None = None) -> MoveResult:
        kind = "truck" if u.kind == "truck" else "forklift"
        start = self._start_node(u)
        path = self.graph.shortest_path(kind, start, goal)
        if path is None:
            return _fail(f"No route from {self.node_label(start)} to {self.node_label(goal)}")
        return MoveResult(True, path=path, action=action, target=goal, pallet_id=pallet_id)

    def _plan_forklift(self, u: Entity, node: Node, action: Action, pallet_id: str | None) -> MoveResult:
        label = self.node_label(node.id)
        if not self.graph.reachable_by("forklift", node.id):
            return _fail(f"Forklifts can't drive to {label}")
        if action == "goto" and node.type == "charger":
            action = "charge"
        if action in ("dock", "depart"):
            return _fail("Only trucks dock or depart")

        if action == "pick":
            if u.carrying:
                return _fail(f"{u.id} is already carrying {u.carrying}")
            if node.type in ("rack_slot", "zone"):
                candidates = self.pallets_at(node.id)
            elif node.type == "dock":
                truck = self.truck_at_dock(node.id)
                if truck is None:
                    return _fail(f"No truck docked at {label}")
                assert truck.cargo is not None
                candidates = [self.entities[p] for p in truck.cargo]
            else:
                return _fail(f"Nothing to pick at {label}")
            if pallet_id is not None:
                p = self.entities.get(pallet_id)
                if p is None or p.kind != "pallet":
                    return _fail(f"Unknown pallet {pallet_id}")
                if p.holder is not None and self.entities[p.holder].kind == "forklift":
                    return _fail(f"{p.id} is already carried by {p.holder}")
                if p not in candidates:
                    return _fail(f"{p.id} is not at {label}")
                if p.claimed_by not in (None, u.id):
                    return _fail(f"{p.id} is already claimed by {p.claimed_by}")
            else:
                free = [p for p in candidates if p.claimed_by in (None, u.id)]
                if not free:
                    return _fail(f"No free pallet at {label}")
                p = free[0]
            return self._route(u, node.id, action, p.id)

        if action == "drop":
            if not u.carrying:
                return _fail(f"{u.id} is not carrying anything")
            if node.type not in ("rack_slot", "zone"):
                return _fail(f"Pallets can only be dropped in a rack slot or zone, not {label}")
            if self.free_spots(node, exclude=u.id) <= 0:
                return _fail(f"{label} is full")
            return self._route(u, node.id, action)

        if action == "load":
            if not u.carrying:
                return _fail(f"{u.id} is not carrying anything")
            if node.type != "dock":
                return _fail(f"Load at a dock, not {label}")
            truck = self.truck_at_dock(node.id)
            if truck is None:
                return _fail(f"No truck docked at {label}")
            if self.truck_room(truck, exclude=u.id) <= 0:
                return _fail(f"{truck.id} is full")
            return self._route(u, node.id, action)

        if action == "charge":
            if node.type != "charger":
                return _fail(f"{label} is not a charger")
            taken = self.charger_taken_by(node.id, exclude=u.id)
            if taken:
                return _fail(f"{label} is in use by {taken}")
            return self._route(u, node.id, action)

        return self._route(u, node.id, "goto")

    def _plan_truck(self, u: Entity, node: Node, action: Action) -> MoveResult:
        if node.type == "dock":
            node = self.graph.nodes[self.dock_by_node[node.id].bay_node]
        if node.type == "bay":
            inferred: Action = "dock"
        elif node.type in ("gate", "exit"):
            inferred = "depart"
        else:
            return _fail("Trucks can only go to a dock or the gate")
        if action not in ("goto", inferred):
            return _fail(f"A truck can't {action} at {self.node_label(node.id)}")
        if u.state == "loading":
            return _fail(f"{u.id} is being loaded")

        if inferred == "dock":
            dock = self.dock_by_bay[node.id]
            dock_ent = self.entities[dock.id]
            if dock_ent.fixed_state == "maintenance":
                return _fail(f"{dock.label} is under maintenance")
            if u.docked_at == dock.node:
                return _fail(f"{u.id} is already docked at {dock.label}")
            for t in self.of_kind("truck"):
                if t.id == u.id:
                    continue
                if t.docked_at == dock.node:
                    return _fail(f"{dock.label} is occupied by {t.id}")
                if t.action == "dock" and t.target == node.id:
                    return _fail(f"{dock.label} is reserved for {t.id}")
            return self._route(u, node.id, "dock")

        if u.state == "gone":
            return _fail(f"{u.id} has already left the site")
        # The gate is the visible target; the truck then drives on to the exit road and is "gone".
        return self._route(u, self.layout.exit_node, "depart")

    # ------------------------------------------------------------------ commands

    def command(self, unit_id: str, target: str, action: Action = "goto", pallet_id: str | None = None,
                source: Source = "manual", dry_run: bool = False) -> MoveResult:
        r = self.plan_move(unit_id, target, action, pallet_id, by_device=source == "device")
        if not r.ok or dry_run:
            return r
        assert r.path is not None and r.action is not None and r.target is not None
        u = self.entities[unit_id]
        u.source = source
        for p in self.of_kind("pallet"):
            if p.claimed_by == u.id and p.id != r.pallet_id:
                p.claimed_by = None
        if r.pallet_id:
            self.entities[r.pallet_id].claimed_by = u.id
        u.action, u.target, u.action_pallet = r.action, r.target, r.pallet_id
        if u.node is not None:
            u.prev_node = u.node
            u.path = r.path[1:]
        else:
            u.path = list(r.path)
        if u.path:
            u.node = None
        if u.kind == "truck":
            u.docked_at = None
            u.state = "arriving" if r.action == "dock" else "departing"
        else:
            u.state = "carrying" if u.carrying else "driving"
        if not u.path:
            self._arrive(u)
        self._update_derived()
        return r

    # ------------------------------------------------------------------ simulation

    def tick(self, dt: float) -> None:
        self.time += dt
        for u in list(self.entities.values()):  # a departing truck can deliver (remove) pallets mid-loop
            if u.kind not in ("forklift", "truck"):
                continue
            if u.path:
                self._drive(u, dt)
            elif u.action_left > 0:
                u.action_left -= dt
                if u.action_left <= 0:
                    self._finish_action(u)
            elif u.state == "charging":
                assert u.battery is not None
                u.battery = min(100.0, u.battery + CHARGE_PCT_PER_S * dt)
                if u.battery >= 100.0:
                    u.state, u.action, u.idle_since = "idle", None, self.time
        self._update_derived()

    def _drive(self, u: Entity, dt: float) -> None:
        g = self.graph
        nxt = g.nodes[u.path[0]]
        reverse = u.prev_node is not None and g.is_reverse(u.prev_node, nxt.id)
        dx, dz = nxt.x - u.x, nxt.z - u.z
        if math.hypot(dx, dz) > 1e-6:
            travel = math.atan2(dz, dx)  # x east, z south: atan2 gives 0 = east, +pi/2 = south
            desired = wrap(travel + math.pi) if reverse else travel
            err = wrap(desired - u.heading)
            turn = TURN_RATE[u.kind] * dt
            u.heading = wrap(u.heading + max(-turn, min(turn, err)))
        else:
            err = 0.0
        vmax = TRUCK_REVERSE_SPEED if reverse else SPEED[u.kind]
        if abs(err) > TURN_SLOW_ANGLE:
            vmax = min(vmax, TURN_SLOW_SPEED)
        remaining = math.hypot(dx, dz) + g.path_length(u.path)
        vmax = max(CREEP_SPEED, min(vmax, math.sqrt(2 * ACCEL * remaining)))
        u.speed = min(vmax, u.speed + ACCEL * dt) if u.speed < vmax else vmax

        move = u.speed * dt
        moved = 0.0
        while move > 1e-9 and u.path:
            n = g.nodes[u.path[0]]
            ddx, ddz = n.x - u.x, n.z - u.z
            d = math.hypot(ddx, ddz)
            if move >= d:
                u.x, u.z = n.x, n.z
                move -= d
                moved += d
                u.prev_node = u.path.pop(0)
            else:
                u.x += ddx / d * move
                u.z += ddz / d * move
                moved += move
                move = 0.0
        if u.kind == "forklift" and u.battery is not None:
            u.battery = max(min(u.battery, BATTERY_FLOOR_PCT), u.battery - DRAIN_PCT_PER_M * moved)
        if not u.path:
            u.speed = 0.0
            u.node = u.prev_node
            self._arrive(u)

    def _arrive(self, u: Entity) -> None:
        a = u.action
        if u.kind == "truck":
            if a == "dock" and u.node in self.dock_by_bay:
                u.state, u.docked_at = "docked", self.dock_by_bay[u.node].node
                u.heading = math.pi / 2  # parked square to the door, cab facing the yard
            elif a == "depart":
                u.state = "gone"
                assert u.cargo is not None
                # Finished goods from the factory (FG-..) are delivered and leave the world; any other
                # cargo comes back with the truck and is unloaded (the warehouse's closed loop).
                delivered = [p for p in u.cargo if p.startswith(FINISHED_PREFIX)]
                for pid in delivered:
                    self.entities.pop(pid, None)
                    self.removed.append(pid)
                u.cargo = [p for p in u.cargo if not p.startswith(FINISHED_PREFIX)]
                if delivered:
                    self.events.append(("info", f"{u.id} delivered {len(delivered)} finished pallet"
                                        f"{'s' if len(delivered) > 1 else ''} from FAC-01", u.id))
                u.inbound = bool(u.cargo)
            u.action, u.target, u.idle_since = None, None, self.time
            return

        if a == "pick":
            p = self.entities.get(u.action_pallet or "")
            ok = p is not None and (
                (p.holder is None and p.node == u.node) or
                (p.holder is not None and self.entities[p.holder].docked_at == u.node))
            if ok:
                u.state, u.action_left = "picking", PICK_S
                return
            self._abort(u, f"{u.id}: pallet {u.action_pallet} is no longer at {self.node_label(u.node)}")
        elif a == "drop":
            node = self.graph.nodes[u.node or ""]
            if self.free_spots(node, exclude=u.id) > 0:
                u.state, u.action_left = "picking", PICK_S
                return
            self._abort(u, f"{u.id}: {self.node_label(u.node)} is full, still holding {u.carrying}")
        elif a == "load":
            truck = self.truck_at_dock(u.node or "")
            if truck is not None and truck.cargo is not None and len(truck.cargo) < truck.capacity:
                u.state, u.action_left = "loading", LOAD_S
                return
            self._abort(u, f"{u.id}: no truck with room at {self.node_label(u.node)}, still holding {u.carrying}")
        elif a == "charge":
            u.state = "charging"
            return
        else:
            u.action, u.target = None, None
            u.state = "carrying" if u.carrying else "idle"
            u.idle_since = self.time

    def _abort(self, u: Entity, text: str) -> None:
        self.events.append(("warn", text, u.id))
        if u.action_pallet and self.entities[u.action_pallet].claimed_by == u.id:
            self.entities[u.action_pallet].claimed_by = None
        u.action, u.target, u.action_pallet = None, None, None
        u.state = "carrying" if u.carrying else "idle"
        u.idle_since = self.time

    def _finish_action(self, u: Entity) -> None:
        u.action_left = 0.0
        a = u.action
        if a == "pick":
            p = self.entities[u.action_pallet or ""]
            if p.holder is not None:  # unloading from a truck
                truck = self.entities[p.holder]
                assert truck.cargo is not None
                truck.cargo.remove(p.id)
                if not truck.cargo:
                    truck.inbound = False
            p.holder, p.node, p.spot, p.claimed_by = u.id, None, None, None
            u.carrying = p.id
        elif a == "drop" and u.carrying:
            node = self.graph.nodes[u.node or ""]
            used = {q.spot for q in self.pallets_at(node.id)}
            p = self.entities[u.carrying]
            p.holder, p.node, p.spot = None, node.id, next(i for i in range(len(node.spots)) if i not in used)
            u.carrying = None
        elif a == "load" and u.carrying:
            truck = self.truck_at_dock(u.node or "")
            p = self.entities[u.carrying]
            if truck is not None and truck.cargo is not None:
                truck.cargo.append(p.id)
                p.holder = truck.id
                u.carrying = None
            else:
                self.events.append(("warn", f"{u.id}: truck left before {p.id} was loaded", u.id))
        u.action, u.target, u.action_pallet = None, None, None
        u.state = "carrying" if u.carrying else "idle"
        u.idle_since = self.time

    # ------------------------------------------------------------------ derived state and tasks

    def _update_derived(self) -> None:
        g = self.graph
        handling = {f.node: f for f in self.of_kind("forklift")
                    if f.busy and f.action in ("pick", "load") and f.node in self.dock_by_node}
        for t in self.of_kind("truck"):
            if t.docked_at is not None and t.state in ("docked", "loading"):
                t.state = "loading" if t.docked_at in handling else "docked"
        for p in self.of_kind("pallet"):
            if p.holder is not None:
                h = self.entities[p.holder]
                if h.kind == "forklift":
                    p.x = h.x + math.cos(h.heading) * FORK_OFFSET_M
                    p.z = h.z + math.sin(h.heading) * FORK_OFFSET_M
                    p.state = "carried"
                else:
                    p.x, p.z, p.state = h.x, h.z, "loaded"
                p.heading = h.heading
            elif p.node is not None:
                n = g.nodes[p.node]
                p.x, p.z = n.spots[p.spot or 0]
                p.heading = 0.0
                p.state = "stored" if n.type == "rack_slot" else "staged"
        for d in self.layout.docks:
            e = self.entities[d.id]
            truck = self.truck_at_dock(d.node)
            if e.fixed_state:
                e.state = e.fixed_state
            else:
                e.state = "occupied" if truck else "available"
        for c in self.layout.chargers:
            e = self.entities[c.id]
            e.state = "occupied" if self.charger_taken_by(c.node, exclude="") else "available"
        for r in self.layout.racks:
            used = sum(1 for s in r.slots if self.pallets_at(s))
            self.entities[r.id].state = "full" if used == len(r.slots) else "available"
        self.entities[self.layout.gateway.id].state = self.gateway_state

    def add_entity(self, e: Entity) -> None:
        """Site-twin units (machines, workers) that are not part of the warehouse seed."""
        self.entities[e.id] = e

    def spawn_pallet(self, node_id: str, meta: dict[str, str | float | bool], source: Source = "sim") -> str | None:
        """New finished-goods pallet at a zone node. Returns its id, or None if the node is full or
        every FG id is in use."""
        node = self.graph.nodes[node_id]
        if self.free_spots(node) <= 0:
            return None
        pid = next((f"{FINISHED_PREFIX}{i:02d}" for i in range(1, 100) if f"{FINISHED_PREFIX}{i:02d}" not in self.entities), None)
        if pid is None:
            return None
        used = {p.spot for p in self.pallets_at(node_id)}
        e = Entity(pid, "pallet", "staged", node.x, node.z, label=str(meta.get("sku", pid)), node=node_id, source=source,
                   meta=dict(meta), spot=next(i for i in range(len(node.spots)) if i not in used))
        self.entities[pid] = e
        self._update_derived()
        return pid

    def task_text(self, u: Entity) -> str:
        nl = self.node_label
        if u.kind == "forklift":
            p = u.carrying or u.action_pallet
            if u.state == "charging":
                return "Charging"
            if u.state == "picking":
                return f"Picking {p}" if u.action == "pick" else f"Putting {p} away at {nl(u.node)}"
            if u.state == "loading":
                truck = self.truck_at_dock(u.node or "")
                return f"Loading {p} onto {truck.id if truck else 'truck'}"
            if u.moving:
                dest = nl(u.target)
                return {"pick": f"Going to pick at {dest}", "drop": f"Carrying {p} to {dest}",
                        "load": f"Taking {p} to {dest}", "charge": f"Going to charge at {dest}"}.get(
                    u.action or "", f"Carrying {p} to {dest}" if u.carrying else f"Driving to {dest}")
            return f"Holding {u.carrying} at {nl(u.node)}" if u.carrying else f"Idle at {nl(u.node)}"
        if u.kind == "truck":
            assert u.cargo is not None
            load = f"{len(u.cargo)}/{u.capacity} pallets"
            if u.state == "arriving":
                return f"Heading to {nl(u.target)}" if u.moving else "Waiting at the gate for a bay"
            if u.state in ("docked", "loading"):
                dock = self.dock_by_node[u.docked_at or ""].label
                verb = "Unloading" if u.inbound else ("Loading" if u.state == "loading" else "Docked")
                return f"{verb} at {dock} · {load}"
            if u.state == "departing":
                return f"Leaving the site · {load}"
            return "Off site"
        if u.kind == "dock":
            if u.state == "maintenance":
                return "Under maintenance"
            truck = self.truck_at_dock(u.node or "")
            return f"{truck.id} docked" if truck else "Free"
        if u.kind == "rack":
            slots = next(r.slots for r in self.layout.racks if r.id == u.id)
            used = sum(1 for s in slots if self.pallets_at(s))
            return f"{used}/{len(slots)} slots used"
        if u.kind == "charger":
            who = self.charger_taken_by(u.node or "", exclude="")
            return f"{who} charging" if who else "Free"
        if u.kind in ("machine", "worker"):
            return str(u.meta.get("task", u.state))
        if u.kind == "pallet":
            p = u
            if p.holder:
                return f"On {p.holder}"
            return f"At {nl(p.node)}"
        return {"online": "Online", "offline": "Offline", "waiting": "Waiting for device"}.get(u.state, u.state)

    def to_unit(self, u: Entity) -> Unit:
        mover = u.kind in ("forklift", "truck")
        return Unit(
            id=u.id, kind=u.kind, source=u.source, state=u.state, label=u.label,  # type: ignore[arg-type]
            x=round(u.x, 3), z=round(u.z, 3), heading_rad=round(u.heading, 3),
            speed_mps=round(u.speed, 2) if mover else None,
            node=u.node, target_node=u.target if mover else None,
            path=list(u.path) if mover else None,
            task=self.task_text(u),
            battery_pct=round(u.battery, 1) if u.battery is not None else None,
            carrying=u.carrying if u.kind == "forklift" else None,
            docked_at=u.docked_at if u.kind == "truck" else None,
            holder=u.holder if u.kind == "pallet" else None,
            cargo=list(u.cargo) if u.cargo is not None else None,
            plan=[PlanStep(node=s.node, action=s.action) for s in u.plan] if u.kind == "forklift" else None,
            meta=u.meta or None,
        )
