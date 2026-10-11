"""Traffic control: forklifts and trucks never drive into each other or into people.

Reservations on the waypoint graph, the way automated warehouse fleets do it:

1. Conflict map (built once from layout geometry). Two resources (a node, or a lane between two
   nodes) conflict when vehicles of the same kind on both at once could touch: nodes closer than
   a body length plus a body width, a node too close to a lane (a forklift parked at a rack face
   sticks into the aisle), lanes closer than two body widths or crossing. Chargers next to each
   other don't conflict: forklifts park there side by side.
2. Grants. A vehicle may only enter its next lane once that lane and the node at its end are
   granted to it, and nothing another vehicle holds conflicts with them; otherwise it stops at
   the node it is on. Vehicles only ever wait at nodes, and two vehicles never hold conflicting
   resources, so they cannot overlap. A node is released once the vehicle is a body length past it.
3. People. Workers are not on the graph: a vehicle stops while a person is in a corridor ahead of
   it (along its route, its width plus a margin, braking distance plus 1 m long).
4. Getting unstuck. A parked forklift holding what another vehicle needs moves aside after 1.5 s
   to a free node off that vehicle's route. A cycle of vehicles waiting for each other is broken
   after 2 s: starting with the least right of way (right of way: carrying a pallet, then trucks,
   then the lower id), a vehicle drives through currently free lanes to the nearest pocket that
   doesn't touch what the others wait for, parks, and resumes its task 3 s later.
   Still waiting after 10 s: re-route around the blocked node if there is another way.
   People always have right of way.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import Graph
    from .world import Entity, World

HALF_LEN = {"forklift": 1.5, "truck": 5.4}
HALF_W = {"forklift": 0.85, "truck": 1.55}
MARGIN_M = 0.2
GAP_M = 1.0              # clear space kept in front of a vehicle approaching a person
LOOKAHEAD_GRANTS = 2     # lanes reserved ahead, so a vehicle doesn't brake at every node
ASIDE_AFTER_S = 1.5      # wait before asking a parked forklift to move
GRIDLOCK_AFTER_S = 2.0   # a wait-for cycle older than this is broken by a detour
REROUTE_AFTER_S = 10.0   # wait before trying another route around a blocked node

Res = tuple[str, ...]    # ("n", node) or ("e", a, b) with a < b


def node_res(n: str) -> Res:
    return ("n", n)


def edge_res(a: str, b: str) -> Res:
    return ("e", a, b) if a < b else ("e", b, a)


@dataclass
class Circle:
    owner: str
    x: float
    z: float
    r: float


def body(e: Entity) -> list[Circle]:
    """Footprint of a unit as circles along its heading (used by tests to check for overlap)."""
    hx, hz = math.cos(e.heading), math.sin(e.heading)
    if e.kind == "truck":
        return [Circle(e.id, e.x + hx * o, e.z + hz * o, 1.6) for o in (-3.6, 0.0, 3.6)]
    if e.kind == "forklift":
        return [Circle(e.id, e.x + hx * o, e.z + hz * o, 0.75) for o in (-0.7, 0.7)]
    return [Circle(e.id, e.x, e.z, 0.45)]  # worker


def priority(e: Entity) -> tuple[int, int, str]:
    """Smaller wins: loaded forklifts first, then trucks, then the lower id."""
    return (0 if e.carrying else 1, 0 if e.kind == "truck" else 1, e.id)


# ---------------------------------------------------------------- geometry and the conflict map

def _seg_point(px: float, pz: float, ax: float, az: float, bx: float, bz: float) -> float:
    dx, dz = bx - ax, bz - az
    l2 = dx * dx + dz * dz
    t = 0.0 if l2 < 1e-9 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def _seg_seg(s1: tuple[float, float, float, float], s2: tuple[float, float, float, float]) -> float:
    ax, az, bx, bz = s1
    cx, cz, dx, dz = s2

    def side(ox: float, oz: float, px: float, pz: float, qx: float, qz: float) -> float:
        return (px - ox) * (qz - oz) - (pz - oz) * (qx - ox)
    if (side(cx, cz, dx, dz, ax, az) * side(cx, cz, dx, dz, bx, bz) < 0
            and side(ax, az, bx, bz, cx, cz) * side(ax, az, bx, bz, dx, dz) < 0):
        return 0.0  # they cross
    return min(_seg_point(ax, az, cx, cz, dx, dz), _seg_point(bx, bz, cx, cz, dx, dz),
               _seg_point(cx, cz, ax, az, bx, bz), _seg_point(dx, dz, ax, az, bx, bz))


def _trim(ax: float, az: float, bx: float, bz: float, cut_a: float, cut_b: float) -> tuple[float, float, float, float] | None:
    """Segment a-b with cut_a removed at a's end and cut_b at b's end (None if nothing is left)."""
    length = math.hypot(bx - ax, bz - az)
    if length <= cut_a + cut_b + 1e-6:
        return None
    ux, uz = (bx - ax) / length, (bz - az) / length
    return (ax + ux * cut_a, az + uz * cut_a, bx - ux * cut_b, bz - uz * cut_b)


def build_conflicts(graph: Graph, lanes: list[tuple[str, str, list[str]]]) -> dict[Res, set[Res]]:
    """Resource -> resources another vehicle of the same kind may not hold at the same time."""
    nodes = graph.nodes
    conf: dict[Res, set[Res]] = {}
    for kind in ("forklift", "truck"):
        hl, hw = HALF_LEN[kind], HALF_W[kind]
        ns = [n for n in nodes.values() if kind in n.kinds]
        es = [(a, b) for a, b, kinds in lanes if kind in kinds]
        for r in [node_res(n.id) for n in ns] + [edge_res(a, b) for a, b in es]:
            conf.setdefault(r, set())
        near = hl + hw + MARGIN_M     # a parked vehicle (any heading) next to another, or to a lane
        lanes_d = 2 * hw + MARGIN_M   # vehicles on two neighbouring lanes

        def link(r1: Res, r2: Res) -> None:
            conf[r1].add(r2)
            conf[r2].add(r1)
        for i, n in enumerate(ns):
            for m in ns[i + 1:]:
                if n.type == "charger" and m.type == "charger":
                    continue  # chargers are built for side-by-side parking
                if math.hypot(n.x - m.x, n.z - m.z) < near:
                    link(node_res(n.id), node_res(m.id))
        for i, (a, b) in enumerate(es):
            na, nb = nodes[a], nodes[b]
            for n in ns:
                if n.id not in (a, b) and _seg_point(n.x, n.z, na.x, na.z, nb.x, nb.z) < near:
                    link(edge_res(a, b), node_res(n.id))
            for c, d in es[i + 1:]:
                nc, nd = nodes[c], nodes[d]
                # Next to a shared node, that node's own reservation keeps them apart.
                s1 = _trim(na.x, na.z, nb.x, nb.z, hl if a in (c, d) else 0.0, hl if b in (c, d) else 0.0)
                s2 = _trim(nc.x, nc.z, nd.x, nd.z, hl if c in (a, b) else 0.0, hl if d in (a, b) else 0.0)
                if s1 and s2 and _seg_seg(s1, s2) < lanes_d:
                    link(edge_res(a, b), edge_res(c, d))
    return conf


# ---------------------------------------------------------------- holdings and grants

def anchor(u: Entity) -> str | None:
    """The node a vehicle is at, or last passed."""
    return u.node if u.node is not None else u.prev_node


def holdings(world: World, u: Entity) -> set[Res]:
    if u.kind not in ("forklift", "truck") or u.state == "gone":
        return set()
    a = anchor(u)
    if a is None:
        return set()
    held: set[Res] = set()
    an = world.graph.nodes[a]
    if u.granted == 0 or math.hypot(u.x - an.x, u.z - an.z) < HALF_LEN[u.kind] + MARGIN_M:
        held.add(node_res(a))  # standing at, or not yet a body length clear of, its node
    prev = a
    for n in u.path[:u.granted]:
        held.add(edge_res(prev, n))
        held.add(node_res(n))
        prev = n
    return held


def _who_blocks(world: World, u: Entity, want: list[Res], held_by: dict[str, set[Res]]) -> Entity | None:
    conf = world.conflicts
    for o_id, hs in held_by.items():
        if o_id == u.id or not hs:
            continue
        for r in want:
            if r in hs or conf.get(r, set()) & hs:
                return world.entities[o_id]
    return None


def _dead_end(world: World, kind: str, node: str) -> bool:
    return len(world.graph.neighbours(kind, node)) == 1  # type: ignore[arg-type]


def _try_grant(world: World, u: Entity, held_by: dict[str, set[Res]]) -> Entity | None:
    """Grant u its next lane + node if free. Returns the vehicle in the way, or None.

    Entering a dead end (a dock, a rack slot, a zone, a charger) is granted together with the
    junction in front of it, or not at all: a vehicle never waits on the junction while the dead
    end is occupied, so whoever is inside can always get out."""
    prev = u.path[u.granted - 1] if u.granted > 0 else anchor(u)
    if prev is None:
        return None
    steps = 1
    if u.granted == len(u.path) - 2 and _dead_end(world, u.kind, u.path[-1]):
        steps = 2
    want: list[Res] = []
    p = prev
    for n in u.path[u.granted:u.granted + steps]:
        want += [edge_res(p, n), node_res(n)]
        p = n
    b = _who_blocks(world, u, want, held_by)
    if b is None:
        u.granted += steps
        held_by[u.id] = holdings(world, u)
    return b


# ---------------------------------------------------------------- people

def person_ahead(world: World, u: Entity, accel: float, vmax: float) -> Entity | None:
    look = HALF_LEN[u.kind] + GAP_M + vmax * vmax / (2 * accel)
    half_w = HALF_W[u.kind] + 0.05
    people = [e for e in world.entities.values() if e.kind == "worker" and e.state != "no_data"]
    if not people:
        return None
    pts = [(u.x, u.z)] + [(world.graph.nodes[n].x, world.graph.nodes[n].z) for n in u.path]
    acc = 0.0
    for i, ((ax, az), (bx, bz)) in enumerate(zip(pts, pts[1:])):
        length = math.hypot(bx - ax, bz - az)
        if length < 1e-6:
            continue
        dx, dz = (bx - ax) / length, (bz - az) / length
        for p in people:
            rx, rz = p.x - ax, p.z - az
            t = rx * dx + rz * dz
            if t < (0.0 if i == 0 else -0.45) or t > length:
                continue
            if acc + t < look + 0.45 and abs(-rx * dz + rz * dx) < half_w + 0.45:
                return p
        acc += length
        if acc > look:
            break
    return None


# ---------------------------------------------------------------- one tick

def step(world: World, dt: float, accel: float, pace: float, speeds: dict[str, float]) -> set[str]:
    """Grant what can be granted; returns the vehicles that must stand still (a person ahead)."""
    vehicles = [e for e in world.entities.values() if e.kind in ("forklift", "truck") and e.state != "gone"]
    held_by = {v.id: holdings(world, v) for v in vehicles}
    blocked: dict[str, Entity] = {}
    for u in sorted([v for v in vehicles if v.path], key=priority):  # right of way grants first
        while u.granted < min(len(u.path), LOOKAHEAD_GRANTS):
            b = _try_grant(world, u, held_by)
            if b is not None:
                blocked[u.id] = b
                break
    hold: set[str] = set()
    for u in vehicles:
        p = person_ahead(world, u, accel, speeds[u.kind]) if u.path else None
        if p is not None:
            hold.add(u.id)
        # Waiting = nothing granted ahead, so it stands at its node (or stopped for a person).
        who = p or (blocked.get(u.id) if u.path and u.granted == 0 else None)
        if who is None:
            u.blocked_by, u.blocked_since = None, None
        elif u.blocked_by != who.id:
            u.blocked_by, u.blocked_since = who.id, world.time
    _unstick(world, vehicles, held_by)
    _resume(world)
    return hold


# ---------------------------------------------------------------- getting unstuck

CLEAR_AISLE_AFTER_S = 4.0  # an idle auto forklift blocking an aisle junction goes to proper parking


def _blocks_junction(world: World, kind: str, node: str) -> bool:
    """Standing at `node` would block an aisle junction (e.g. a rack slot right next to the aisle)."""
    for r in world.conflicts.get(node_res(node), set()):
        if r[0] == "n" and world.graph.nodes[r[1]].type == "junction":
            return True
    return world.graph.nodes[node].type == "junction"


def _parking_penalty(world: World, kind: str, node: str) -> float:
    """0 for good parking (a zone or charger bay off the aisles), more for spots in the way."""
    n = world.graph.nodes[node]
    if n.type == "junction":
        return 30.0
    return 20.0 if _blocks_junction(world, kind, node) else 0.0


def _parked(e: Entity) -> bool:
    return e.kind == "forklift" and not e.path and not e.busy and e.state != "charging" and e.source != "device"


def _free_for(world: World, u: Entity, node: str, held_by: dict[str, set[Res]], prev: str | None) -> bool:
    want = [node_res(node)] + ([edge_res(prev, node)] if prev else [])
    return _who_blocks(world, u, want, held_by) is None


def _unstick(world: World, vehicles: list[Entity], held_by: dict[str, set[Res]]) -> None:
    ents = world.entities
    for u in vehicles:
        b = ents.get(u.blocked_by or "")
        if b is None or b.kind == "worker" or u.blocked_since is None:
            continue
        if _parked(b) and world.time - u.blocked_since >= ASIDE_AFTER_S and _move_aside(world, b, u, held_by):
            u.blocked_since = world.time
            return
    for start in vehicles:  # wait-for cycles: break one with a detour
        cycle: list[Entity] = []
        e: Entity | None = start
        while e is not None and e not in cycle and len(cycle) < 12:
            cycle.append(e)
            nxt = ents.get(e.blocked_by or "") if e.path else None
            e = nxt if nxt is not None and nxt.kind != "worker" else None
        if e is not start or len(cycle) < 2:
            continue
        if any(c.blocked_since is None or world.time - c.blocked_since < GRIDLOCK_AFTER_S for c in cycle):
            continue
        # Everyone queued into the jam (their wait chain leads into the cycle) can make way too:
        # when the two in the middle of an aisle are boxed in, the ones at the ends back out.
        jam = list(cycle)
        for w in vehicles:
            seen: list[Entity] = []
            e2: Entity | None = w
            while e2 is not None and e2 not in seen and e2 not in jam and len(seen) < 12:
                seen.append(e2)
                nxt = ents.get(e2.blocked_by or "") if e2.path else None
                e2 = nxt if nxt is not None and nxt.kind != "worker" else None
            if e2 is not None and e2 in jam:
                jam += [x for x in seen if x not in jam]
        candidates = sorted(cycle, key=priority, reverse=True) + sorted([j for j in jam if j not in cycle], key=priority, reverse=True)
        for v in candidates:
            if v.source != "device" and _escape(world, v, [c for c in jam if c is not v], held_by):
                return
        # Nobody can make way: parked forklifts next to the jam move aside to open a way out.
        for v in cycle:
            va = anchor(v)
            for m in world.graph.neighbours(v.kind, va) if va else []:  # type: ignore[arg-type]
                b = _who_blocks(world, v, [edge_res(va, m), node_res(m)], held_by) if va else None
                if b is not None and _parked(b) and _move_aside(world, b, v, held_by):
                    return
    for f in vehicles:  # auto mode: don't leave a forklift standing where it blocks an aisle
        if (_parked(f) and f.source == "auto" and f.resume is None and f.node is not None
                and world.time - f.idle_since >= CLEAR_AISLE_AFTER_S and _blocks_junction(world, f.kind, f.node)):
            if _park(world, f, held_by):
                return
    for u in vehicles:
        b = ents.get(u.blocked_by or "")
        if b is None or b.kind == "worker" or u.blocked_since is None:
            continue
        if world.time - u.blocked_since >= REROUTE_AFTER_S:
            _reroute(world, u, b)
            u.blocked_since = world.time


def _park(world: World, f: Entity, held_by: dict[str, set[Res]]) -> bool:
    """Send an idle forklift to the nearest good parking spot (zone or charger bay off the aisles)."""
    a = anchor(f)
    if a is None:
        return False
    best: tuple[float, str] | None = None
    for n in world.graph.nodes.values():
        if "forklift" not in n.kinds or n.id == a or _parking_penalty(world, "forklift", n.id) > 0:
            continue
        if any(o.target == n.id or o.node == n.id for o in world.of_kind("forklift") if o.id != f.id):
            continue
        if not _free_for(world, f, n.id, held_by, None):
            continue
        path = world.graph.shortest_path("forklift", a, n.id)
        if path and (best is None or world.graph.path_length(path) < best[0]):
            best = (world.graph.path_length(path), n.id)
    if best is None or best[0] > 60.0:
        return False
    if world.command(f.id, best[1], "goto", source="auto").ok:
        world.events.append(("info", f"{f.id} clears the aisle and parks at {world.node_label(best[1])}", f.id))
        return True
    return False


def _route_conflicts(world: World, u: Entity, steps: int) -> set[Res]:
    """Resources (and everything conflicting with them) on u's next few lanes."""
    out: set[Res] = set()
    prev = anchor(u)
    for n in u.path[:steps]:
        rs = [node_res(n)] + ([edge_res(prev, n)] if prev else [])
        for r in rs:
            out.add(r)
            out |= world.conflicts.get(r, set())
        prev = n
    return out


