"""Task planning for forklifts and trucks.

Used by auto mode (background movement) and by BTN0 when the selected forklift's task list is
empty. It only proposes steps; every step still goes through World.command validation.

The flow keeps stock circulating: inbound trucks are unloaded to Zone A (receiving), Zone A is
put away into the racks, rack and Zone B stock is loaded onto outbound trucks, and a truck that
leaves full comes back later as inbound with the same pallets.
"""

from __future__ import annotations

from .world import Entity, Step, World

RECEIVING_ZONE = "ZONE_A"
STAGING_ZONE = "ZONE_B"
CHARGE_BELOW_PCT = 25.0
TRUCK_DEPART_AT = 4          # an outbound truck leaves once it has this many pallets
TRUCK_DEPART_IDLE_S = 8.0    # ...and nothing has been loaded for this long
TRUCK_RETURN_S = 20.0        # a gone truck comes back after this long off site
TRUCK_WAITING_S = 5.0        # a truck waiting at the gate is given a bay after this long
FORKLIFT_IDLE_S = 2.0        # pause between tasks so movements read as separate jobs


def _dist(world: World, u: Entity, node: str) -> float:
    kind = "truck" if u.kind == "truck" else "forklift"
    start = u.node or (u.path[0] if u.path else None)
    if start is None:
        return float("inf")
    path = world.graph.shortest_path(kind, start, node)
    return world.graph.path_length(path) if path else float("inf")


def _nearest(world: World, u: Entity, nodes: list[str]) -> list[str]:
    return sorted(nodes, key=lambda n: _dist(world, u, n))


def _docked(world: World, inbound: bool) -> list[Entity]:
    return [t for t in world.of_kind("truck")
            if t.docked_at is not None and t.inbound == inbound and not t.moving]


def _free_rack_slots(world: World, exclude: str) -> list[str]:
    g = world.graph
    return [n.id for n in g.nodes.values() if n.type == "rack_slot" and world.free_spots(n, exclude) > 0]


def carrying_step(world: World, f: Entity) -> Step | None:
    """Where to take the pallet a forklift is holding."""
    for t in _docked(world, inbound=False):
        if world.truck_room(t, exclude=f.id) > 0 and t.docked_at:
            return Step(t.docked_at, "load")
    slots = _nearest(world, f, _free_rack_slots(world, f.id))
    if slots:
        return Step(slots[0], "drop")
    for z in (STAGING_ZONE, "ZONE_C", RECEIVING_ZONE):
        if world.free_spots(world.graph.nodes[z], f.id) > 0:
            return Step(z, "drop")
    return None


def _unclaimed(world: World, pallets: list[Entity], f: Entity) -> bool:
    return any(p.claimed_by in (None, f.id) for p in pallets)


def suggest_forklift(world: World, f: Entity) -> list[Step]:
    assert f.battery is not None
    if f.battery < CHARGE_BELOW_PCT and f.state != "charging":
        chargers = [c.node for c in world.layout.chargers if not world.charger_taken_by(c.node, f.id)]
        if chargers:
            return [Step(_nearest(world, f, chargers)[0], "charge")]
    if f.carrying:
        s = carrying_step(world, f)
        return [s] if s else []

    zone_a = world.graph.nodes[RECEIVING_ZONE]
    for t in _docked(world, inbound=True):
        assert t.cargo is not None and t.docked_at is not None
        if _unclaimed(world, [world.entities[p] for p in t.cargo], f) and world.free_spots(zone_a, f.id) > 0:
            return [Step(t.docked_at, "pick"), Step(RECEIVING_ZONE, "drop")]

    for t in _docked(world, inbound=False):
        if world.truck_room(t, exclude=f.id) <= 0 or t.docked_at is None:
            continue
        sources = [STAGING_ZONE] if _unclaimed(world, world.pallets_at(STAGING_ZONE), f) else []
        sources += _nearest(world, f, [n.id for n in world.graph.nodes.values()
                                       if n.type == "rack_slot" and _unclaimed(world, world.pallets_at(n.id), f)])
        if sources:
            return [Step(sources[0], "pick"), Step(t.docked_at, "load")]

    if _unclaimed(world, world.pallets_at(RECEIVING_ZONE), f):
        slots = _nearest(world, f, _free_rack_slots(world, f.id))
        if slots:
            return [Step(RECEIVING_ZONE, "pick"), Step(slots[0], "drop")]
    return []


def run_next_step(world: World, f: Entity, source: str) -> tuple[bool, str]:
    """Run the forklift's next task-list step, refilling the list from the planner when empty.

    Steps that are no longer valid (pallet gone, truck left) are dropped. Returns (ok, text).
    """
    skipped: list[str] = []
    refilled = False
    for _ in range(6):
        if not f.plan:
            if refilled:
                break
            f.plan = suggest_forklift(world, f)
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


def auto_step(world: World) -> list[str]:
    """One auto-mode pass. Returns human-readable notes for the event log."""
    notes: list[str] = []
    now = world.time
    for f in world.of_kind("forklift"):
        if f.source == "device" or f.moving or f.busy or f.action is not None:
            continue
        if now - f.idle_since < FORKLIFT_IDLE_S:
            continue
        ok, text = run_next_step(world, f, "auto")
        if ok:
            notes.append(text)
    for t in world.of_kind("truck"):
        if t.source == "device" or t.moving or t.state == "loading":
            continue
        assert t.cargo is not None
        idle = now - t.idle_since
        if t.docked_at and not t.inbound and len(t.cargo) >= TRUCK_DEPART_AT and idle >= TRUCK_DEPART_IDLE_S:
            if not any(f.target == t.docked_at for f in world.of_kind("forklift")):
                if world.command(t.id, world.layout.gate_node, "depart", source="auto").ok:
                    notes.append(f"{t.id} departs with {len(t.cargo)} pallets")
        elif (t.state == "gone" and idle >= TRUCK_RETURN_S) or (t.state == "arriving" and idle >= TRUCK_WAITING_S):
            for d in world.layout.docks:
                if world.command(t.id, d.node, "dock", source="auto").ok:
                    notes.append(f"{t.id} assigned to {d.label}")
                    break
    return notes


def track_idle(world: World, docked_cargo: dict[str, int]) -> None:
    """Restart a docked truck's idle timer whenever its cargo count changes."""
    for t in world.of_kind("truck"):
        n = len(t.cargo or [])
        if docked_cargo.get(t.id) != n:
            docked_cargo[t.id] = n
            t.idle_since = world.time
