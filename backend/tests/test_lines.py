"""R2: production lines. Material conservation, OEE folded from an event log, starving and blocking from buffers,
Weibull failures that wear makes more likely, a bearing whose vibration rises before it fails, and the shift calendar."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

from twindock.production import StateLog, durations_from_events, oee_from_durations

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SITES, SiteSim  # noqa: E402

CFG = json.loads(SITES.read_text())


def line_sim(hour: float = 10.5, seed: int = 8) -> SiteSim:
    s = SiteSim(CFG, [], seed=seed)
    s.verbose = False
    s.local_hour = lambda: hour  # type: ignore[method-assign]
    return s


def run(s: SiteSim, seconds: float, each=None) -> None:  # type: ignore[no-untyped-def]
    for _ in range(round(seconds / 0.25)):
        s.step(0.25)
        if each:
            each(s)


def conserved(s: SiteSim) -> None:
    prod = s.core.get("production")
    good = sum(ln.good for ln in prod.lines.values())
    scrap = sum(ln.scrap for ln in prod.lines.values())
    assert prod.fed == prod.infeed + prod.wip() + good + scrap, (prod.fed, prod.infeed, prod.wip(), good, scrap)


# ------------------------------------------------------------------ material

def test_material_is_conserved_at_every_step() -> None:
    """Blanks in = blanks at the infeed + work in progress + good + scrap, through feeds, jams, a degrade to failure,
    a grid failure and shift breaks."""
    s = line_sim()
    prod = s.core.get("production")
    run(s, 900, conserved)
    for _ in range(3):
        s.core.command("MM-01", "feed", {"units": 240})
        run(s, 600, conserved)
    s.core.command("MM-03", "degrade", {})
    s.core.command("PM-04", "grid_failure", {})
    run(s, 120, conserved)
    s.core.command("PM-04", "grid_restore", {})
    s.local_hour = lambda: 12.2  # type: ignore[method-assign]  # lunch break
    run(s, 300, conserved)
    assert sum(ln.good for ln in prod.lines.values()) > 400


# ------------------------------------------------------------------ OEE from events

def test_oee_from_a_scripted_event_log() -> None:
    """A packer (ideal 8 s) over 1 h: 40 min running, 5 min breakdown, 5 min starved, 10 min break (planned).
    It made 270 good and 10 scrap. A = 40/50, P = 8 × 280 / 2400, Q = 270/280."""
    t0 = 1_000_000
    m = 60_000
    events = [(t0, "running"), (t0 + 20 * m, "fault"), (t0 + 25 * m, "running"), (t0 + 40 * m, "starved"),
              (t0 + 45 * m, "running"), (t0 + 50 * m, "planned_stop")]
    d = durations_from_events(events, t0 + 60 * m)
    o = oee_from_durations(d, 8.0, 270, 10)
    assert o["availability"] == pytest.approx(40 / 50)
    assert o["performance"] == pytest.approx(8 * 280 / 2400)
    assert o["quality"] == pytest.approx(270 / 280)
    assert o["oee"] == pytest.approx(0.8 * (8 * 280 / 2400) * (270 / 280))
    L = o["losses"]
    assert L["breakdown_s"] == 300 and L["starved_s"] == 300 and L["planned_stop_s"] == 600
    assert L["speed_s"] == pytest.approx(2400 - 8 * 280) and L["quality_s"] == pytest.approx(80)
    # the incremental log folds to the same durations
    log = StateLog()
    for t, st in events:
        log.mark(t, st)
    assert log.durations(t0 + 60 * m) == d


def test_engine_oee_comes_from_monitor_events_and_excludes_gaps() -> None:
    from conftest import Harness
    h = Harness()
    hello = {"type": "machine_monitor", "protocol": "wifi", "fw_version": "sim-2.3", "source": "sim",
             "capabilities": next(d for d in CFG["devices"] if d["id"] == "MM-02")["capabilities"]}
    h.mqtt_in("twin/FAC-01/MM-02/hello", hello)

    def say(ch: str, v: object) -> None:
        h.mqtt_in(f"twin/FAC-01/MM-02/{ch}", {"ts_ms": 1, "value": v, "source": "sim"})
    say("state", "running")
    for _ in range(60):  # 60 s running, reporting every 2 s
        h.run(2)
        say("state", "running")
    say("state", "fault")
    for _ in range(15):  # 30 s fault
        h.run(2)
        say("state", "fault")
    h.run(40)  # silent: after 15 s without data the monitor is stale, and that gap counts as neither running nor planned
    m = h.engine.production.machines["M-02"]
    o = h.engine.production.machine_oee(m, h.clock.ms)
    assert o["availability"] == pytest.approx(120 / (150 + 15), abs=0.03)  # the last known state holds for the 15 s, not the 25 s after
    assert o["losses"]["breakdown_s"] == pytest.approx(45, abs=2)


# ------------------------------------------------------------------ starving and blocking

def test_a_stopped_packer_blocks_its_press_and_an_empty_infeed_starves_it() -> None:
    s = line_sim()
    prod = s.core.get("production")
    run(s, 60)
    press, packer = prod.machines["MM-01"], prod.machines["MM-02"]
    s.core.command("MM-02", "repair", {"seconds": 600})  # the packer is down for a while
    run(s, 180)
    assert packer.state == "maintenance"
    assert press.state == "blocked" and prod.lines[1].buffer == int(s.params.f("production.material.buffer_capacity"))
    run(s, 600)  # packer back: it drains the buffer; the press runs again
    assert press.state in ("running", "blocked")
    prod.infeed = 0  # nothing left at the infeed
    run(s, 120)
    assert press.state == "starved" and prod.machines["MM-03"].state == "starved"
    run(s, 300)  # the packer empties the buffer behind a starved press, then starves too
    assert packer.state == "starved"
    s.core.command("MM-01", "feed", {"units": 240})
    run(s, 30)
    assert press.state in ("running", "blocked")


# ------------------------------------------------------------------ failures and wear

def test_minor_stops_follow_their_weibull_rate() -> None:
    s = line_sim(seed=3)
    prod = s.core.get("production")
    for m in prod.machines.values():
        m.wear, m.wear_limit = 0.0, 9.0  # no wear effects here
    prod.infeed = prod.fed = 10**6
    stops: dict[str, int] = {}
    s.core.listeners.append(lambda e: stops.__setitem__(e.name, stops.get(e.name, 0) + 1) if e.name.endswith(" fault") else None)
    run(s, 8 * 3600)
    p = s.params
    lf = p.leaf("production.failures.minor_ttf_s").value
    mean = float(lf["scale"]) * math.gamma(1 + 1 / float(lf["shape"]))
    total_stops = sum(stops.values())
    # operating time ≈ running time; the presses are blocked part of the time behind the slower packers
    expected_max = 4 * 8 * 3600 / mean
    assert 0.25 * expected_max < total_stops < 1.2 * expected_max, (total_stops, expected_max)


def test_wear_makes_minor_stops_more_likely() -> None:
    s = line_sim()
    prod = s.core.get("production")
    m = prod.machines["MM-01"]
    m.wear = 0.0
    fresh = [prod._draw_minor(m) for _ in range(400)]
    m.wear = 0.9
    worn = [prod._draw_minor(m) for _ in range(400)]
    assert sum(worn) / len(worn) < 0.5 * sum(fresh) / len(fresh)


def test_rising_vibration_predicts_the_bearing_failure() -> None:
    """A seeded defect: wear grows, vibration rises well before the bearing gives out, then the machine breaks down
    with "Bearing failure" and the repair fits a new bearing."""
    s = line_sim()
    prod = s.core.get("production")
    m = prod.machines["MM-01"]
    m.next_minor_s = 1e9
    prod.lines[1].buffer = -10_000  # keep the press cycling
    healthy = s.params.f("production.machines.M-01.healthy_vibration_mm_s")
    s.core.command("MM-01", "degrade", {})
    first_high = failed_at = None
    for _ in range(4 * 900):
        s.step(0.25)
        if first_high is None and m.state == "running" and prod.vibration(m) > healthy + 1.0:
            first_high = s.core.t
        if m.state == "fault" and m.alarm == s.params.v("production.failures.bearing_alarm"):
            failed_at = s.core.t
            break
    assert first_high is not None and failed_at is not None
    assert failed_at - first_high > 60  # at least a minute of warning in the demo's accelerated defect
    run(s, 4000)  # repair time (lognormal, median 30 min)
    assert m.wear < 0.1 and m.state != "fault"


# ------------------------------------------------------------------ shifts

def test_shift_calendar_phases() -> None:
    s = line_sim()
    sh = s.core.get("shifts")
    assert sh.phase(6.05) == ("A", "setup")
    assert sh.phase(10.5) == ("A", "production")
    assert sh.phase(12.2) == ("A", "break")
    assert sh.phase(13.95) == ("A", "handover")
    assert sh.phase(14.1) == ("B", "setup")
    assert sh.phase(23.0) == ("C", "production")
    assert sh.phase(3.2) == ("C", "break")


def test_lines_stop_in_breaks() -> None:
    s = line_sim(hour=12.2)  # A-shift lunch
    run(s, 120)
    prod = s.core.get("production")
    assert all(m.state == "planned_stop" for m in prod.machines.values())
    assert all(s.core.q.air_demand_nm3_min[m.id] == 0 for m in prod.machines.values())