def _move_aside(world: World, b: Entity, u: Entity, held_by: dict[str, set[Res]]) -> bool:
    """Send parked forklift b to the nearest free node that doesn't conflict with u's route."""
    a = anchor(b)
    if a is None:
        return False
    keep_clear = _route_conflicts(world, u, 4)
    # Its way there must not lead through the vehicle it is making room for.
    u_held = held_by.get(u.id, set())
    through_u = {n for n in world.graph.nodes
                 if node_res(n) in u_held or world.conflicts.get(node_res(n), set()) & u_held}
    best: tuple[float, str] | None = None
    for n in world.graph.nodes.values():
        # A free charger bay is a fine place to step aside (often the only one in the charger corner).
        if "forklift" not in n.kinds or n.id == a or n.type == "dock" or node_res(n.id) in keep_clear:
            continue
        if any(f.target == n.id or f.node == n.id for f in world.of_kind("forklift") if f.id != b.id):
            continue
        if not _free_for(world, b, n.id, held_by, None):
            continue
        if n.id in through_u:
            continue
        path = world.graph.shortest_path("forklift", a, n.id, avoid=through_u)
        if not path:
            continue
        length = world.graph.path_length(path)
        # Pockets (zones, rack slots, charger bays) before junctions: a forklift parked on an aisle
        # junction is just the next one in somebody's way.
        score = length + _parking_penalty(world, "forklift", n.id)
        if length <= 40.0 and (best is None or score < best[0]):
            best = (score, n.id)
    if best is None:
        return False
    src = b.source if b.source in ("manual", "auto") else "manual"
    if world.command(b.id, best[1], "goto", source=src).ok:  # type: ignore[arg-type]
        world.events.append(("info", f"{b.id} moves aside to {world.node_label(best[1])} to let {u.id} pass", b.id))
        return True
    return False


