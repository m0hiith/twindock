"""F1: Riverside Campus. Graph connectivity, separate pedestrian and vehicle graphs that only cross at marked crossings,
zones with hazard and PPE, devices in every building, workers on walkways."""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

import pytest

from twindock.devices import load_sites
from twindock.graph import Graph, load_layout
from twindock.wiring import kit_ids

WORLD = Path(__file__).resolve().parents[1] / "world"
LAYOUT = json.loads((WORLD / "layout.json").read_text())
SITES = load_sites()
NODES = {n["id"]: n for n in LAYOUT["nodes"]}
VEH_LANES = [x for x in LAYOUT["lanes"] if x["kinds"]]
PED_LANES = [x for x in LAYOUT["lanes"] if not x["kinds"]]
CAMPUS = LAYOUT["campus"]
ZONES = {z["id"]: z for s in SITES["sites"] for z in s["zones"]}


def components(lanes: list[dict]) -> list[set[str]]:
    adj: dict[str, set[str]] = {}
    for x in lanes:
        adj.setdefault(x["a"], set()).add(x["b"])
        adj.setdefault(x["b"], set()).add(x["a"])
    seen: set[str] = set()
    out = []
    for start in adj:
        if start in seen:
            continue
        comp, q = {start}, deque([start])
        while q:
            for m in adj[q.popleft()]:
                if m not in comp:
                    comp.add(m)
                    q.append(m)
        seen |= comp
        out.append(comp)
    return out


def seg(n: str, m: str) -> tuple[tuple[float, float], tuple[float, float]]:
    return (NODES[n]["x"], NODES[n]["z"]), (NODES[m]["x"], NODES[m]["z"])


def intersect(p1, p2, p3, p4):  # type: ignore[no-untyped-def]
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-9:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])) if 0 <= t <= 1 and 0 <= u <= 1 else None


def test_layout_loads_and_every_lane_has_nodes() -> None:
    load_layout()
    for x in LAYOUT["lanes"]:
        assert x["a"] in NODES and x["b"] in NODES, x


def test_vehicle_graphs_are_connected_along_the_flows() -> None:
    g = Graph(load_layout())
    # trucks: gate -> weighbridge -> yard -> dock bay, and on to the raw material docks and out
    for a, b in (("ROAD_E", "BAY_1"), ("ROAD_E", "RAW_BAY_1"), ("ROAD_E", "RAW_BAY_2"), ("RAW_BAY_1", "ROAD_E")):
        assert g.shortest_path("truck", a, b), f"no truck route {a} -> {b}"
    path = g.shortest_path("truck", "ROAD_E", "BAY_1")
    assert path is not None and path.index("WEIGH") < path.index("GATE_IN") < path.index("BAY_1")
    # a truck waiting at the factory's road also crosses the weighbridge on its way in
    inbound = g.shortest_path("truck", "ROAD_IN", "BAY_1")
    assert inbound is not None and "WEIGH" in inbound
    # forklifts: raw material -> manufacturing -> warehouse (-> dispatch docks)
    for a, b in (("RAW_DOCK_1", "FAC_AISLE_1"), ("RAW_DOCK_2", "FAC_OUT"), ("FAC_OUT", "DOCK_1"), ("RAW_DOCK_1", "DOCK_3")):
        assert g.shortest_path("forklift", a, b), f"no forklift route {a} -> {b}"


def test_pedestrian_graph_is_one_network_that_reaches_every_building() -> None:
    comps = components(PED_LANES)
    big = max(comps, key=len)
    ped_ids = {n["id"] for n in LAYOUT["nodes"] if not n["kinds"]}
    assert ped_ids <= big, f"unreachable on foot: {sorted(ped_ids - big)}"
    for b in CAMPUS["buildings"]:
        assert b["door"] in big, b["id"]
    for m in CAMPUS["muster_points"]:
        assert m["node"] in big, m["id"]
    assert {"WALK_PRESS", "WALK_COLD", "WALK_OFFICE"} <= big  # the factory floor is on the same network


