"""S2: machine state machine (simulator), vibration baseline/z-score, OEE, line output to pallets."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest
from conftest import Harness

from twindock import planner
from twindock.production import Baseline, oee

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from sim_models import MachineMonitor  # noqa: E402

SITES = json.loads((Path(__file__).resolve().parents[1] / "world" / "sites.json").read_text())
MM01 = next(d for d in SITES["devices"] if d["id"] == "MM-01")
MM02 = next(d for d in SITES["devices"] if d["id"] == "MM-02")
HELLO = {"type": "machine_monitor", "protocol": "wifi", "fw_version": "sim-2.3", "source": "sim",
         "capabilities": MM01["capabilities"]}


def run_sim(m: MachineMonitor, seconds: float, t0: float = 0.0, dt: float = 0.25) -> list[tuple[float, str, dict]]:
    out = []
    t = t0
    while t < t0 + seconds:
        t += dt
        for ch, p in m.step(t, dt, int(t * 1000)):
            out.append((t, ch, p))
    return out


# ------------------------------------------------------------------ simulator state machine

def test_machine_states_and_production() -> None:
    m = MachineMonitor(MM01, random.Random(3))
    out = run_sim(m, 1800)
    states = {p["value"] for _, ch, p in out if ch == "state"}
    assert states <= {"running", "idle", "fault", "maintenance"}
    assert {"running", "idle", "fault"} <= states  # over 30 min all three happen
    units = [p["value"] for _, ch, p in out if ch == "units"]
    assert units == sorted(units) and units[-1] > 100  # cumulative, ~6 s cycles
    # alarms only accompany faults
    assert all(p["value"] in MM01["sim"]["alarms"] for _, ch, p in out if ch == "alarm")


def test_no_production_outside_running() -> None:
    m = MachineMonitor(MM01, random.Random(1))
    m.command("maintenance", 0.0, 0)
    before = m.units
    run_sim(m, 25)
    assert m.state == "maintenance" and m.units == before
    run_sim(m, 10, t0=25)
    assert m.state == "running"


def test_degrade_raises_vibration_and_restore_clears() -> None:
    m = MachineMonitor(MM01, random.Random(2))
    m.state_until = 10_000  # keep it running
    base = [p["value"] for _, ch, p in run_sim(m, 30) if ch == "vibration_rms"]
    m.command("degrade", 30, 30_000)
    worn = [p["value"] for _, ch, p in run_sim(m, 90, t0=30) if ch == "vibration_rms"]
    assert sum(worn[-10:]) / 10 > sum(base) / len(base) + 1.0
    m.command("restore", 120, 120_000)
    back = [p["value"] for _, ch, p in run_sim(m, 20, t0=120) if ch == "vibration_rms"]
    assert abs(sum(back) / len(back) - sum(base) / len(base)) < 0.3


# ------------------------------------------------------------------ baseline / z-score

def make_baseline() -> Baseline:
    return Baseline(baseline_s=90, min_samples=40, window=10, z_threshold=3.0, z_clear=2.0)


def test_baseline_learns_then_flags_and_clears() -> None:
    rng = random.Random(5)
    b = make_baseline()
    t = 0
    for _ in range(100):  # 100 s of normal running
        t += 1000
        assert b.add(2.8 + rng.gauss(0, 0.15), t) is None
    assert b.learned and abs(b.stats.mean - 2.8) < 0.1 and 0.08 < b.stats.std < 0.25
    for _ in range(60):  # still normal: never flagged
        t += 1000
        assert b.add(2.8 + rng.gauss(0, 0.15), t) is None
    assert not b.abnormal and b.z is not None and abs(b.z) < 2
    events = []
    for i in range(120):  # slow rise of 0.015 mm/s per s (the "degrade" control)
        t += 1000
        events.append(b.add(2.8 + 0.015 * i + rng.gauss(0, 0.15), t))
    assert "raised" in events and b.abnormal
    raised_at = events.index("raised")
    assert 20 < raised_at < 90  # visible within a minute or so, not instantly
    for _ in range(30):
        t += 1000
        r = b.add(2.8 + rng.gauss(0, 0.15), t)
        if r:
            events.append(r)
    assert events[-1] == "cleared" and not b.abnormal


def test_baseline_needs_time_and_samples() -> None:
    b = make_baseline()
    for i in range(200):  # many samples but only 20 s: not learned yet
        b.add(1.0, i * 100)
    assert not b.learned


# ------------------------------------------------------------------ OEE

def test_oee_formula() -> None:
    r = oee(running_ms=80_000, planned_ms=100_000, ideal_cycle_s=6.0, good=12, rejects=0)
    assert r["availability"] == pytest.approx(0.8)
    assert r["performance"] == pytest.approx(6 * 12 / 80)
    assert r["quality"] == pytest.approx(1.0)
    assert r["oee"] == pytest.approx(0.8 * 0.9 * 1.0)
    r = oee(80_000, 100_000, 8.0, 9, 1)
    assert r["quality"] == pytest.approx(0.9)
    assert r["performance"] == pytest.approx(8 * 10 / 80)
    assert oee(0, 0, 6.0, 0, 0)["oee"] is None  # no data, no number
    assert oee(10_000, 10_000, 6.0, 5, 0)["performance"] == 1.0  # capped


# ------------------------------------------------------------------ engine: line -> pallets -> warehouse

def sim_in(h: Harness, dev: str, ch: str, value, unit: str | None = None) -> None:  # type: ignore[no-untyped-def]
    p = {"ts_ms": h.clock.ms % 10_000_000, "value": value, "source": "sim"}
    if unit:
        p["unit"] = unit
    h.engine.on_mqtt(f"twin/FAC-01/{dev}/{ch}", json.dumps(p).encode())
    h.collect()


def line_up(h: Harness) -> None:
    for dev in ("MM-01", "MM-02"):
        h.engine.on_mqtt(f"twin/FAC-01/{dev}/hello", json.dumps(HELLO).encode())
        sim_in(h, dev, "state", "running")


def test_machine_unit_follows_monitor_and_goes_no_data(h: Harness) -> None:
    assert h.world.entities["M-01"].state == "no_data"  # nothing received: unknown, not "running"
    line_up(h)
    h.run(0.5)
    assert h.world.entities["M-01"].state == "running"
    assert h.world.entities["M-01"].source == "sim"
    sim_in(h, "MM-01", "alarm", "Die jam")
    sim_in(h, "MM-01", "state", "fault")
    h.run(0.5)
    assert h.world.entities["M-01"].state == "fault"
    assert "Die jam" in h.world.entities["M-01"].meta["task"]
    assert any("fault (Die jam)" in e["text"] for e in h.of_type("event"))
    h.run(16.0)  # monitor silent > 15 s
    assert h.world.entities["M-01"].state == "no_data"
    prod = h.of_type("production_update")[-1]
    assert next(m for m in prod["machines"] if m["id"] == "M-01")["state"] == "no_data"


def test_finished_units_become_pallets_and_forklifts_take_them(h: Harness) -> None:
    line_up(h)
    for n in range(0, 7):  # first reading is the counter's starting point; then 6 units = one pallet
        sim_in(h, "MM-02", "units", n)
    h.run(0.2)
    fg = [e for e in h.world.entities.values() if e.id.startswith("FG-")]
    assert len(fg) == 1 and fg[0].node == "FAC_OUT" and fg[0].source == "sim"
    assert any("FG-01 finished" in e["text"] for e in h.of_type("event"))
    # the planner sends a forklift to collect it and put it away in the warehouse
    f = h.world.entities["FL-04"]
    h.world.entities["TR-01"].docked_at = None  # no truck to load: loading would otherwise come first
    steps = planner.suggest_forklift(h.world, f)
    h.world.entities["TR-01"].docked_at = "DOCK_2"
    assert steps and steps[0].node == "FAC_OUT" and steps[0].action == "pick"
    assert h.world.command("FL-04", "FAC_OUT", "pick", source="manual").ok
    h.run(60.0)
    assert h.world.entities["FG-01"].holder == "FL-04"


def test_finished_pallets_are_delivered_when_their_truck_departs(h: Harness) -> None:
    pid = h.world.spawn_pallet("FAC_OUT", {"sku": "FG-0001"})
    assert pid == "FG-01"
    truck = h.world.entities["TR-01"]  # docked at Bay 2 in the seed
    assert truck.cargo is not None
    h.world.entities[pid].node, h.world.entities[pid].holder = None, truck.id
    truck.cargo.append(pid)
    assert h.world.command("TR-01", h.world.layout.gate_node, "depart", source="manual").ok
    h.run(60.0)
    assert pid not in h.world.entities
    assert any(pid in (m.get("removed") or []) for m in h.of_type("unit_update"))
    assert truck.cargo is not None and pid not in truck.cargo


def test_degrade_goes_to_the_simulator_only(h: Harness) -> None:
    h.board_online()
    before = len(h.mqtt)
    h.client({"type": "machine_command", "cmd_id": "d1", "machine_id": "M-01", "action": "degrade"})
    assert h.last_ack()["ok"]
    new = h.mqtt[before:]
    assert [o.topic for o in new] == ["twin/FAC-01/MM-01/cmd/degrade"]
    h.client({"type": "machine_command", "cmd_id": "d2", "machine_id": "FL-01", "action": "degrade"})
    assert not h.last_ack()["ok"]
    assert all(not o.topic.startswith("twin/gateway/") or o.payload.get("led") == "LED0" for o in h.mqtt)


def test_abnormal_vibration_event_through_engine(h: Harness) -> None:
    line_up(h)
    rng = random.Random(9)
    for i in range(100):
        sim_in(h, "MM-01", "vibration_rms", round(2.8 + rng.gauss(0, 0.15), 3), "mm/s")
        h.run(1.0)
    for i in range(90):
        sim_in(h, "MM-01", "vibration_rms", round(2.8 + 0.015 * i + rng.gauss(0, 0.15), 3), "mm/s")
        sim_in(h, "MM-01", "state", "running")
        h.run(1.0)
    texts = [e["text"] for e in h.of_type("event")]
    assert any("abnormal vibration compared with baseline" in t for t in texts)
    m = next(m for m in h.of_type("production_update")[-1]["machines"] if m["id"] == "M-01")
    assert m["abnormal"] and m["baseline"]["learned"] and m["z"] > 3
