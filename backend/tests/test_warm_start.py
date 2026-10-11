"""D3: warm start and the simulation clock."""

from __future__ import annotations

import json
import time

from conftest import Harness

from twindock.engine import Engine
from twindock.graph import load_layout
from twindock.main import App
from twindock.simclock import SimClock, day_seed

T0 = 1_760_000_000_000  # a fixed start, so the warm start is reproducible


def warm(minutes: float = 45, seed: int = 1234) -> tuple[App, float]:
    a = App()
    a.clock.sim_ms = T0
    a.start_sim(seed)
    t = time.perf_counter()
    a.warm_start(minutes, seed)
    return a, time.perf_counter() - t


def test_warm_start_is_fast_and_leaves_a_running_factory() -> None:
    a, wall = warm()
    e = a.engine
    assert wall < 10.0, f"warm start took {wall:.1f} s"
    assert e.warm_start is not None and e.warm_start.sim_s == 45 * 60
    assert a.clock.sim_ms == T0 + 45 * 60_000
    # production: monitors online, baselines learned, units made, pallets out of the line
    p = e.production.wire(e._fresh())
    assert all(m["state"] != "no_data" for m in p["machines"])
    assert all(m["baseline"]["learned"] for m in p["machines"])
    assert p["line"]["units_today"] > 50 and p["line"]["pallets_made"] > 3
    assert p["line"]["oee"] is not None
    # utilities: the compressor has cycled, meters read, the campus draws power
    cp = e.devices.sim["CP-01"]
    assert cp.readings["pressure_bar"].value > 5
    assert len({round(v, 1) for _, v in cp.history["pressure_bar"]}) > 3
    pw = e.power_summary()
    assert pw["grid_ok"] is True and pw["grid_kw"] is not None and pw["demand_kw"] > 0
    # safety: people are on site and tracked
    # people: exactly the shift on duty is on site (the roster), tracked by their badges
    from sim.models.production import shift_phase
    lt = time.localtime(a.clock.sim_ms / 1000)
    shift, _ = shift_phase(a.sim.sim.params, lt.tm_hour + lt.tm_min / 60)
    roster = {w["id"] for w in e.devices.cfg["workers"] if w.get("shift") == shift}
    assert {w.id for w in e.safety.workers.values() if w.fresh} == roster
    assert sum(e.safety.wire(e.clock())["zone_counts"].values()) >= 3
    # logistics: trucks and forklifts are working
    states = {u.state for u in e.world.entities.values() if u.kind in ("truck", "forklift")}
    assert states - {"idle", "arriving", "gone"}, states
    on_duty_badges = {w["badge"] for w in e.devices.cfg["workers"] if w.get("shift") == shift}
    for d in e.devices.wire(e.gw, e.clock(), e.ble):
        if d["source"] != "sim":
            continue
        if d["type"] == "badge":  # off-shift badges are switched off in the gate rack
            assert (d["status"] == "online") == (d["id"] in on_duty_badges), d["id"]
        else:
            assert d["status"] == "online", d["id"]
    # the real board was never touched
    assert e.gw.hello is None and e.gw.status is None


def test_warm_start_is_reproducible() -> None:
    a, _ = warm(6, seed=99)
    b, _ = warm(6, seed=99)
    pa, pb = a.engine.production.wire(a.engine._fresh()), b.engine.production.wire(b.engine._fresh())
    assert pa["line"] == pb["line"]
    pos = lambda app: sorted((u.id, round(u.x, 3), round(u.z, 3)) for u in app.engine.world.entities.values())  # noqa: E731
    assert pos(a) == pos(b)
    c, _ = warm(6, seed=100)
    assert pos(c) != pos(a) or c.engine.production.wire(c.engine._fresh())["line"] != pa["line"]


def test_day_seed_changes_with_the_date() -> None:
    assert day_seed("2026-10-11") == day_seed("2026-10-11")
    assert day_seed("2026-10-11") != day_seed("2026-10-12")


def clocked() -> tuple[Harness, SimClock]:
    h = Harness()
    clock = SimClock(sim_ms=T0)
    h.engine = Engine(load_layout(), clock=clock)
    return h, clock


def test_speed_control_and_board_lock() -> None:
    h, clock = clocked()
    h.engine.on_connect("client-1")
    h.collect()
    first = h.of_type("sim_clock")[0]
    assert first["speed"] == 1 and first["speeds"] == [1, 5, 20] and first["speed_locked"] is None
    h.client({"type": "set_sim_speed", "cmd_id": "s1", "speed": 20})
    assert h.last_ack()["ok"] and clock.speed == 20
    assert h.of_type("sim_clock")[-1]["speed"] == 20
    # The real board comes online: back to real time, and fast speeds are refused while it is there.
    h.board_online()
    h.engine.tick(0.05)
    h.collect()
    assert clock.speed == 1
    assert any("real time" in e["text"] for e in h.of_type("event"))
    h.client({"type": "set_sim_speed", "cmd_id": "s2", "speed": 5})
    assert not h.last_ack()["ok"] and "real board" in h.last_ack()["reason"]
    h.client({"type": "set_sim_speed", "cmd_id": "s3", "speed": 1})
    assert h.last_ack()["ok"]


def test_live_loop_runs_at_speed() -> None:
    a = App()
    a.clock.sim_ms = T0
    a.start_sim(5)
    a.clock.speed = 20
    for _ in range(20):  # one real second of 20 Hz ticks at x20
        a.advance(0.05 * a.clock.speed)
    assert a.clock.sim_ms == T0 + 20_000
    msgs = [o.msg for o in a.engine.drain() if hasattr(o, "msg")]
    assert json.dumps(msgs)  # everything that went out is plain JSON