def test_walkways_cross_vehicle_lanes_and_roads_only_at_marked_crossings() -> None:
    crossing_ids = {c["id"] for c in CAMPUS["crossings"]}
    hall = {"WALK_OFFICE", "WALK_STAFF_DOOR", "WALK_QC", "WALK_PACKER", "WALK_PRESS", "WALK_EAST", "WALK_COLD_DOOR", "WALK_COLD", "WALK_DOCK_DOOR",
            "WALK_DOCKS", "P_FAC_E"}  # inside the factory hall, where people share the floor with forklifts by design
    new_ped = [x for x in PED_LANES if x.get("campus") and not (x["a"] in hall and x["b"] in hall)]
    assert new_ped
    roads = LAYOUT["roads"]
    for x in new_ped:
        p1, p2 = seg(x["a"], x["b"])
        marked = x.get("crossing") in crossing_ids
        veh_hits = [(v["a"], v["b"]) for v in VEH_LANES if intersect(p1, p2, *seg(v["a"], v["b"])) is not None]
        road_hits = []
        for r in roads:
            for q1, q2 in zip(r["points"], r["points"][1:]):
                half = r["width"] / 2
                # the road band as a rectangle (roads here are axis-aligned)
                x0, x1 = sorted((q1[0], q2[0]))
                z0, z1 = sorted((q1[1], q2[1]))
                x0, x1, z0, z1 = x0 - (half if x0 == x1 else 0), x1 + (half if x0 == x1 else 0), z0 - (half if z0 == z1 else 0), z1 + (half if z0 == z1 else 0)
                for t in (i / 40 for i in range(41)):
                    px, pz = p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t
                    if x0 < px < x1 and z0 < pz < z1:
                        road_hits.append(r["id"])
                        break
        if not marked:
            assert not veh_hits, f"walkway {x['a']}-{x['b']} crosses vehicle lane {veh_hits} without a marked crossing"
            assert not road_hits, f"walkway {x['a']}-{x['b']} runs over road {road_hits} without a marked crossing"
    for c in CAMPUS["crossings"]:
        lane = next(x for x in PED_LANES if {x["a"], x["b"]} == {c["a"], c["b"]})
        assert lane.get("crossing") == c["id"]
        assert c["hotspot"]["radius_m"] > 0


def test_every_crossing_of_a_vehicle_lane_is_a_hotspot() -> None:
    marked = [x for x in PED_LANES if x.get("crossing")]
    assert len(marked) == len(CAMPUS["crossings"]) >= 5
    for x in marked:
        hits = [v for v in VEH_LANES if intersect(*seg(x["a"], x["b"]), *seg(v["a"], v["b"])) is not None]
        assert hits or x["crossing"] == "X0", f"crossing {x['crossing']} crosses no vehicle lane"


def test_every_building_is_a_zone_with_devices_hazard_and_ppe() -> None:
    dev_zones: dict[str, list[str]] = {}
    for d in SITES["devices"]:
        dev_zones.setdefault(d["zone_id"], []).append(d["id"])
    for b in CAMPUS["buildings"]:
        z = ZONES[b["zone"]]
        assert z.get("hazard") in ("low", "medium", "high"), b["id"]
        if b["id"] != "SEC_CABIN" and b["id"] != "PUMP_HOUSE":
            assert dev_zones.get(b["zone"]), f"{b['id']} has no devices"
        assert len(dev_zones.get(b["zone"], [])) <= 8, "sensible counts, not hundreds"
    assert ZONES["FAC01_HAZMAT"]["hazard"] == "high" and "respirator" in ZONES["FAC01_HAZMAT"]["ppe"]
    assert all("hazard" in z for z in ZONES.values()), [i for i, z in ZONES.items() if "hazard" not in z]


def test_buildings_do_not_overlap_and_hazmat_is_separated() -> None:
    boxes = [(b["id"], b["x"], b["z"], b["x"] + b["w"], b["z"] + b["d"]) for b in CAMPUS["buildings"]]
    boxes += [(f"layout:{b['id']}", b["x"], b["z"], b["x"] + b["w"], b["z"] + b["d"]) for b in LAYOUT["buildings"]]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[0].startswith("layout:") and b[0].startswith("layout:"):
                continue  # the cold room sits inside the factory hall, as before
            assert a[3] <= b[1] or b[3] <= a[1] or a[4] <= b[2] or b[4] <= a[2], f"{a[0]} overlaps {b[0]}"
    hz = next(b for b in boxes if b[0] == "HAZMAT")
    for o in boxes:
        if o[0] in ("HAZMAT",):
            continue
        dx = max(0, max(hz[1], o[1]) - min(hz[3], o[3]))
        dz = max(0, max(hz[2], o[2]) - min(hz[4], o[4]))
        d = math.hypot(dx, dz)
        # nothing is closer than 8 m; the occupied buildings (everything but the fire pump house, its own supply) are 12 m+ away
        assert d >= 8, f"{o[0]} is {d:.1f} m from the hazardous store"
        if o[0] not in ("FIRE_PUMP",):
            assert d >= 12, f"{o[0]} is {d:.1f} m from the hazardous store"


