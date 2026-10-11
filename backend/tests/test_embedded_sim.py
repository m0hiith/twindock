"""Embedded simulator (no broker, e.g. the Vercel deploy): SIM devices report, the board is never touched."""

from __future__ import annotations

from conftest import Harness

from twindock.embedded_sim import EmbeddedSim


def test_embedded_sim_feeds_sim_devices_and_never_the_board(h: Harness) -> None:
    e = h.engine
    sim = EmbeddedSim(e, seed=2)
    sim.start()
    assert e.sim_reachable and not e.mqtt_connected
    for _ in range(40):
        h.clock.ms += 250
        sim.step(0.25)
        e.tick(0.25)
        h.collect()
        for o in h.mqtt:
            assert o.topic != "twin/gateway/cmd/led"
            assert sim.command(o.topic, o.payload)
        h.mqtt.clear()
    snap = e.snapshot().model_dump(mode="json")["devices"]
    by = {d["id"]: d for d in snap}
    sims = [d for d in snap if d["source"] == "sim"]
    assert sims and all(d["status"] == "online" for d in sims), [d["id"] for d in sims if d["status"] != "online"]
    assert by["PM-05"]["readings"], "the generator meter reports"
    assert by["GW-01"]["status"] == "offline" and not by["GW-01"]["readings"]  # the real board is never simulated
    assert e.gw.hello is None and not e.gw.online


def test_demo_beats_work_without_a_broker(h: Harness) -> None:
    sim = EmbeddedSim(h.engine, seed=2)
    sim.start()
    h.client({"type": "scenario_command", "cmd_id": "b1", "beat": "degrade"})
    assert h.last_ack()["ok"], h.last_ack()
    h.collect()
    assert any(o.topic == "twin/FAC-01/MM-01/cmd/degrade" for o in h.mqtt)
