"""S0: site/zone/device model, topic parsing, staleness, and the GW-01 isolation guarantee."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from conftest import Harness

from twindock.contract import def_validator, first_error, mqtt_validator, validator
from twindock.devices import load_sites, parse_site_topic, point_in_polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SiteSim, select_devices  # noqa: E402

HELLO_MM = {"type": "machine_monitor", "protocol": "wifi", "fw_version": "sim-2.3", "source": "sim",
            "capabilities": ["state", "cycle_time_s", "current_a", "vibration_rms", "units"]}


def sim_in(h: Harness, topic: str, payload: dict | None) -> None:
    h.engine.on_mqtt(topic, b"" if payload is None else json.dumps(payload).encode())
    h.collect()


def test_sites_file_is_valid() -> None:
    cfg = load_sites()
    assert {s["id"] for s in cfg["sites"]} == {"WH-01", "FAC-01"}
    assert {z["kind"] for z in next(s for s in cfg["sites"] if s["id"] == "FAC-01")["zones"]} >= {
        "production", "cold_room", "docks", "office"}
    real = [d for d in cfg["devices"] if d["source"] == "device"]
    # GW-01 (the board) and RB-01 (a real badge seen only through the board's BLE scans)
    assert [d["id"] for d in real] == ["GW-01", "RB-01"]


def test_snapshot_devices_validate(h: Harness) -> None:
    h.engine.on_connect("client-1")
    h.collect()  # the harness schema-checks world_snapshot (sites + devices included)
    snap = h.of_type("world_snapshot")[-1]
    ids = {d["id"] for d in snap["devices"]}
    assert "GW-01" in ids and "MM-01" in ids
    for d in snap["devices"]:
        assert first_error(def_validator("device"), d) is None
    gw = next(d for d in snap["devices"] if d["id"] == "GW-01")
    assert gw["source"] == "device" and gw["status"] == "offline" and gw["last_seen_ms"] is None


def test_topic_parsing() -> None:
    assert parse_site_topic("twin/FAC-01/MM-01/vibration_rms") == ("FAC-01", "MM-01", "vibration_rms")
    assert parse_site_topic("twin/WH-01/EN-03/hello") == ("WH-01", "EN-03", "hello")
    assert parse_site_topic("twin/gateway/status") is None          # the board's topics are not site topics
    assert parse_site_topic("twin/gateway/cmd/led") is None
    assert parse_site_topic("twin/fac-01/MM-01/state") is None       # site id is upper case
    assert parse_site_topic("twin/FAC-01/MM-01/Bad") is None         # channel is snake_case
    assert parse_site_topic("twin/FAC-01/MM-01/cmd/degrade") is None  # commands are not readings


def test_sim_device_goes_stale_then_offline(h: Harness) -> None:
    sim_in(h, "twin/FAC-01/MM-01/hello", HELLO_MM)
    sim_in(h, "twin/FAC-01/MM-01/vibration_rms", {"ts_ms": 1, "value": 2.1, "unit": "mm/s", "source": "sim"})
    h.run(1.0)
    dev = lambda: h.engine.devices.wire_device("MM-01", h.engine.gw, h.clock.ms)  # noqa: E731
    assert dev()["status"] == "online"
    assert dev()["readings"]["vibration_rms"]["value"] == 2.1
    h.run(15.0)
    assert dev()["status"] == "stale"
    h.run(46.0)
    assert dev()["status"] == "offline"
    # a fault report wins over freshness
    sim_in(h, "twin/FAC-01/MM-01/status", {"ts_ms": 2, "fault": "Motor overcurrent", "source": "sim"})
    assert dev()["status"] == "fault"
    # device_update messages carried the transitions (schema-checked by the harness)
    h.run(1.0)
    statuses = [d["status"] for m in h.of_type("device_update") for d in m["devices"] if d["id"] == "MM-01"]
    assert ["online", "stale", "offline", "fault"] == [s for i, s in enumerate(statuses) if i == 0 or statuses[i - 1] != s]


def test_sim_messages_never_touch_the_real_board(h: Harness) -> None:
    h.board_online()
    h.mqtt_in("twin/gateway/led", {"ts_ms": 2000, "led": "LED1", "on": True})
    gw_before = copy.deepcopy(h.engine.gw.wire().model_dump(mode="json"))
    mqtt_before = len(h.mqtt)
    attacks = [
        ("twin/WH-01/GW-01/hello", {**HELLO_MM, "type": "gateway"}),
        ("twin/WH-01/GW-01/status", {"ts_ms": 5, "battery_pct": 1, "source": "sim"}),
        ("twin/WH-01/GW-01/led", {"ts_ms": 5, "value": False, "source": "sim"}),
        ("twin/FAC-01/GW-01/button", {"ts_ms": 5, "value": "pressed", "source": "sim"}),
        ("twin/FAC-01/MM-01/hello", HELLO_MM),
        ("twin/FAC-01/MM-01/state", {"ts_ms": 5, "value": "running", "source": "sim"}),
        ("twin/FAC-01/MM-01/led", {"ts_ms": 5, "value": True, "source": "sim"}),  # not a capability
        ("twin/FAC-01/XX-99/hello", HELLO_MM),                                     # not commissioned
        ("twin/FAC-01/EN-01/hello", {**HELLO_MM, "source": "device"}),              # claims to be real
    ]
    for topic, payload in attacks:
        sim_in(h, topic, payload)
    h.run(2.0)
    assert h.engine.gw.wire().model_dump(mode="json") == gw_before
    assert len(h.mqtt) == mqtt_before, "a sim message caused MQTT output"
    assert all(not o.topic.startswith("twin/gateway/cmd") or o.payload.get("led") == "LED0" for o in h.mqtt)
    texts = [e["text"] for e in h.of_type("event")]
    assert any("GW-01 is a real device" in t for t in texts)
    assert any("XX-99 is not commissioned" in t for t in texts)
    # GW-01's device entry follows only the board's own status
    gw01 = h.engine.devices.wire_device("GW-01", h.engine.gw, h.clock.ms)
    assert gw01["source"] == "device" and gw01["status"] == "online" and gw01["battery_pct"] is None
    h.run(16.0)
    assert h.engine.devices.wire_device("GW-01", h.engine.gw, h.clock.ms)["status"] == "stale"


def test_hello_must_match_commissioning(h: Harness) -> None:
    sim_in(h, "twin/FAC-01/MM-01/hello", {**HELLO_MM, "type": "badge"})
    assert h.engine.devices.sim["MM-01"].hello is None
    sim_in(h, "twin/FAC-01/MM-01/state", {"ts_ms": 1, "value": "running", "source": "sim"})
    assert "state" not in h.engine.devices.sim["MM-01"].readings  # no hello yet: dropped


def test_select_accepts_devices(h: Harness) -> None:
    h.client({"type": "select_unit", "cmd_id": "s1", "unit_id": "EN-01"})
    assert h.last_ack()["ok"] and h.engine.selected == "EN-01"


def test_point_in_polygon() -> None:
    sq = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert point_in_polygon(5, 5, sq) and not point_in_polygon(11, 5, sq)


def test_simulator_payloads_are_valid_and_never_real() -> None:
    cfg = json.loads((Path(__file__).resolve().parents[1] / "world" / "sites.json").read_text())
    devices = select_devices(cfg, None, None)
    assert devices and all(d["source"] == "sim" for d in devices)
    assert "GW-01" not in {d["id"] for d in devices}
    s = SiteSim(cfg, devices, seed=1)
    sent: list[tuple[str, dict]] = []
    s.publish = lambda m, ch, p, retain=False: sent.append((s.topic(m, ch), p))  # type: ignore[method-assign]
    s.hellos()
    for _ in range(200):
        s.step(0.25)
    assert sent and all(not t.startswith("twin/gateway/") for t, _ in sent)
    for t, p in sent:
        ch = t.rsplit("/", 1)[1]
        name = "mqtt/site_hello" if ch == "hello" else "mqtt/site_status" if ch == "status" else "mqtt/site_reading"
        assert first_error(validator(name), p) is None, (t, p)
        assert p["source"] == "sim"
    assert mqtt_validator  # imported for parity with the board tests


def test_zone_filter() -> None:
    cfg = json.loads((Path(__file__).resolve().parents[1] / "world" / "sites.json").read_text())
    assert {d["zone_id"] for d in select_devices(cfg, None, ["cold_room"])} == {"FAC01_COLD"}
    assert {d["site_id"] for d in select_devices(cfg, "WH-01", None)} == {"WH-01"}
    s = SiteSim(cfg, [cfg["devices"][1]], seed=1)
    assert s.models[cfg["devices"][1]["id"]].hello()["fw_version"].startswith("sim-")
