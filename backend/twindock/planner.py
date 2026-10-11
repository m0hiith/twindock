"""Task planning for forklifts and trucks.

Used by auto mode (background movement) and by BTN0 when the selected forklift's task list is
empty. It only proposes steps; every step still goes through World.command validation.

The flow keeps stock circulating: inbound trucks are unloaded to Zone A (receiving), Zone A is
put away into the racks, rack and Zone B stock is loaded onto outbound trucks, and a truck that
leaves full comes back later as inbound with the same pallets.

Auto mode passes a random generator so the floor doesn't replay the same moves every time: job
order, pallet and slot choices, waits and truck bays vary. BTN0 passes none and stays predictable.
"""

from __future__ import annotations

import random

from .world import Entity, Step, World

RECEIVING_ZONE = "ZONE_A"
STAGING_ZONE = "ZONE_B"
FACTORY_OUT = "FAC_OUT"       # FAC-01 line output: finished pallets wait here for a forklift
RAW_STOCK = "RAW_STOCK"       # raw material store: delivered pallets wait here for the raw forklift
FACTORY_IN = "FAC_IN"         # the line's inbound spot: the presses use its pallets up (engine._raw_material)
RAW_CHARGERS = {"RAW_CHARGER"}
CHARGE_BELOW_PCT = 25.0
TRUCK_DEPART_AT = 4          # an outbound truck leaves once it has this many pallets
TRUCK_DEPART_IDLE_S = 8.0    # ...and nothing has been loaded for this long
TRUCK_RETURN_S = 20.0        # a gone truck comes back after this long off site
TRUCK_WAITING_S = 5.0        # a truck waiting at the gate is given a bay after this long
FORKLIFT_IDLE_S = 2.0        # pause between tasks so movements read as separate jobs
# Auto mode's random rhythm. Each 1 s auto pass, an eligible unit acts with this probability,
# which gives a random (geometric) wait instead of everyone moving in lockstep.
AUTO_START_P = 0.5
AUTO_TRUCK_P = 0.3
AUTO_WANDER_P = 0.15         # an idle forklift with no work drives somewhere now and then
CHOICE_SPREAD = 3            # random choices pick among this many nearest candidates
WANDER_TYPES = ("zone",)  # idle forklifts park in a zone, never on an aisle junction (traffic.py)


def _dist(world: World, u: Entity, node: str) -> float:
    kind = "truck" if u.kind == "truck" else "forklift"
    start = u.node or (u.path[0] if u.path else None)
    if start is None:
        return float("inf")
    path = world.graph.shortest_path(kind, start, node)
    return world.graph.path_length(path) if path else float("inf")


def _nearest(world: World, u: Entity, nodes: list[str], rng: random.Random | None = None) -> list[str]:
    """Nearest first. With rng, one of the few nearest is moved to the front, so choices vary
    without sending a forklift across the building for no reason."""
    ordered = sorted(nodes, key=lambda n: _dist(world, u, n))
    if rng is not None and len(ordered) > 1:
        i = rng.randrange(min(CHOICE_SPREAD, len(ordered)))
        ordered.insert(0, ordered.pop(i))
    return ordered


def _area_of_dock(world: World, dock_node: str | None) -> str:
    d = world.dock_by_node.get(dock_node or "")
    return d.area if d else "warehouse"


def _docked(world: World, inbound: bool, area: str = "warehouse") -> list[Entity]:
    return [t for t in world.of_kind("truck")
            if t.docked_at is not None and t.inbound == inbound and not t.moving and _area_of_dock(world, t.docked_at) == area]


def _free_rack_slots(world: World, exclude: str) -> list[str]:
    g = world.graph
    return [n.id for n in g.nodes.values() if n.type == "rack_slot" and world.free_spots(n, exclude) > 0]


def carrying_step(world: World, f: Entity, rng: random.Random | None = None) -> Step | None:
    """Where to take the pallet a forklift is holding."""
    for t in _docked(world, inbound=False):
        if world.truck_room(t, exclude=f.id) > 0 and t.docked_at and not _dock_taken(world, t.docked_at, f):
            return Step(t.docked_at, "load")
    slots = _nearest(world, f, _free_rack_slots(world, f.id), rng)
    if slots:
        return Step(slots[0], "drop")
    for z in (STAGING_ZONE, "ZONE_C", RECEIVING_ZONE):
        if world.free_spots(world.graph.nodes[z], f.id) > 0:
            return Step(z, "drop")
    return None


def _dock_taken(world: World, dock_node: str, f: Entity) -> bool:
    """Another forklift is already working this dock (heading there or with it in its plan): one
    forklift per truck at a time, so they don't queue on the main aisle in front of one door."""
    for o in world.of_kind("forklift"):
        if o.id != f.id and (o.target == dock_node or any(s.node == dock_node for s in o.plan)):
            return True
    return False