def _escape(world: World, v: Entity, rest: list[Entity], held_by: dict[str, set[Res]]) -> bool:
    """Break a jam: v (standing at its node) drives through resources that are free right now, and
    don't touch what the others are waiting for, to the nearest pocket (a dead end, preferred) or
    free node. It parks there and picks its task up again once the others have moved on."""
    import heapq
    a = anchor(v)
    if a is None or v.granted > 0 or v.busy:
        return False
    kind = v.kind
    wanted: set[Res] = set()
    for r in rest:
        ra = anchor(r)
        # Only what they stand on and are waiting for now; their later route can wait its turn.
        steps = [ra] + r.path[:1] if ra else r.path[:1]
        for p, n in zip(steps, steps[1:]):
            for res in (node_res(n), edge_res(p, n)):
                wanted.add(res)
                wanted |= world.conflicts.get(res, set())
        if ra:
            wanted.add(node_res(ra))
            wanted |= world.conflicts.get(node_res(ra), set())
    others_held = {k: hs for k, hs in held_by.items() if k != v.id}
    dist = {a: 0.0}
    prev: dict[str, str] = {}
    heap = [(0.0, a)]
    best: tuple[tuple[int, float], str] | None = None
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist[n]:
            continue
        if n != a:
            pocket = _dead_end(world, kind, n)
            key = (0 if pocket else 1, d)
            taken = any(o.target == n for o in world.entities.values() if o.id != v.id and o.kind == kind)
            if world.graph.nodes[n].type != "dock" and not taken and (best is None or key < best[0]):
                best = (key, n)  # never park on somebody else's destination
        for m in world.graph.neighbours(kind, n):  # type: ignore[arg-type]
            res = [edge_res(n, m), node_res(m)]
            if any(r in wanted for r in res) or _who_blocks(world, v, res, others_held) is not None:
                continue
            nd = d + world.graph.distance(n, m)
            if nd < dist.get(m, math.inf) and nd < 60.0:
                dist[m], prev[m] = nd, n
                heapq.heappush(heap, (nd, m))
    if best is None:
        return False
    goal = best[1]
    path = [goal]
    while path[-1] != a:
        path.append(prev[path[-1]])
    path.reverse()
    if v.target and v.action and v.resume is None:
        v.resume = (v.target, v.action, v.action_pallet)
    v.path, v.granted, v.target, v.action, v.node = path[1:], 0, goal, "goto", None
    v.blocked_by, v.blocked_since = None, None
    v.resume_after = world.time + 3.0
    v.made_way_for = {r.id: anchor(r) for r in rest}
    world.events.append(("info", f"{v.id} makes way at {world.node_label(goal)} to clear a jam", v.id))
    return True


