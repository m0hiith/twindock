import math

from conftest import Harness
from twindock.world import SPEED, logistics_params


def move(h: Harness, unit: str, target: str, action: str = "goto", **kw: object) -> dict:
    h.client({"type": "move_unit", "cmd_id": f"c{len(h.ws)}", "unit_id": unit, "target_node": target,
              "action": action, **kw})
    return h.last_ack()


def test_truck_can_only_target_docks_or_gate(h: Harness) -> None:
    ack = move(h, "TR-02", "RACK_A1")
    assert not ack["ok"] and "dock or the gate" in ack["reason"]
    ack = move(h, "TR-02", "ZONE_A")
    assert not ack["ok"]
    assert move(h, "TR-02", "DOCK_3")["ok"]


def test_dock_holds_one_truck(h: Harness) -> None:
    ack = move(h, "TR-02", "DOCK_2")  # TR-01 is docked at Bay 2 in the seed
    assert not ack["ok"] and "occupied by TR-01" in ack["reason"]
    assert move(h, "TR-02", "DOCK_3")["ok"]
    assert move(h, "TR-01", "GATE_IN")["ok"]  # TR-01 leaves
    ack = move(h, "TR-01", "DOCK_3")
    assert not ack["ok"] and "reserved for TR-02" in ack["reason"]


def test_forklift_cannot_pick_a_carried_pallet(h: Harness) -> None:
    assert move(h, "FL-01", "RACK_A1", "pick")["ok"]
    h.run(25)
    w = h.world
    assert w.entities["FL-01"].carrying == "PL-01"
    ack = move(h, "FL-03", "RACK_A1", "pick", pallet_id="PL-01")
    assert not ack["ok"] and "already carried by FL-01" in ack["reason"]


def test_pallet_claim_blocks_second_forklift(h: Harness) -> None:
    assert move(h, "FL-01", "RACK_A2", "pick")["ok"]
    ack = move(h, "FL-03", "RACK_A2", "pick")
    assert not ack["ok"] and "No free pallet" in ack["reason"]


def test_dry_run_returns_path_without_moving(h: Harness) -> None:
    before = (h.world.entities["FL-01"].x, h.world.entities["FL-01"].z)
    ack = move(h, "FL-01", "DOCK_3", dry_run=True)
    assert ack["ok"] and ack["path"][0] == "MAIN_1" and ack["path"][-1] == "DOCK_3"
    h.run(2)
    fl = h.world.entities["FL-01"]
    assert (fl.x, fl.z) == before and fl.state == "idle"


def test_forklift_drives_at_realistic_speed_and_heading_follows_path(h: Harness) -> None:
    w = h.world
    ack = move(h, "FL-01", "DOCK_1")  # straight south, 6.5 m
    assert ack["path"] == ["MAIN_1", "DOCK_1"]
    h.run(1.5)
    fl = w.entities["FL-01"]
    assert fl.state == "driving" and fl.node is None
    assert math.isclose(fl.heading, math.pi / 2, abs_tol=0.05)  # facing south
    assert fl.speed <= SPEED["forklift"] + 1e-9
    h.run(6)
    assert fl.node == "DOCK_1" and fl.state == "idle" and fl.speed == 0


def test_full_pick_and_load_cycle(h: Harness) -> None:
    w = h.world
    assert move(h, "FL-01", "RACK_A1", "pick")["ok"]
    h.run(25)
    assert w.entities["FL-01"].carrying == "PL-01"
    ack = move(h, "FL-01", "DOCK_2", "load")
    assert ack["ok"], ack
    h.run(35)  # rack slots sit 0.6 m into the rack face (traffic: they don't block the aisle)
    tr = w.entities["TR-01"]
    assert "PL-01" in (tr.cargo or [])
    assert w.entities["PL-01"].holder == "TR-01"
    assert w.entities["FL-01"].carrying is None