def _unclaimed(world: World, pallets: list[Entity], f: Entity) -> bool:
    return any(p.claimed_by in (None, f.id) for p in pallets)


def suggest_raw_forklift(world: World, f: Entity, rng: random.Random | None = None) -> list[Step]:
    """The raw material store's forklift: unload raw trucks to the raw stock, feed the line's inbound spot from it."""
    if f.carrying:
        for node in (FACTORY_IN, RAW_STOCK):
            if node in world.graph.nodes and world.free_spots(world.graph.nodes[node], f.id) > 0:
                return [Step(node, "drop")]
        return []
    if RAW_STOCK in world.graph.nodes and FACTORY_IN in world.graph.nodes:
        if _unclaimed(world, world.pallets_at(RAW_STOCK), f) and world.free_spots(world.graph.nodes[FACTORY_IN], f.id) > 0:
            return [Step(RAW_STOCK, "pick"), Step(FACTORY_IN, "drop")]
        for t in _docked(world, inbound=True, area="raw"):
            assert t.cargo is not None and t.docked_at is not None
            if _dock_taken(world, t.docked_at, f):
                continue
            if t.cargo and _unclaimed(world, [world.entities[p] for p in t.cargo], f) and world.free_spots(world.graph.nodes[RAW_STOCK], f.id) > 0:
                return [Step(t.docked_at, "pick"), Step(RAW_STOCK, "drop")]
    return []


def suggest_forklift(world: World, f: Entity, rng: random.Random | None = None) -> list[Step]:
    assert f.battery is not None
    raw = f.meta.get("area") == "raw"
    if f.battery < CHARGE_BELOW_PCT and f.state != "charging":
        chargers = [c.node for c in world.layout.chargers
                    if (c.node in RAW_CHARGERS) == raw and not world.charger_taken_by(c.node, f.id)]
        if chargers:
            return [Step(_nearest(world, f, chargers)[0], "charge")]
    if raw:
        return suggest_raw_forklift(world, f, rng)
    if f.carrying:
        s = carrying_step(world, f, rng)
        return [s] if s else []

    def unload() -> list[Step]:
        zone_a = world.graph.nodes[RECEIVING_ZONE]
        for t in _docked(world, inbound=True):
            assert t.cargo is not None and t.docked_at is not None
            if _dock_taken(world, t.docked_at, f):
                continue
            if _unclaimed(world, [world.entities[p] for p in t.cargo], f) and world.free_spots(zone_a, f.id) > 0:
                return [Step(t.docked_at, "pick"), Step(RECEIVING_ZONE, "drop")]
        return []

    def load() -> list[Step]:
        for t in _docked(world, inbound=False):
            if world.truck_room(t, exclude=f.id) <= 0 or t.docked_at is None or _dock_taken(world, t.docked_at, f):
                continue
            sources = [STAGING_ZONE] if _unclaimed(world, world.pallets_at(STAGING_ZONE), f) else []
            sources += _nearest(world, f, [n.id for n in world.graph.nodes.values()
                                           if n.type == "rack_slot" and _unclaimed(world, world.pallets_at(n.id), f)], rng)
            if sources:
                return [Step(sources[0], "pick"), Step(t.docked_at, "load")]
        return []

    def collect_production() -> list[Step]:
        # Finished pallets from the factory line go to the warehouse: a rack slot if one is free,
        # else the staging zone, where outbound trucks are loaded from.
        if FACTORY_OUT not in world.graph.nodes or not _unclaimed(world, world.pallets_at(FACTORY_OUT), f):
            return []
        slots = _nearest(world, f, _free_rack_slots(world, f.id), rng)
        if slots:
            return [Step(FACTORY_OUT, "pick"), Step(slots[0], "drop")]
        if world.free_spots(world.graph.nodes[STAGING_ZONE], f.id) > 0:
            return [Step(FACTORY_OUT, "pick"), Step(STAGING_ZONE, "drop")]
        return []

    def put_away() -> list[Step]:
        if _unclaimed(world, world.pallets_at(RECEIVING_ZONE), f):
            slots = _nearest(world, f, _free_rack_slots(world, f.id), rng)
            if slots:
                return [Step(RECEIVING_ZONE, "pick"), Step(slots[0], "drop")]
        return []

    jobs = [unload, load, collect_production, put_away]  # the flow's priority order; auto mode varies it
    if rng is not None:
        rng.shuffle(jobs)
    for job in jobs:
        steps = job()
        if steps:
            return steps
    return []