def _resume(world: World) -> None:
    for v in world.of_kind("forklift") + world.of_kind("truck"):
        if not (v.resume and not v.path and not v.busy and world.time >= v.resume_after):
            continue
        # Only once the ones it made way for have got going (or 20 s later, whatever happens):
        # resuming straight away would just drive back into the same jam.
        moved_on = all(o is None or not o.path or anchor(o) != was
                       for o, was in ((world.entities.get(k), w) for k, w in v.made_way_for.items()))
        if moved_on or world.time >= v.resume_after + 20.0:
            v.made_way_for = {}
            assert v.resume is not None
            target, action, pallet = v.resume
            v.resume = None
            src = v.source if v.source in ("manual", "auto") else "manual"
            world.command(v.id, target, action, pallet, source=src)  # type: ignore[arg-type]


def _reroute(world: World, u: Entity, b: Entity) -> None:
    a = anchor(u)
    if a is None or u.target is None or u.granted > 0:
        return
    avoid = {n for n in [anchor(b)] + b.path[:1] if n and n != u.target}
    path = world.graph.shortest_path(u.kind, a, u.target, avoid=avoid)  # type: ignore[arg-type]
    if path and len(path) > 1 and path[1:] != u.path:
        u.path, u.granted = path[1:], 0
        world.events.append(("info", f"{u.id} takes another route around {b.id}", u.id))