def test_buildings_stay_inside_their_site_bounds() -> None:
    for s in SITES["sites"]:
        for z in s["zones"]:
            for x, zz in z["polygon"]:
                assert s["bounds"]["x"][0] <= x <= s["bounds"]["x"][1] and s["bounds"]["z"][0] <= zz <= s["bounds"]["z"][1], z["id"]
    bx, bz = LAYOUT["bounds"]["x"], LAYOUT["bounds"]["z"]
    for b in CAMPUS["buildings"]:
        assert bx[0] <= b["x"] and b["x"] + b["w"] <= bx[1] and bz[0] <= b["z"] and b["z"] + b["d"] <= bz[1], b["id"]


def test_every_device_is_in_a_zone_and_every_kit_in_use() -> None:
    from twindock.devices import point_in_polygon
    for d in SITES["devices"]:
        z = ZONES[d["zone_id"]]
        if d["type"] == "badge":
            continue  # a badge starts at its worker's first stand and then walks
        assert point_in_polygon(d["x"], d["z"], z["polygon"]), f"{d['id']} is outside {d['zone_id']}"
    used = {d.get("kit") for d in SITES["devices"]}
    assert set(kit_ids()) - used == set()


def test_workers_walk_only_on_walkways() -> None:
    lanes = {frozenset((x["a"], x["b"])) for x in PED_LANES}
    for w in SITES["workers"]:
        if not w.get("campus"):
            continue
        r = w["routes"]["default"]
        for a, b in zip(r, r[1:] + r[:1]):
            assert frozenset((a, b)) in lanes, f"{w['id']} walks {a} -> {b} where there is no walkway"
        assert all(not NODES[n]["kinds"] for n in r)
    roles = {w["role"] for w in SITES["workers"]}
    assert {"security_guard", "maintenance", "utilities_operator", "etp_operator", "first_aider"} <= roles


def test_muster_points_are_clear_of_buildings_and_roads() -> None:
    for m in CAMPUS["muster_points"]:
        for b in CAMPUS["buildings"]:
            assert not (b["x"] - 3 <= m["x"] <= b["x"] + b["w"] + 3 and b["z"] - 3 <= m["z"] <= b["z"] + b["d"] + 3), f"{m['id']} is next to {b['id']}"
        for r in LAYOUT["roads"]:
            for q1, q2 in zip(r["points"], r["points"][1:]):
                half = r["width"] / 2
                if q1[0] == q2[0]:
                    assert not (abs(m["x"] - q1[0]) < half and min(q1[1], q2[1]) < m["z"] < max(q1[1], q2[1])), f"{m['id']} is on {r['id']}"
                else:
                    assert not (abs(m["z"] - q1[1]) < half and min(q1[0], q2[0]) < m["x"] < max(q1[0], q2[0])), f"{m['id']} is on {r['id']}"
    assert SITES["muster_points"] and {m["id"] for m in SITES["muster_points"]} == {m["id"] for m in CAMPUS["muster_points"]}


def test_campus_is_idempotent() -> None:
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[2]
    before = (WORLD / "layout.json").read_text(), (WORLD / "sites.json").read_text()
    subprocess.run([sys.executable, str(root / "tools" / "campus" / "gen_campus.py")], check=True, cwd=root, capture_output=True)
    assert ((WORLD / "layout.json").read_text(), (WORLD / "sites.json").read_text()) == before


@pytest.mark.parametrize("site", ["WH-01", "FAC-01"])
def test_sites_cover_the_whole_campus_without_overlapping(site: str) -> None:
    s = {x["id"]: x for x in SITES["sites"]}
    assert s["WH-01"]["bounds"]["x"][1] < s["FAC-01"]["bounds"]["x"][0]
    assert s[site]["bounds"]["z"] == [-12, 104]
