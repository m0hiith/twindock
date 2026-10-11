"""R4: people and safety. The roster decides who is on site; badges report positions with BLE error; heat stress
depends on the work; evacuation time follows from walking distances; falls only on cue or at a documented rate."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from conftest import Harness
from test_scenarios_f3 import Bridge

from twindock.safety import Safety

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SITES, SiteSim  # noqa: E402

CFG = json.loads(SITES.read_text())
BADGES = [w["badge"] for w in CFG["workers"]]


def roster(shift: str) -> set[str]:
    return {w["id"] for w in CFG["workers"] if w.get("shift") == shift}


def on_site(h: Harness) -> set[str]:
    return {w.id for w in h.engine.safety.workers.values() if w.fresh}


def test_headcount_equals_the_roster_through_a_shift_change(h: Harness) -> None:
    b = Bridge(h, BADGES, hour=10.5)
    b.run(30)
    assert on_site(h) == roster("A")
    b.sim.local_hour = lambda: 13.95  # type: ignore[method-assign]  # crew B arrives for the 14:00 shift
    b.run(5 * 60)
    assert roster("B") <= on_site(h)  # B is in; A is handing over
    b.sim.local_hour = lambda: 14.3  # type: ignore[method-assign]  # A walks out through the gate
    b.run(10 * 60)
    people = b.sim.core.get("people").walkers
    assert {w.worker for w in people.values() if w.on_site} == roster("B")
    assert on_site(h) == roster("B")  # the twin's headcount (fresh badges) is the roster on shift


def test_evacuation_time_follows_from_walking_distances(h: Harness) -> None:
    b = Bridge(h, BADGES, hour=10.5)
    b.run(30)
    h.client({"type": "safety_command", "cmd_id": "ev", "action": "start_evacuation", "by": "Drill", "reason": "evacuation drill"})
    assert h.last_ack()["ok"]
    e = h.engine.safety.evacuation
    assert e is not None and e.predicted_s is not None and e.predicted_s > 20
    for _ in range(4 * 600):
        b.step()
        if e.accounted_ms is not None:
            break
    assert e.accounted_ms is not None, h.engine.safety.headcount()
    actual = (e.accounted_ms - e.started_ms) / 1000
    # people walk a little faster than the planning speed and need a moment to get the buzz: same order of magnitude
    assert 0.4 * e.predicted_s <= actual <= 1.3 * e.predicted_s + 10, (actual, e.predicted_s)


def test_badge_positions_carry_slowly_wandering_ble_error() -> None:
    s = SiteSim(CFG, [d for d in CFG["devices"] if d["id"] == "BG-05"], seed=6)
    s.verbose = False
    s.local_hour = lambda: 10.5  # type: ignore[method-assign]
    w = s.core.get("people").walkers["BG-05"]
    errs: list[tuple[float, float]] = []
    s.publish = lambda m, ch, p, retain=False: errs.append((p["value"][0] - w.x, p["value"][1] - w.z)) if ch == "position" else None  # type: ignore[method-assign]
    for _ in range(4 * 1800):
        s.step(0.25)
    ex = [e[0] for e in errs[60:]]
    sd = math.sqrt(sum(x * x for x in ex) / len(ex))
    spec = s.params.leaf("sensors.badge.position").value
    assert 0.5 * spec["ble_sigma"] < sd < 1.6 * spec["ble_sigma"], sd
    lag1 = sum(a * b for a, b in zip(ex, ex[1:])) / sum(a * a for a in ex)
    assert lag1 > 0.8  # correlated from one second to the next, like real BLE positioning


def test_heavier_work_gets_rest_reminders_sooner() -> None:
    zones = {z["id"]: z for s in CFG["sites"] for z in s["zones"]}
    s = Safety.build(CFG["safety"], CFG["workers"], sites=CFG["sites"], muster_points=CFG.get("muster_points"))
    press = s.workers["WK-01"]   # press operator: heavy work
    guard = s.workers["WK-05"]   # security guard: light work
    for w in (press, guard):
        s.set_position(w.id, 120.0, 10.0, zones["FAC01_PRODUCTION"], 0)
        w.shift_start_ms = 0
    fresh = {w.badge: True for w in s.workers.values()}
    s.evaluate(1000, [], fresh, zones, set(), {"FAC01_PRODUCTION": 30.0})  # heat index 30: below 32 in still air
    buzzed = {b for b, a, x in s.take_badge_actions() if a == "buzz" and x.get("route") == "rest"}
    assert press.badge in buzzed and guard.badge not in buzzed  # 30 + 3 for heavy work ≥ 32; light work stays at 30
    assert press.heat_effective == 33.0 and guard.heat_effective == 30.0


def test_meal_break_sends_people_to_the_canteen() -> None:
    s = SiteSim(CFG, [], seed=2)
    s.verbose = False
    s.local_hour = lambda: 11.9  # type: ignore[method-assign]
    for _ in range(40):
        s.step(0.25)
    s.local_hour = lambda: 12.05  # type: ignore[method-assign]  # A-shift lunch
    for _ in range(4 * 400):
        s.step(0.25)
    people = s.core.get("people").walkers
    canteen = next(n for n in json.loads((Path(SITES).parent / "layout.json").read_text())["nodes"] if n["id"] == "WALK_CANTEEN")
    at_lunch = [w for w in people.values() if w.status == "break"]
    assert at_lunch and all(math.hypot(w.x - canteen["x"], w.z - canteen["z"]) < 3 for w in at_lunch)
    stay = set(s.params.v("people.stay_in_breaks_roles"))
    assert all(w.role not in stay for w in at_lunch)


def test_falls_only_on_cue_or_at_the_documented_rate() -> None:
    s = SiteSim(CFG, [], seed=4)
    s.verbose = False
    s.local_hour = lambda: 10.5  # type: ignore[method-assign]
    for _ in range(4 * 3600):
        s.step(0.25)
    assert not [e for e in s.core.log if e.name.endswith(" fell")]  # an hour of normal work: no falls
    s.params._f["people.fall_rate_per_h"] = 3600 * 0.002  # a deliberately absurd rate to see the mechanism work
    for _ in range(4 * 300):
        s.step(0.25)
    falls = [e for e in s.core.log if e.name.endswith(" fell")]
    assert falls and all("documented rate" in e.cause for e in falls)
