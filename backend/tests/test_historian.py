"""R6: the historian (SQLite, deadband compression, ring-buffer retention, downsampled series), CSV export and the
shift report (data and PDF) built from a simulated run."""

from __future__ import annotations

from conftest import Harness
from fastapi.testclient import TestClient

from twindock.embedded_sim import EmbeddedSim
from twindock.historian import Historian
from twindock.report import shift_report, shift_report_pdf, shift_window


def test_deadband_keeps_changes_and_drops_flat_lines() -> None:
    h = Historian(":memory:")
    for i in range(600):  # 10 min of a flat 7.00 bar at 1 Hz
        h.add("CP-01", "pressure_bar", i * 1000, 7.0)
    for i in range(600, 660):  # then a ramp
        h.add("CP-01", "pressure_bar", i * 1000, 7.0 + (i - 600) * 0.05)
    pts = h.raw("CP-01", "pressure_bar", 0, 700_000)
    flat = [p for p in pts if p[0] < 600_000]
    assert len(flat) <= 11  # one point a minute while nothing moves
    assert len([p for p in pts if p[0] >= 600_000]) >= 55  # every real change is kept
    assert h.kept < h.seen


def test_states_on_change_and_positions_never_stored() -> None:
    h = Historian(":memory:")
    for t, s in [(0, "running"), (1000, "running"), (2000, "fault"), (3000, "fault"), (4000, "running")]:
        h.add("MM-01", "state", t, s)
    h.add("BG-01", "position", 100, [1.0, 2.0])
    assert h.states("MM-01", "state", 0, 5000) == [(0, "running"), (2000, "fault"), (4000, "running")]
    assert ("BG-01", "position") not in h.channels()
    assert h.states("MM-01", "state", 2500, 5000)[0] == (2500, "fault")  # the state in force at the window's start


def test_retention_is_a_ring_buffer() -> None:
    h = Historian(":memory:", retention_s=3600)
    for i in range(0, 3 * 3600, 30):
        h.add("PM-01", "power_kw", i * 1000, float(i % 7))
        h.flush(i * 1000)
    pts = h.raw("PM-01", "power_kw", 0, 4 * 3600 * 1000)
    assert pts and pts[0][0] >= (3 * 3600 - 3600 - 300) * 1000  # only the last hour (+ one prune period) is kept


def test_series_buckets_average_min_max() -> None:
    h = Historian(":memory:")
    for i in range(100):
        h.add("EN-04", "temperature", i * 1000, float(i))
    s = h.series("EN-04", "temperature", 0, 99_999, buckets=10)
    assert len(s) == 10
    t, avg, lo, hi, n = s[0]
    assert t == 0 and lo == 0 and hi == 9 and avg == 4.5 and n == 10


def test_history_api_and_csv() -> None:
    from twindock.main import app, state
    now = state.engine.clock()
    for i in range(120):
        state.engine.historian.add("PM-06", "power_kw", now - (120 - i) * 1000, 10.0 + (i % 5))
    c = TestClient(app)
    r = c.get("/api/history", params={"device": "PM-06", "channel": "power_kw", "range": "15m"}).json()
    assert r["points"] and all(len(p) == 5 for p in r["points"])
    csv = c.get("/api/history.csv", params={"device": "PM-06", "channel": "power_kw", "range": "15m"})
    assert csv.headers["content-type"].startswith("text/csv") and csv.text.startswith("time,avg,min,max,samples\n")
    assert len(csv.text.strip().splitlines()) > 5
    assert c.get("/api/history", params={"device": "PM-06", "channel": "power_kw", "range": "3d"}).status_code == 400


def test_shift_report_from_a_simulated_run() -> None:
    h = Harness()
    sim = EmbeddedSim(h.engine, seed=3)
    sim.sim.local_hour = lambda: 10.5  # type: ignore[method-assign]
    sim.start()
    for _ in range(4 * 1500):  # 25 minutes
        h.clock.ms += 250
        sim.step(0.25)
        h.engine.tick(0.25)
        for o in h.engine.drain():
            if hasattr(o, "topic"):
                sim.command(o.topic, o.payload)
    h.engine.historian.flush(h.clock.ms)
    from sim import Params
    name, t0, t1 = shift_window(Params.load().v("production.shifts.calendar"), h.clock.ms)
    r = shift_report(h.engine)
    assert r["shift"] == name and r["from_ms"] == t0 and r["source"] == "sim"
    assert r["production"]["good_cartons"] > 50
    for m in r["production"]["machines"]:
        assert m["oee"] is not None and 0 < m["oee"] <= 1 and set(m["losses"]) >= {"breakdown_s", "blocked_s"}
    assert r["energy"]["kwh"]["production"] > 0 and r["energy"]["kwh_per_carton"] > 0
    pdf = shift_report_pdf(r)
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
