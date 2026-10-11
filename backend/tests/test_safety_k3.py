"""K3 worker safety: direction-aware proximity, fall / man-down with cancel, SOS, time limits, gas evacuation,
heat, lone worker, PPE, evacuation headcount, shift and privacy."""

from __future__ import annotations

import json

from conftest import Harness

from twindock.devices import load_sites
from twindock.safety import Safety, heat_index_c, zones_adjacent

CFG = load_sites()
ZONES = {z["id"]: z for s in CFG["sites"] for z in s["zones"]}
FRESH = {f"BG-0{i}": True for i in range(1, 5)}
T0 = 1_700_000_000_000
S = 1000
MIN = 60_000


def safety() -> Safety:
    return Safety.build(CFG["safety"], CFG["workers"], privacy=CFG["privacy"], sites=CFG["sites"], muster_points=CFG["muster_points"])


def at(s: Safety, wid: str, x: float, z: float, zone: str | None, now: int) -> None:
    s.set_position(wid, x, z, ZONES.get(zone or ""), now)


def step(s: Safety, now: int, forklifts: list[tuple] | None = None, gas: set[str] | None = None, heat: dict[str, float] | None = None) -> None:  # type: ignore[type-arg]
    s.evaluate(now, forklifts or [], FRESH, ZONES, gas, heat)


# ---------------------------------------------------------------- proximity with direction

def test_worker_ahead_of_a_reversing_forklift_is_warned_earlier() -> None:
    """Same 4.5 m: no warning beside a forklift driving forwards, a warning behind one that reverses towards them."""
    side, behind = safety(), safety()
    at(side, "WK-02", 100.0, 18.5, "FAC01_PRODUCTION", T0)
    at(behind, "WK-02", 95.5, 14.0, "FAC01_PRODUCTION", T0)
    # Forklift moves west (-x). Heading east (0 rad) while moving west = reversing.
    for s in (side, behind):
        step(s, T0, [("FL-01", 100.4, 14.0, 1.0, 0.0)])
        step(s, T0 + S, [("FL-01", 100.0, 14.0, 1.0, 0.0)])
    assert side.workers["WK-02"].near is None  # 4.5 m to the side: outside 3 m
    n = behind.workers["WK-02"].near
    assert n is not None and n.reversing and n.level == "warning"  # 4.5 m behind a reversing forklift: inside 3 m × 2
    # Driving forwards towards the same worker (heading west = pi): the smaller "ahead" factor, 4.5 > 3 × 1.3
    fwd = safety()
    at(fwd, "WK-02", 95.5, 14.0, "FAC01_PRODUCTION", T0)
    step(fwd, T0, [("FL-01", 100.4, 14.0, 1.0, 3.14159)])
    step(fwd, T0 + S, [("FL-01", 100.0, 14.0, 1.0, 3.14159)])
    assert fwd.workers["WK-02"].near is None


def test_proximity_buzzes_the_badge_and_flashes_the_forklift() -> None:
    h = Harness()
    h.engine.set_mqtt_connected(True)
    e = h.engine
    e.safety.set_position("WK-02", 100.0, 14.0, ZONES["FAC01_PRODUCTION"], h.clock.ms)
    e.safety.evaluate(h.clock.ms, [("FL-01", 101.0, 14.0, 2.0)], FRESH, ZONES)
    e._badge_actions()
    h.collect()
    assert any(m.topic.endswith("/BG-02/cmd/buzz") for m in h.mqtt)


# ---------------------------------------------------------------- fall / man-down

def test_fall_cancelled_within_30_s_is_a_false_alarm() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    s.on_badge("WK-01", "fall", True, T0 + S)
    step(s, T0 + 2 * S)
    w = s.workers["WK-01"]
    assert w.prealert is not None and w.prealert.kind == "fall" and w.man_down is None
    s.on_badge("WK-01", "cancel", True, T0 + 20 * S)
    step(s, T0 + 40 * S)
    assert w.prealert is None and w.man_down is None
    assert s.today.falls == 1 and s.today.falls_cancelled == 1
    assert ("BG-01", "buzz", {"route": "prealert"}) in s.badge_actions


def test_fall_not_cancelled_becomes_man_down_with_location() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    s.on_badge("WK-01", "fall", True, T0)
    step(s, T0 + 29 * S)
    assert s.workers["WK-01"].man_down is None
    step(s, T0 + 31 * S)
    w = s.workers["WK-01"]
    assert w.man_down == "fall" and w.x == 122.0 and s.location_visible(w)


