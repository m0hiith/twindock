import math

from twindock.graph import Graph, load_layout


def graph() -> Graph:
    return Graph(load_layout())


def test_forklift_short_path_inside_warehouse() -> None:
    assert graph().shortest_path("forklift", "MAIN_1", "DOCK_1") == ["MAIN_1", "DOCK_1"]


def test_path_goes_through_aisle_to_rack_slot() -> None:
    p = graph().shortest_path("forklift", "MAIN_1", "RACK_A3")
    assert p is not None and p[0] == "MAIN_1" and p[-1] == "RACK_A3"
    assert p[-2] == "AISLE_3"  # rack slots are spurs off their own aisle node


def test_path_is_shortest_by_distance() -> None:
    g = graph()
    p = g.shortest_path("forklift", "RACK_A1", "DOCK_3")
    assert p is not None
    # West route via AISLE_W/MAIN_W is longer than the east route via AISLE_E/MID_E/MAIN_E? Check by brute force.
    alt_w = ["RACK_A1", "AISLE_1", "AISLE_W", "MAIN_W", "MAIN_1", "MAIN_2", "MAIN_3", "DOCK_3"]
    alt_e = ["RACK_A1", "AISLE_1", "AISLE_2", "AISLE_3", "AISLE_4", "AISLE_E", "MID_E", "MAIN_E", "MAIN_3", "DOCK_3"]
    assert g.path_length(p) <= min(g.path_length(alt_w), g.path_length(alt_e)) + 1e-9


def test_trucks_and_forklifts_use_separate_lanes() -> None:
    g = graph()
    assert g.shortest_path("truck", "GATE_IN", "BAY_1") == ["GATE_IN", "YARD_E", "YARD_3", "YARD_2", "YARD_1", "BAY_1"]
    assert g.shortest_path("forklift", "MAIN_1", "BAY_1") is None
    assert g.shortest_path("truck", "GATE_IN", "RACK_A1") is None


def test_every_node_is_connected_for_its_kinds() -> None:
    g = graph()
    for kind, home in (("forklift", "MAIN_1"), ("truck", "GATE_IN")):
        for n in g.nodes.values():
            if kind in n.kinds:
                assert g.shortest_path(kind, home, n.id) is not None, f"{n.id} unreachable for {kind}"


def test_trucks_reverse_into_bays_only() -> None:
    g = graph()
    assert g.is_reverse("YARD_1", "BAY_1")
    assert not g.is_reverse("BAY_1", "YARD_1")
    assert not g.is_reverse("YARD_2", "YARD_1")


def test_same_node_path() -> None:
    assert graph().shortest_path("forklift", "DOCK_2", "DOCK_2") == ["DOCK_2"]
    assert math.isclose(graph().path_length(["DOCK_2"]), 0.0)
