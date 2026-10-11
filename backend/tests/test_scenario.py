"""S10: demo scenario runner. Every beat drives only the simulator and the engine, never the board."""

from __future__ import annotations

from conftest import Harness

BEATS = {
    "degrade": ["twin/FAC-01/MM-01/cmd/degrade"],
    "visitor": ["twin/FAC-01/BG-04/cmd/route"],
    "cold_door": ["twin/FAC-01/DR-01/cmd/door_open"],
    "stale": ["twin/FAC-01/AQ-01/cmd/silence"],
}


def run_beat(h: Harness, beat: str) -> None:
    h.client({"type": "scenario_command", "cmd_id": f"s-{beat}", "beat": beat})


def test_each_beat_sends_only_simulator_commands(h: Harness) -> None:
    h.board_online()
    for beat, topics in BEATS.items():
        before = len(h.mqtt)
        run_beat(h, beat)
        assert h.last_ack()["ok"], h.last_ack()
        assert [o.topic for o in h.mqtt[before:]] == topics
    assert all(not o.topic.startswith("twin/gateway/") or o.payload.get("led") == "LED0" for o in h.mqtt)
    route = next(o for o in h.mqtt if o.topic == "twin/FAC-01/BG-04/cmd/route")
    assert route.payload["route"] == "press_visit"


def test_near_miss_sends_a_forklift_and_the_worker(h: Harness) -> None:
    h.engine.set_mqtt_connected(True)
    run_beat(h, "near_miss")
    assert h.last_ack()["ok"]
    movers = [f for f in h.world.of_kind("forklift") if f.target == "FAC_OUT"]
    assert len(movers) == 1
    assert any(o.topic == "twin/FAC-01/BG-02/cmd/route" and o.payload["route"] == "outbound" for o in h.mqtt)


def test_beats_need_the_broker(h: Harness) -> None:
    run_beat(h, "degrade")  # mqtt not connected in the harness by default
    assert not h.last_ack()["ok"] and "MQTT" in h.last_ack()["reason"]


def test_reset_restores_world_and_simulator(h: Harness) -> None:
    h.engine.set_mqtt_connected(True)
    run_beat(h, "near_miss")
    h.run(3.0)
    h.engine.safety.today.warnings = 3
    before = len(h.mqtt)
    run_beat(h, "reset")
    assert h.last_ack()["ok"]
    sent = {o.topic: o.payload for o in h.mqtt[before:]}
    assert sent["twin/FAC-01/MM-01/cmd/restore"]["cmd_id"]
    assert sent["twin/FAC-01/BG-02/cmd/route"]["route"] == "default"
    assert sent["twin/FAC-01/AQ-01/cmd/silence"]["on"] is False
    assert sent["twin/FAC-01/DR-01/cmd/door_close"]
    assert not any(f.target == "FAC_OUT" for f in h.world.of_kind("forklift"))
    assert h.engine.safety.today.warnings == 0
    assert h.world.entities["M-01"].kind == "machine" and h.world.entities["WK-01"].kind == "worker"
    assert h.of_type("world_snapshot")  # every screen gets the reset world