def test_no_movement_starts_a_prealert_and_walking_clears_it() -> None:
    s = safety()
    for k in range(0, 90):  # the badge reports once a second from the same spot
        at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0 + k * S)
    step(s, T0 + 89 * S)
    assert s.workers["WK-03"].prealert is None
    for k in range(90, 92):
        at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0 + k * S)
    step(s, T0 + 91 * S)
    assert s.workers["WK-03"].prealert is not None and s.workers["WK-03"].prealert.kind == "no_motion"
    for k in range(92, 123):
        at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0 + k * S)
    step(s, T0 + 122 * S)
    assert s.workers["WK-03"].man_down == "no_motion"
    at(s, "WK-03", 104.0, 12.0, "FAC01_PRODUCTION", T0 + 123 * S)
    step(s, T0 + 123 * S)
    assert s.workers["WK-03"].man_down is None


def test_man_down_and_sos_alerts_through_the_rules_engine() -> None:
    h = Harness()
    e = h.engine
    for wid, x in (("WK-01", 122.0), ("WK-03", 110.0)):
        e.safety.set_position(wid, x, 12.0, ZONES["FAC01_PRODUCTION"], h.clock.ms)
    e.safety.on_badge("WK-01", "sos", True, h.clock.ms)
    for w in e.safety.workers.values():
        w.fresh = w.id in ("WK-01", "WK-03")
    raised, _ = e.rules.evaluate(e._facts(), h.clock.ms)
    sos = [a for a in raised if a.rule_id == "sos"]
    assert len(sos) == 1 and sos[0].severity == "critical"
    assert "Production" in sos[0].message and "WK-03 (12 m)" in sos[0].message  # nearest first-aider
    assert e.safety.clear_incident("WK-01", h.clock.ms) is None
    _, resolved = e.rules.evaluate(e._facts(), h.clock.ms + S)
    assert any(a.rule_id == "sos" for a in resolved)


# ---------------------------------------------------------------- zones

def test_zone_time_limit_in_the_cold_room() -> None:
    s = safety()
    at(s, "WK-02", 135.0, 20.0, "FAC01_COLD", T0)
    step(s, T0 + 19 * MIN)
    assert s.workers["WK-02"].zone_overtime_min is None
    at(s, "WK-02", 135.5, 20.0, "FAC01_COLD", T0 + 21 * MIN)
    step(s, T0 + 21 * MIN)
    assert s.workers["WK-02"].zone_overtime_min == 1.0


def test_gas_alarm_evacuates_the_zone_and_its_neighbours_only() -> None:
    assert zones_adjacent(ZONES["FAC01_PRODUCTION"], ZONES["FAC01_COLD"], 6.0)
    assert not zones_adjacent(ZONES["FAC01_PRODUCTION"], ZONES["WH01_STORAGE"], 6.0)
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    at(s, "WK-02", 135.0, 20.0, "FAC01_COLD", T0)
    at(s, "WK-04", 20.0, 10.0, "WH01_STORAGE", T0)
    step(s, T0 + S, gas={"FAC01_PRODUCTION"})
    assert s.workers["WK-01"].evacuate and s.workers["WK-02"].evacuate
    assert s.workers["WK-04"].evacuate is None
    step(s, T0 + 2 * S, gas=set())
    assert s.workers["WK-01"].evacuate is None


def test_heat_index_and_rest_reminder_names_nobody() -> None:
    assert abs(heat_index_c(20.0, 50.0) - 20.0) < 1.5  # mild air: about the air temperature
    assert 40 < heat_index_c(35.0, 50.0) < 41.5  # NOAA table: 95 °F at 50 % is about 105 °F (40.6 °C)
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    step(s, T0 + S, heat={"FAC01_PRODUCTION": 34.0, "FAC01_COLD": 4.0})
    assert s.heat_zones == {"FAC01_PRODUCTION": 34.0}
    assert ("BG-01", "buzz", {"route": "rest"}) in s.badge_actions
    assert "WK-01" not in json.dumps(s.wire(T0)["heat_zones"])


