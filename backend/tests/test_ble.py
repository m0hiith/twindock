import pytest
from conftest import Harness

from twindock.ble_tracker import BleConfig, BleTracker, Zone, unit_for_tag

# Nearest first: right at Bay 1 (the board is beside the docks), then the main aisle.
ZONES = (Zone("DOCK_1", -55), Zone("MAIN_1", -70))


def scan(rssi: int, name: str = "TD-FL01") -> list[dict[str, object]]:
    return [{"name": name, "addr": "AA:BB:CC:DD:EE:01", "rssi_dbm": rssi}]


def tracked(h: Harness, zones: tuple[Zone, ...] = ZONES) -> Harness:
    h.engine.ble = BleTracker(BleConfig(zones=zones))
    h.board_online()
    return h


def feed(h: Harness, rssi: int, scans: int, name: str = "TD-FL01") -> None:
    """One scan every 2 s, like the firmware."""
    for _ in range(scans):
        h.mqtt_in("twin/gateway/ble", {"ts_ms": 1, "sightings": scan(rssi, name)})
        h.run(2)


def test_tag_names_map_to_forklifts() -> None:
    assert unit_for_tag("TD-FL01") == "FL-01"
    assert unit_for_tag("TD-FL12") == "FL-12"
    assert unit_for_tag("TD-TR01") is None
    assert unit_for_tag("TD-FL1") is None


def test_moving_average_over_last_five_readings() -> None:
    t = BleTracker(BleConfig(zones=ZONES, stable_s=0))
    for i, r in enumerate([-40, -40, -40, -40, -40, -90]):
        t.update(scan(r), i * 2000)
    track = t.tracks["TD-FL01"]
    assert list(track.readings) == [-40, -40, -40, -40, -90]
    assert track.avg == -50  # one bad reading moves the average 10 dB, not 50
    assert t.raw_zone(track) == "DOCK_1"


def test_zone_switches_only_after_three_stable_seconds() -> None:
    t = BleTracker(BleConfig(window=1, zones=ZONES, stable_s=3))
    assert t.update(scan(-50), 0) == []          # DOCK_1 pending since 0
    assert t.update(scan(-50), 2000) == []       # 2 s: not yet
    [c] = t.update(scan(-50), 4000)              # 4 s >= 3 s: commit
    assert (c.zone, c.first) == ("DOCK_1", True)
    # Flapping between zones never holds for 3 s, so the committed zone stays put.
    for i, r in enumerate([-60, -50, -60, -50, -60, -50]):
        assert t.update(scan(r), 6000 + i * 2000) == []
    assert t.tracks["TD-FL01"].zone == "DOCK_1"
    t.update(scan(-60), 20000)
    [c] = t.update(scan(-60), 23000)
    assert (c.zone, c.first) == ("MAIN_1", False)


def test_config_must_go_nearest_first() -> None:
    with pytest.raises(ValueError, match="strongest to weakest"):
        BleConfig(zones=(Zone("MAIN_1", -70), Zone("DOCK_1", -55))).check(None)
    with pytest.raises(ValueError, match="not a forklift node"):
        BleConfig(zones=(Zone("BAY_1", -55),)).check({"DOCK_1"})


def test_tag_makes_forklift_live_and_drives_it_to_the_zone(h: Harness) -> None:
    tracked(h)
    fl = h.world.entities["FL-01"]
    feed(h, -50, 2)  # only 2 s of agreement so far
    assert fl.source == "manual"
    feed(h, -50, 1)
    assert fl.source == "device" and fl.target == "DOCK_1"
    assert any("now tracked by tag TD-FL01" in e["text"] for e in h.of_type("event"))
    unit = [u for m in h.of_type("unit_update") for u in m["units"] if u["id"] == "FL-01"][-1]
    assert unit["source"] == "device"
    feed(h, -50, 5)  # keep the tag alive while it drives
    assert fl.node == "DOCK_1"
    tracks = h.of_type("ble_tracks")[-1]["tracks"]
    assert tracks[0]["unit_id"] == "FL-01" and tracks[0]["zone"] == "DOCK_1" and tracks[0]["readings"] == 5


def test_manual_commands_are_rejected_for_tracked_forklifts(h: Harness) -> None:
    tracked(h)
    feed(h, -50, 3)
    h.client({"type": "move_unit", "cmd_id": "c1", "unit_id": "FL-01", "target_node": "RACK_A2", "action": "goto"})
    ack = h.last_ack()
    assert not ack["ok"] and "tracked by the board" in ack["reason"]
    h.client({"type": "select_unit", "cmd_id": "c2", "unit_id": "FL-01"})
    h.press("BTN0", 50_000)
    assert any(e["text"] == "BTN0: FL-01 is tracked by the board" for e in h.of_type("event"))


def test_lost_tag_hands_forklift_back_to_manual(h: Harness) -> None:
    tracked(h)
    feed(h, -50, 3)
    fl = h.world.entities["FL-01"]
    assert fl.source == "device"
    h.run(11)  # no scans for longer than lost_after_s
    assert fl.source == "manual"
    assert any("TD-FL01 not seen for 10 s" in e["text"] for e in h.of_type("event"))
    assert h.of_type("ble_tracks")[-1]["tracks"] == []


def test_without_calibrated_zones_nothing_is_placed(h: Harness) -> None:
    tracked(h, zones=())
    feed(h, -40, 6)
    assert h.world.entities["FL-01"].source == "manual"
    t = h.of_type("ble_tracks")[-1]
    assert t["config"]["zones"] == [] and t["tracks"][0]["avg_rssi_dbm"] == -40 and t["tracks"][0]["zone"] is None


def test_unknown_tag_is_reported_not_mapped(h: Harness) -> None:
    tracked(h)
    feed(h, -50, 3, name="TD-FL09")
    assert any(e["text"] == "Tag TD-FL09 has no matching forklift" for e in h.of_type("event"))


def test_reset_returns_tracked_forklifts_to_manual_until_reacquired(h: Harness) -> None:
    tracked(h)
    feed(h, -50, 3)
    h.engine.reset()
    h.collect()
    fl = h.world.entities["FL-01"]
    assert fl.source == "manual"
    feed(h, -50, 3)
    assert fl.source == "device"
