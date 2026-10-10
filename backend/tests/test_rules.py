"""S6: every rule fires and resolves; acknowledge/resolve lifecycle; durations; no alerts on missing data."""

from __future__ import annotations

import json

from conftest import Harness

from twindock.rules import Clause, Rules, load_rules

HELLO = {
    "MM-01": {"type": "machine_monitor", "protocol": "wifi", "capabilities": ["state", "vibration_rms", "alarm"]},
    "DR-01": {"type": "door_sensor", "protocol": "thread", "capabilities": ["open"]},
    "EN-01": {"type": "env_sensor", "protocol": "thread", "capabilities": ["temperature", "humidity"]},
    "AQ-01": {"type": "air_quality", "protocol": "wifi", "capabilities": ["co2_ppm", "pm25_ugm3"]},
    "BG-04": {"type": "badge", "protocol": "ble", "capabilities": ["position"]},
    "BG-02": {"type": "badge", "protocol": "ble", "capabilities": ["position"]},
}


def hello(h: Harness, dev: str) -> None:
    p = {**HELLO[dev], "fw_version": "sim-1.0", "source": "sim"}
    h.engine.on_mqtt(f"twin/FAC-01/{dev}/hello", json.dumps(p).encode())
    h.collect()


def reading(h: Harness, dev: str, ch: str, value) -> None:  # type: ignore[no-untyped-def]
    h.engine.on_mqtt(f"twin/FAC-01/{dev}/{ch}", json.dumps({"ts_ms": 1, "value": value, "source": "sim"}).encode())
    h.collect()


def hold(h: Harness, seconds: float, dev: str, ch: str, value) -> None:  # type: ignore[no-untyped-def]
    """Keep sending the same reading every 5 s (devices stay online) for `seconds`."""
    t = 0.0
    while t < seconds:
        reading(h, dev, ch, value)
        h.run(min(5.0, seconds - t))
        t += 5.0


def open_alerts(h: Harness) -> dict[str, dict]:
    msgs = h.of_type("alerts_update")
    if not msgs:
        return {}
    return {a["rule_id"]: a for a in msgs[-1]["alerts"] if a["state"] != "resolved"}


def resolved(h: Harness, rule: str) -> bool:
    return any(a["rule_id"] == rule and a["state"] == "resolved" for a in h.of_type("alerts_update")[-1]["alerts"])


def test_rule_files_load_and_read_in_plain_language() -> None:
    rules = load_rules()
    ids = {r.id for r in rules}
    assert ids >= {"machine_fault", "abnormal_vibration", "outbound_backlog", "proximity_warning", "proximity_critical",
                   "restricted_zone", "cold_room_door_open", "cold_room_temperature", "air_quality_co2", "gateway_offline"}
    for r in rules:
        assert len(r.plain) > 20 and r.plain[0].isupper()


def test_clause_never_matches_missing_data() -> None:
    assert not Clause("temperature", "gt", 5).holds({})
    assert not Clause("temperature", "outside", [0, 5]).holds({"temperature": None})
    assert Clause("temperature", "outside", [0, 5]).holds({"temperature": 7.2})
    assert not Clause("x", "gt", 1).holds({"x": "text"})  # type mismatch is not a match


def test_machine_fault_fires_and_resolves(h: Harness) -> None:
    hello(h, "MM-01")
    reading(h, "MM-01", "alarm", "Die jam")
    reading(h, "MM-01", "state", "fault")
    h.run(1.0)
    a = open_alerts(h)["machine_fault"]
    assert a["severity"] == "critical" and "fault (Die jam)" in a["message"] and a["target"]["unit_id"] == "M-01"
    assert a["target"]["site_id"] == "FAC-01" and "x" in a["target"]
    reading(h, "MM-01", "state", "running")
    h.run(1.0)
    assert "machine_fault" not in open_alerts(h) and resolved(h, "machine_fault")


def test_abnormal_vibration_fires_and_resolves(h: Harness) -> None:
    hello(h, "MM-01")
    reading(h, "MM-01", "state", "running")
    h.engine.production.machines["M-01"].base.abnormal = True
    h.engine.production.machines["M-01"].base.z = 3.4
    h.run(1.0)
    assert "z = 3.4" in open_alerts(h)["abnormal_vibration"]["message"]
    h.engine.production.machines["M-01"].base.abnormal = False
    h.run(1.0)
    assert resolved(h, "abnormal_vibration")


def test_machine_with_stale_monitor_raises_nothing(h: Harness) -> None:
    hello(h, "MM-01")
    reading(h, "MM-01", "state", "fault")
    h.run(1.0)
    assert "machine_fault" in open_alerts(h)
    h.run(16.0)  # monitor silent: the fault is no longer a known current state
    assert "machine_fault" not in open_alerts(h)


def test_outbound_backlog_after_30_s(h: Harness) -> None:
    for i in range(4):
        assert h.world.spawn_pallet("FAC_OUT", {"sku": f"FG-{i}"})
    h.engine.production.pallets_waiting = 1
    h.run(20.0)
    assert "outbound_backlog" not in open_alerts(h)
    h.run(11.0)
    assert open_alerts(h)["outbound_backlog"]["severity"] == "warning"
    h.engine.production.pallets_waiting = 0
    h.run(1.0)
    assert resolved(h, "outbound_backlog")