def test_lone_worker_check_in_escalates() -> None:
    s = safety()
    at(s, "WK-02", 135.0, 20.0, "FAC01_COLD", T0)
    step(s, T0 + 9 * MIN)
    assert s.workers["WK-02"].lone_level is None
    at(s, "WK-02", 135.4, 20.0, "FAC01_COLD", T0 + 10 * MIN + S)
    step(s, T0 + 10 * MIN + S)
    assert s.workers["WK-02"].lone_level == "warning"
    step(s, T0 + 12 * MIN + S)
    assert s.workers["WK-02"].lone_level == "critical"
    s.on_badge("WK-02", "checkin", True, T0 + 12 * MIN + 2 * S)
    step(s, T0 + 12 * MIN + 3 * S)
    assert s.workers["WK-02"].lone_level is None


def test_not_alone_means_no_check_in() -> None:
    s = safety()
    at(s, "WK-02", 135.0, 20.0, "FAC01_COLD", T0)
    at(s, "WK-03", 136.0, 21.0, "FAC01_COLD", T0)
    step(s, T0 + 15 * MIN)
    assert s.workers["WK-02"].lone_level is None


def test_ppe_reminder_only_without_a_worn_helmet_and_never_recorded() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 9.0, "FAC01_PRESS", T0)
    step(s, T0 + S)
    assert s.workers["WK-01"].ppe_missing == "helmet" and s.ppe_reminders == 1
    assert not s.history  # a reminder, not a record
    w = s.wire(T0)["workers"][0]
    assert "ppe" not in json.dumps(w)  # never sent with the worker's id
    s.set_helmet("WK-01", True)
    step(s, T0 + 2 * S)
    assert s.workers["WK-01"].ppe_missing is None and s.ppe_reminders == 0


# ---------------------------------------------------------------- evacuation

def test_evacuation_headcount() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    at(s, "WK-02", 135.0, 20.0, "FAC01_COLD", T0)
    at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0)
    assert s.start_evacuation(T0 + S, "drill", "Control Room") is None
    assert s.start_evacuation(T0 + S, "drill", "x") == "An evacuation is already running"
    step(s, T0 + S)
    hc = s.headcount()
    assert hc is not None and hc["on_site"] == 3 and hc["accounted"] == 0
    mp = CFG["muster_points"][1]
    at(s, "WK-01", mp["x"], mp["z"], None, T0 + 60 * S)
    at(s, "WK-03", mp["x"] + 2, mp["z"], None, T0 + 60 * S)
    step(s, T0 + 60 * S)
    hc = s.headcount()
    assert hc is not None and hc["accounted"] == 2 and hc["by_muster"]["MP-2"] == 2
    assert [u["id"] for u in hc["unaccounted"]] == ["WK-02"] and hc["unaccounted"][0]["last_zone_id"] == "FAC01_COLD"
    assert all(w["location_shown"] for w in s.wire(T0)["workers"] if w["fresh"])  # during an evacuation locations are shown
    assert s.end_evacuation(T0 + 90 * S) is None and s.headcount() is None


def test_evacuation_from_the_monitoring_page_sends_badges_to_muster(h: Harness) -> None:
    e = h.engine
    h.engine.set_mqtt_connected(True)
    e.safety.set_position("WK-01", 122.0, 12.0, ZONES["FAC01_PRODUCTION"], h.clock.ms)
    h.client({"type": "safety_command", "cmd_id": "e1", "action": "start_evacuation", "reason": "gas leak", "by": "Monitor"})
    assert h.last_ack()["ok"]
    assert any(m.topic.endswith("/BG-01/cmd/goto") for m in h.mqtt)
    su = h.of_type("safety_update")[-1]
    assert su["evacuation"]["reason"] == "gas leak" and su["evacuation"]["on_site"] == 1
    h.client({"type": "safety_command", "cmd_id": "e2", "action": "end_evacuation"})
    assert h.last_ack()["ok"] and h.of_type("safety_update")[-1]["evacuation"] is None


def test_sim_actions_only_for_simulated_badges(h: Harness) -> None:
    h.client({"type": "safety_command", "cmd_id": "f1", "action": "sim_fall", "worker_id": "WK-01"})
    assert not h.last_ack()["ok"]  # no broker
    h.engine.set_mqtt_connected(True)
    h.client({"type": "safety_command", "cmd_id": "f2", "action": "sim_fall", "worker_id": "WK-01"})
    assert h.last_ack()["ok"] and any(m.topic == "twin/FAC-01/BG-01/cmd/fall" for m in h.mqtt)


# ---------------------------------------------------------------- shift and privacy