def test_drop_requires_carrying_and_space(h: Harness) -> None:
    ack = move(h, "FL-01", "RACK_B4", "drop")
    assert not ack["ok"] and "not carrying" in ack["reason"]
    assert move(h, "FL-03", "ZONE_A", "pick")["ok"]
    h.run(25)
    ack = move(h, "FL-03", "RACK_A1", "drop")
    assert not ack["ok"] and "full" in ack["reason"]
    assert move(h, "FL-03", "RACK_B4", "drop")["ok"]


def test_charger_holds_one_forklift(h: Harness) -> None:
    ack = move(h, "FL-01", "CHARGER_C1", "charge")  # FL-02 charges there in the seed
    assert not ack["ok"] and "FL-02" in ack["reason"]
    assert move(h, "FL-01", "CHARGER_C2")["ok"]  # goto a charger means charge
    assert h.world.entities["FL-01"].action == "charge"


def test_battery_drain_is_physical_over_15_minutes(h: Harness) -> None:
    """15 min of nonstop driving uses a few percent of a 400 Ah battery (rolling resistance + standby), and the
    amp-hour books balance: what was drawn is exactly what the state of charge lost."""
    w = h.world  # drive the world directly: 15 simulated minutes of nonstop driving
    fl = w.entities["FL-01"]
    start = fl.battery or 0.0
    targets = ["DOCK_3", "CHARGER_C2", "ZONE_A", "RACK_B4"]  # passing through, never charging
    for i in range(int(15 * 60 / 0.1)):
        if not fl.moving:
            assert w.command("FL-01", targets[i % 4], "goto").ok
            fl.action = None if fl.action == "charge" else fl.action  # drive past, don't charge
        w.tick(0.1)
        if fl.state == "charging":
            fl.state, fl.action = "idle", None
    used_pct = start - (fl.battery or 0.0)
    assert 0.5 < used_pct < 5.0, used_pct
    cap = logistics_params().f("logistics.forklift.capacity_ah")
    assert abs((fl.ah_used - fl.ah_charged) - used_pct / 100 * cap) < 1e-6  # drawn − charged = what the SOC lost


def test_device_units_reject_manual_moves(h: Harness) -> None:
    h.world.entities["FL-04"].source = "device"
    ack = move(h, "FL-04", "DOCK_2")
    assert not ack["ok"] and "tracked by the board" in ack["reason"]


def test_static_units_cannot_move(h: Harness) -> None:
    assert not move(h, "DK-01", "DOCK_2")["ok"]
    assert not move(h, "XX-99", "DOCK_2")["ok"]


def test_truck_backs_into_bay_and_docks(h: Harness) -> None:
    w = h.world
    assert move(h, "TR-02", "DOCK_1")["ok"]
    h.run(60)
    tr = w.entities["TR-02"]
    assert tr.state == "docked" and tr.docked_at == "DOCK_1"
    assert math.isclose(tr.heading, math.pi / 2, abs_tol=1e-6)  # cab towards the yard
    assert w.entities["DK-01"].state == "occupied"


def test_departing_truck_frees_the_dock_and_goes_off_site(h: Harness) -> None:
    w = h.world
    ack = move(h, "TR-01", "GATE_IN")
    assert ack["ok"] and ack["path"][-1] == "ROAD_E"
    assert w.entities["DK-02"].state == "available"
    h.run(60)
    tr = w.entities["TR-01"]
    assert tr.state == "gone" and tr.inbound  # it left with 2 pallets, so it returns to be unloaded


def test_invalid_message_is_rejected_with_reason(h: Harness) -> None:
    h.client({"type": "move_unit", "cmd_id": "x1", "unit_id": "FL-01"})
    ack = h.last_ack()
    assert not ack["ok"] and "Invalid message" in ack["reason"]
    h.client({"type": "teleport", "cmd_id": "x2"})
    assert h.of_type("event")[-1]["level"] == "error"