def test_restricted_zone_fires_and_resolves(h: Harness) -> None:
    hello(h, "BG-04")
    reading(h, "BG-04", "position", [122.0, 12.2])  # visitor in the press area
    h.run(1.0)
    a = open_alerts(h)["restricted_zone"]
    assert a["severity"] == "critical" and "WK-04 (visitor) entered restricted Press area" == a["message"]
    reading(h, "BG-04", "position", [108.0, 14.0])
    h.run(1.0)
    assert resolved(h, "restricted_zone")


def test_proximity_fires_and_resolves(h: Harness) -> None:
    hello(h, "BG-02")
    assert h.world.command("FL-04", "FAC_OUT", "goto", source="manual").ok
    fired = False
    for _ in range(200):
        reading(h, "BG-02", "position", [75.0, 20.2])
        h.run(0.25)
        if {"proximity_warning", "proximity_critical"} & set(open_alerts(h)):
            fired = True
            break
    assert fired
    a = next(v for k, v in open_alerts(h).items() if k.startswith("proximity"))
    assert "Pedestrian near forklift: WK-02 (logistics)" in a["message"] and "FL-04" in a["message"]
    for _ in range(80):  # forklift drives on and away
        reading(h, "BG-02", "position", [75.0, 20.2])
        h.run(0.25)
    assert not {"proximity_warning", "proximity_critical"} & set(open_alerts(h))


def test_cold_room_door_open_after_60_s(h: Harness) -> None:
    hello(h, "DR-01")
    hold(h, 55.0, "DR-01", "open", True)
    assert "cold_room_door_open" not in open_alerts(h)
    hold(h, 10.0, "DR-01", "open", True)
    assert "cold_room_door_open" in open_alerts(h)
    reading(h, "DR-01", "open", False)
    h.run(1.0)
    assert resolved(h, "cold_room_door_open")


def test_cold_room_temperature_out_of_range(h: Harness) -> None:
    hello(h, "EN-01")
    hold(h, 35.0, "EN-01", "temperature", 7.4)
    assert "7.4 °C" in open_alerts(h)["cold_room_temperature"]["message"]
    reading(h, "EN-01", "temperature", 3.1)
    h.run(1.0)
    assert resolved(h, "cold_room_temperature")


def test_air_quality(h: Harness) -> None:
    hello(h, "AQ-01")
    hold(h, 65.0, "AQ-01", "co2_ppm", 1240)
    assert "1240 ppm" in open_alerts(h)["air_quality_co2"]["message"]
    reading(h, "AQ-01", "co2_ppm", 700)
    h.run(1.0)
    assert resolved(h, "air_quality_co2")


def test_gateway_offline_only_after_being_online(h: Harness) -> None:
    h.engine.set_mqtt_connected(True)
    h.run(20.0)  # never seen: Waiting for device, not an alert
    assert "gateway_offline" not in open_alerts(h)
    h.board_online()
    h.run(1.0)
    h.run(16.0)
    a = open_alerts(h)["gateway_offline"]
    assert a["severity"] == "critical" and a["target"]["unit_id"] == "GW-01"
    h.mqtt_in("twin/gateway/status", {"ts_ms": 30_000, "uptime_s": 30})
    h.run(1.0)
    assert resolved(h, "gateway_offline")


def test_acknowledge_then_resolve(h: Harness) -> None:
    hello(h, "MM-01")
    reading(h, "MM-01", "state", "fault")
    h.run(1.0)
    aid = open_alerts(h)["machine_fault"]["id"]
    h.client({"type": "ack_alert", "cmd_id": "k1", "alert_id": aid, "by": "Control Room (phone)"})
    assert h.last_ack()["ok"]
    a = open_alerts(h)["machine_fault"]
    assert a["state"] == "acknowledged" and a["acknowledged_by"] == "Control Room (phone)" and a["acknowledged_ms"]
    h.client({"type": "ack_alert", "cmd_id": "k2", "alert_id": aid, "by": "Twin"})
    assert not h.last_ack()["ok"] and "Already acknowledged" in h.last_ack()["reason"]
    reading(h, "MM-01", "state", "running")
    h.run(1.0)
    done = next(x for x in h.of_type("alerts_update")[-1]["alerts"] if x["id"] == aid)
    assert done["state"] == "resolved" and done["acknowledged_by"] == "Control Room (phone)" and done["resolved_ms"]
    h.client({"type": "ack_alert", "cmd_id": "k3", "alert_id": aid, "by": "Twin"})
    assert h.last_ack()["reason"] == "Already resolved"
    h.client({"type": "ack_alert", "cmd_id": "k4", "alert_id": "A99999", "by": "Twin"})
    assert not h.last_ack()["ok"]


def test_open_alerts_sorted_critical_first() -> None:
    from twindock.rules import Rule
    r = Rules([Rule("w", "W", "Warn on x.", "line", "warning", "w {id}", (), (Clause("x", "eq", 1),)),
               Rule("c", "C", "Crit on y.", "line", "critical", "c {id}", (), (Clause("y", "eq", 1),))])
    r.evaluate({"line": [{"id": "L", "x": 1, "y": 0}]}, 1000)
    r.evaluate({"line": [{"id": "L", "x": 1, "y": 1}]}, 2000)
    assert [a["rule_id"] for a in r.wire()["alerts"]] == ["c", "w"]
