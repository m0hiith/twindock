"""Traffic: forklifts and trucks never drive into each other or into people (traffic.py)."""

from __future__ import annotations

import itertools
import math
import random

import pytest

from conftest import Harness

from twindock import planner
from twindock.traffic import body
from twindock.world import Entity, World

OVERLAP_TOLERANCE_M = 0.15  # footprints are approximations; allow a touch, never driving through


def overlaps(a: Entity, b: Entity) -> float:
    """Worst overlap (m) between two units' footprints, 0 if they don't touch."""
    worst = 0.0
    for ca in body(a):
        for cb in body(b):
            worst = max(worst, ca.r + cb.r - math.hypot(ca.x - cb.x, cb.z - ca.z))
    return worst


def bodies(w: World) -> list[Entity]:
    return [e for e in w.entities.values()
            if (e.kind in ("forklift", "truck") and e.state != "gone") or (e.kind == "worker" and e.state != "no_data")]


def worst_overlap(w: World) -> tuple[float, str]:
    worst, who = 0.0, ""
    for a, b in itertools.combinations(bodies(w), 2):
        if a.kind == "worker" and b.kind == "worker":
            continue  # people walk past each other
        o = overlaps(a, b)
        if o > worst:
            worst, who = o, f"{a.id}/{b.id}"
    return worst, who


def drive(h: Harness, seconds: float) -> float:
    worst = 0.0
    for _ in range(round(seconds / 0.1)):
        h.world.tick(0.1)
        worst = max(worst, worst_overlap(h.world)[0])
    return worst


def park(w: World, uid: str, node: str) -> None:
    u, n = w.entities[uid], w.graph.nodes[node]
    u.x, u.z, u.node, u.prev_node, u.path, u.state, u.action, u.target = n.x, n.z, n.id, n.id, [], "idle", None, None


def test_head_on_in_one_aisle_both_arrive_without_touching(h: Harness) -> None:
    w = h.world
    park(w, "FL-01", "AISLE_1")
    park(w, "FL-03", "AISLE_4")
    assert w.command("FL-01", "AISLE_4", "goto").ok and w.command("FL-03", "AISLE_1", "goto").ok
    reached: set[str] = set()
    for _ in range(900):
        w.tick(0.1)
        assert overlaps(w.entities["FL-01"], w.entities["FL-03"]) <= OVERLAP_TOLERANCE_M
        reached |= {e.id for e, n in ((w.entities["FL-01"], "AISLE_4"), (w.entities["FL-03"], "AISLE_1")) if e.node == n}
    assert reached == {"FL-01", "FL-03"}
    assert any("makes way" in t or "moves aside" in t for _, t, _ in w.events)  # one of them gave way


def test_following_keeps_a_gap(h: Harness) -> None:
    w = h.world
    park(w, "FL-01", "AISLE_W")
    park(w, "FL-03", "AISLE_1")
    assert w.command("FL-03", "AISLE_E", "goto").ok
    w.tick(0.2)
    assert w.command("FL-01", "AISLE_E", "goto").ok  # same way, right behind
    closest = math.inf
    reached = set()
    for _ in range(300):
        w.tick(0.1)
        a, b = w.entities["FL-01"], w.entities["FL-03"]
        closest = min(closest, math.hypot(a.x - b.x, a.z - b.z))
        reached |= {e.id for e in (a, b) if e.node == "AISLE_E"}
    assert closest >= 3.0  # never closer than a forklift length centre to centre
    assert reached == {"FL-01", "FL-03"}  # both got there (the first then moved aside for the second)


def test_crossing_at_a_junction(h: Harness) -> None:
    w = h.world
    park(w, "FL-01", "MAIN_1")
    park(w, "FL-03", "AISLE_W")
    park(w, "FL-02", "CHG_J")
    assert w.command("FL-01", "MAIN_W", "goto").ok   # westbound into the corner
    assert w.command("FL-03", "CHG_J", "goto").ok    # southbound through the same corner
    reached = set()
    for _ in range(400):
        w.tick(0.1)
        assert worst_overlap(w)[0] <= OVERLAP_TOLERANCE_M
        reached |= {e.id for e, n in ((w.entities["FL-01"], "MAIN_W"), (w.entities["FL-03"], "CHG_J")) if e.node == n}
    assert reached == {"FL-01", "FL-03"}


def test_parked_forklift_moves_aside(h: Harness) -> None:
    w = h.world
    park(w, "FL-03", "AISLE_2")  # idle in the middle of the aisle
    park(w, "FL-01", "AISLE_W")
    assert w.command("FL-01", "AISLE_E", "goto").ok
    assert drive(h, 40.0) <= OVERLAP_TOLERANCE_M
    assert w.entities["FL-01"].node == "AISLE_E"
    assert w.entities["FL-03"].node != "AISLE_2"
    assert any("FL-03 moves aside" in t for _, t, _ in w.events)


def test_stops_for_a_pedestrian_on_the_lane(h: Harness) -> None:
    w = h.world
    park(w, "FL-01", "AISLE_W")
    park(w, "FL-03", "ZONE_C")  # out of this aisle: only the person is in the way
    walker = w.entities["WK-01"]
    walker.state, walker.x, walker.z = "working", 20.0, 8.0  # standing in the aisle
    assert w.command("FL-01", "AISLE_E", "goto").ok
    for _ in range(150):
        w.tick(0.1)
    fl = w.entities["FL-01"]
    assert fl.blocked_by == "WK-01" and fl.speed == 0.0
    assert overlaps(fl, walker) <= 0 and "pedestrian" in w.task_text(fl)
    walker.z = 3.0  # steps out of the way
    for _ in range(200):
        w.tick(0.1)
    assert fl.node == "AISLE_E"


@pytest.mark.parametrize("seed", [11, 3, 7, 21, 42])
def test_auto_mode_ten_minutes_without_overlap_or_gridlock(h: Harness, seed: int) -> None:
    w = h.world
    rng = random.Random(seed)
    moved = {f.id: 0.0 for f in w.of_kind("forklift")}
    last = {f.id: (f.x, f.z) for f in w.of_kind("forklift")}
    stuck = {f.id: 0.0 for f in w.of_kind("forklift")}
    worst, who = 0.0, ""
    for i in range(6000):  # 10 minutes at 0.1 s
        w.tick(0.1)
        if i % 10 == 0:
            planner.auto_step(w, rng)
        for f in w.of_kind("forklift"):
            moved[f.id] += math.hypot(f.x - last[f.id][0], f.z - last[f.id][1])
            last[f.id] = (f.x, f.z)
            stuck[f.id] = stuck[f.id] + 0.1 if f.blocked_by else 0.0
            assert stuck[f.id] < 60.0, f"{f.id} blocked by {f.blocked_by} for a minute"
        o, pair = worst_overlap(w)
        if o > worst:
            worst, who = o, pair
    assert worst <= OVERLAP_TOLERANCE_M, f"{who} overlapped by {worst:.2f} m"
    assert sum(moved.values()) > 500  # the warehouse kept working