def test_off_site_positions_are_not_tracked() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    s.set_position("WK-01", 400.0, 400.0, None, T0 + S)
    assert s.workers["WK-01"].x is None and s.workers["WK-01"].zone_id is None


def test_shift_and_breaks_are_personal() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    for k in range(1, 4 * 60 + 2):
        at(s, "WK-01", 122.0 + (k % 2), 12.0, "FAC01_PRODUCTION", T0 + k * MIN)
        step(s, T0 + k * MIN)
    me = s.personal("WK-01", T0 + 241 * MIN)
    assert me is not None and me["break_due"] and me["hours_on_shift"] > 4
    wire = s.wire(T0 + 241 * MIN)
    assert wire["breaks_due"] == 1 and "hours_on_shift" not in json.dumps(wire)  # only a count is broadcast
    # A 15-minute break in the office resets it
    for k in range(16):
        at(s, "WK-01", 95.0, 33.0, "FAC01_OFFICE", T0 + (242 + k) * MIN)
        step(s, T0 + (242 + k) * MIN)
    assert not s.personal("WK-01", T0 + 258 * MIN)["break_due"]  # type: ignore[index]


def test_checkout_after_no_data_stops_tracking() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    step(s, T0 + 31 * MIN)
    assert s.workers["WK-01"].shift_start_ms is None and s.workers["WK-01"].x is None


def test_positions_reach_screens_only_during_an_alert(h: Harness) -> None:
    e = h.engine
    e.safety.set_position("WK-01", 122.0, 12.0, ZONES["FAC01_PRODUCTION"], h.clock.ms)
    e.safety.workers["WK-01"].fresh = True
    wk = e.world.entities["WK-01"]
    wk.x, wk.z, wk.state = 122.0, 12.0, "working"
    unit = next(u for u in e._all_units() if u.id == "WK-01")
    assert unit.state == "private" and (unit.x, unit.z) != (122.0, 12.0)  # shown at the zone, not where they are
    w = next(x for x in e.safety.wire(h.clock.ms)["workers"] if x["id"] == "WK-01")
    assert w["x"] is None and w["zone_id"] is None and not w["location_shown"]
    e.safety.on_badge("WK-01", "sos", True, h.clock.ms)
    unit = next(u for u in e._all_units() if u.id == "WK-01")
    assert (unit.x, unit.z) == (122.0, 12.0) and unit.state != "private"


def test_history_is_pruned_after_the_retention_period() -> None:
    s = safety()
    at(s, "WK-01", 122.0, 12.0, "FAC01_PRODUCTION", T0)
    s.on_badge("WK-01", "sos", True, T0)
    assert s.history
    step(s, T0 + 31 * 86_400_000)
    assert not s.history


def test_simulated_badge_fall_cancel_and_goto() -> None:
    import random
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    from site_sim import SiteSim, select_devices  # type: ignore[import-not-found]

    cfg = load_sites()
    sim = SiteSim(cfg, [d for d in select_devices(cfg, None, None) if d["id"] == "BG-01"], seed=1)
    seen: list[str] = []
    real = sim.publish
    sim.publish = lambda m, ch, p, retain=False: (seen.append(ch), real(m, ch, p, retain))[-1]  # type: ignore[method-assign]
    m = sim.core.get("people").walkers["BG-01"]  # the worker's true position (the badge reports it)
    sim.step(1.0)
    sim.command("BG-01", "fall")
    sim.step(1.0)
    assert "fall" in seen
    x0 = m.x
    sim.step(5.0)
    assert m.x == x0  # lying still
    sim.command("BG-01", "cancel")
    sim.step(1.0)
    assert "cancel" in seen
    mp = cfg["muster_points"][1]
    sim.command("BG-01", "goto", {"x": mp["x"], "z": mp["z"]})
    for _ in range(200):
        sim.step(1.0)
    assert abs(m.x - mp["x"]) < 1 and abs(m.z - mp["z"]) < 1
    assert random  # noqa


def test_a_data_gap_does_not_count_as_standing_still() -> None:
    s = safety()
    at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0)
    at(s, "WK-03", 102.0, 12.0, "FAC01_PRODUCTION", T0 + 20 * MIN)  # the badge was silent for 20 minutes, then reports from the same spot
    step(s, T0 + 20 * MIN + S)
    assert s.workers["WK-03"].prealert is None
    step(s, T0 + 20 * MIN + 95 * S)
    assert s.workers["WK-03"].prealert is not None  # but really standing still for 90 s is