def run_next_step(world: World, f: Entity, source: str, rng: random.Random | None = None) -> tuple[bool, str]:
    """Run the forklift's next task-list step, refilling the list from the planner when empty.

    Steps that are no longer valid (pallet gone, truck left) are dropped. Returns (ok, text).
    """
    skipped: list[str] = []
    refilled = False
    for _ in range(6):
        if not f.plan:
            if refilled:
                break
            f.plan = suggest_forklift(world, f, rng)
            refilled = True
            if not f.plan:
                break
        step = f.plan[0]
        r = world.command(f.id, step.node, step.action, step.pallet_id, source=source)  # type: ignore[arg-type]
        f.plan.pop(0)
        if r.ok:
            return True, f"{f.id}: {step.action} at {world.node_label(step.node)}"
        skipped.append(r.reason or "invalid")
    why = f" (skipped: {'; '.join(skipped)})" if skipped else ""
    return False, f"{f.id} has nothing to do{why}"


def auto_step(world: World, rng: random.Random) -> list[str]:
    """One auto-mode pass (once a second). Returns human-readable notes for the event log."""
    notes: list[str] = []
    now = world.time
    for f in world.of_kind("forklift"):
        if f.source == "device" or f.moving or f.busy or f.action is not None or f.resume is not None:
            continue  # (resume: it made way in a jam and picks its own task up again, traffic.py)
        if now - f.idle_since < FORKLIFT_IDLE_S or rng.random() > AUTO_START_P:
            continue
        ok, text = run_next_step(world, f, "auto", rng)
        if ok:
            notes.append(text)
        elif not f.carrying and rng.random() < AUTO_WANDER_P:
            raw = f.meta.get("area") == "raw"
            spots = [n.id for n in world.graph.nodes.values()
                     if n.type in WANDER_TYPES and "forklift" in n.kinds and n.id != f.node
                     and (n.id in (RAW_STOCK,) if raw else n.id not in (RAW_STOCK, FACTORY_IN))]
            if not spots:
                continue
            target = rng.choice(spots)
            if world.command(f.id, target, "goto", source="auto").ok:
                notes.append(f"{f.id}: no work, moving to {world.node_label(target)}")
    for t in world.of_kind("truck"):
        if t.source == "device" or t.moving or t.state == "loading" or rng.random() > AUTO_TRUCK_P:
            continue
        assert t.cargo is not None
        idle = now - t.idle_since
        area = str(t.meta.get("area", "warehouse"))
        docks = [d for d in world.layout.docks if d.area == area]
        if area == "raw":
            # The supplier's truck: unloaded at a raw dock, leaves empty, returns with a new load.
            if t.docked_at and not t.cargo and idle >= TRUCK_DEPART_IDLE_S:
                if not any(f.target == t.docked_at for f in world.of_kind("forklift")) and world.command(t.id, world.layout.gate_node, "depart", source="auto").ok:
                    notes.append(f"{t.id} leaves the raw material store empty")
                continue
            if (t.state == "gone" and idle >= TRUCK_RETURN_S) or (t.state == "arriving" and idle >= TRUCK_WAITING_S):
                if t.state == "gone" and not t.cargo:
                    made = world.load_raw_cargo(t.id, int(t.capacity or 4))
                    t.inbound = True
                    notes.append(f"{t.id} returns with {len(made)} raw material pallets")
                for d in rng.sample(docks, len(docks)):
                    if world.command(t.id, d.node, "dock", source="auto").ok:
                        notes.append(f"{t.id} assigned to {d.label}")
                        break
            continue
        if t.docked_at and not t.inbound and len(t.cargo) >= TRUCK_DEPART_AT and idle >= TRUCK_DEPART_IDLE_S:
            if not any(f.target == t.docked_at for f in world.of_kind("forklift")):
                if world.command(t.id, world.layout.gate_node, "depart", source="auto").ok:
                    notes.append(f"{t.id} departs with {len(t.cargo)} pallets")
        elif (t.state == "gone" and idle >= TRUCK_RETURN_S) or (t.state == "arriving" and idle >= TRUCK_WAITING_S):
            for d in rng.sample(docks, len(docks)):
                if world.command(t.id, d.node, "dock", source="auto").ok:
                    notes.append(f"{t.id} assigned to {d.label}")
                    break
    # Raw material is used up by the presses themselves: the engine counts their parts (engine._raw_material).
    return notes


def line_running(world: World) -> bool:
    """A factory machine is running (its state comes from its monitor; with no data the line uses nothing up)."""
    return any(m.state == "running" for m in world.of_kind("machine"))


def track_idle(world: World, docked_cargo: dict[str, int]) -> None:
    """Restart a docked truck's idle timer whenever its cargo count changes."""
    for t in world.of_kind("truck"):
        n = len(t.cargo or [])
        if docked_cargo.get(t.id) != n:
            docked_cargo[t.id] = n
            t.idle_since = world.time
