"""R5: the factory reacts. Each automatic chain end to end, through the simulator and the engine together:
cause -> action -> result. Stopping production waits for a person."""

from __future__ import annotations

import json

from conftest import Harness
from test_scenarios_f3 import CFG, DEF, Bridge

TECH_IDS = ["BG-06", "BG-07"]


def decide(b: Bridge, kind: str, decision: str = "approve") -> dict:  # type: ignore[type-arg]
    c = b.h.engine.control.c
    rec = next(r for r in c.recs.values() if r.kind == kind)
    b.h.client({"type": "control_decision", "cmd_id": f"d-{rec.id}", "rec_id": rec.id, "decision": decision, "by": "Shift lead"})
    assert b.h.last_ack()["ok"], b.h.last_ack()
    return {"rec": rec.id}


def wos(b: Bridge, kind: str) -> list:  # type: ignore[type-arg]
    return [w for w in b.h.engine.control.c.wos.values() if w.kind == kind]


def test_bearing_chain_wear_anomaly_approval_technician_repair_normal(h: Harness) -> None:
    b = Bridge(h, ["MM-01", "MM-02", *TECH_IDS], hour=10.5)
    e = h.engine
    m = e.production.machines["M-01"]
    sim_m = b.sim.core.get("production").machines["MM-01"]
    sim_m.next_minor_s = 1e9  # keep this test about the bearing
    b.run(150)  # baseline learned while healthy
    assert m.base.learned and not wos(b, "bearing")
    b.sim.command("MM-01", "degrade")
    for _ in range(4 * 200):
        b.step()
        if wos(b, "bearing"):
            break
    wo = wos(b, "bearing")[0]
    assert wo.state == "awaiting_approval" and "vibration abnormal" in wo.cause
    assert any(r.kind == "stop_machine" and r.wo_id == wo.id for r in e.control.c.recs.values())
    assert not any(o.topic.endswith("MM-01/cmd/repair") for o in h.mqtt)  # nothing stops until a person says so
    decide(b, "stop_machine")
    assert wo.state == "dispatched" and wo.technician == "WK-06"
    assert any(o.topic == "twin/FAC-01/BG-06/cmd/goto" for o in h.mqtt)  # the technician walks there
    for _ in range(4 * 300):
        b.step()
        if wo.state == "in_progress":
            break
    assert wo.state == "in_progress"
    assert any(o.topic.endswith("MM-01/cmd/repair") for o in h.mqtt)
    tech = e.safety.workers["WK-06"]
    assert ((tech.x - e.world.entities["M-01"].x) ** 2 + (tech.z - e.world.entities["M-01"].z) ** 2) ** 0.5 < 6
    b.run(25 * 60 + 60)  # the 25 min bearing change, then back to work
    assert wo.state == "done" and "new bearing fitted" in (wo.result or "")
    assert sim_m.wear < 0.1 and sim_m.defect_rate == 0
    assert not m.base.learned  # relearning its normal
    acts = [a for a in e.control.c.actions]
    assert any("approved stopping M-01" in a.action for a in acts)
    assert any(a.result and "new bearing fitted" in a.result for a in acts)  # cause -> action -> result
    assert any(o.topic == "twin/FAC-01/BG-06/cmd/route" for o in h.mqtt)  # back to the usual round


def test_dismissed_work_order_stops_nothing(h: Harness) -> None:
    b = Bridge(h, ["MM-01", "MM-02", *TECH_IDS], hour=10.5)
    b.sim.core.get("production").machines["MM-01"].next_minor_s = 1e9
    b.run(150)
    b.sim.command("MM-01", "degrade")
    for _ in range(4 * 200):
        b.step()
        if wos(b, "bearing"):
            break
    decide(b, "stop_machine", "dismiss")
    wo = wos(b, "bearing")[0]
    assert wo.state == "dismissed"
    b.run(30)
    assert not any(o.topic.endswith("/cmd/repair") or o.topic.endswith("BG-06/cmd/goto") for o in h.mqtt)


def test_a_bearing_that_fails_before_approval_closes_as_a_breakdown(h: Harness) -> None:
    b = Bridge(h, ["MM-01", "MM-02", *TECH_IDS], hour=10.5)
    sim_m = b.sim.core.get("production").machines["MM-01"]
    sim_m.next_minor_s = 1e9
    b.run(150)
    b.sim.command("MM-01", "degrade")
    for _ in range(4 * 900):
        b.step()
        if wos(b, "bearing") and wos(b, "bearing")[0].state == "broke_down":
            break
    wo = wos(b, "bearing")[0]
    assert wo.state == "broke_down" and "failed before the repair" in (wo.result or "")
    assert not any(r.wo_id == wo.id for r in h.engine.control.c.recs.values())


def test_leak_chain_break_measurement_fix_and_follow_up(h: Harness) -> None:
    b = Bridge(h, ["MM-01", "MM-02", "MM-03", "MM-04", "CP-01", "CP-02", *TECH_IDS], hour=10.5)
    e = h.engine
    e.control.cfg["leak_fix_min"] = 2  # a short job for the test
    air = b.sim.core.get("air")
    air.leak_ref = 0.6  # a neglected network
    b.run(60)
    b.sim.local_hour = lambda: 12.2  # type: ignore[method-assign]  # lunch: no machine uses air
    b.run(240)
    b.sim.local_hour = lambda: 12.6  # type: ignore[method-assign]  # back to work
    b.run(5)
    assert e.control.c.leak_estimate is not None and e.control.c.leak_estimate > 0.35
    wo = wos(b, "leak_fix")[0]
    assert wo.state == "dispatched" and wo.technician == "WK-07"  # no production stop: dispatched at once
    for _ in range(4 * 600):
        b.step()
        if wo.state == "done":
            break
    assert wo.state == "done" and air.leak_ref == b.sim.params.f("air.leaks.after_fix_nm3_min")
    before = e.control.c.leak_estimate
    b.sim.local_hour = lambda: 17.05  # type: ignore[method-assign]  # B-shift tea break: measure again
    b.run(240)
    b.sim.local_hour = lambda: 17.4  # type: ignore[method-assign]
    b.run(5)
    assert e.control.c.leak_estimate < before * 0.5
    assert "next break" in (wo.result or "") or "measured at the next break" in (wo.result or "")


def test_compressor_service_by_run_hours(h: Harness) -> None:
    b = Bridge(h, ["MM-01", "MM-02", "CP-01", "CP-02", *TECH_IDS], hour=10.5)
    e = h.engine
    e.control.cfg["compressor_service_min"] = 3
    e.control.c._last_service["CP-01"] = 1240.0 - 2000.0  # due now
    b.run(20)
    wo = wos(b, "compressor_service")[0]
    assert wo.asset == "CP-01" and wo.state == "dispatched"
    for _ in range(4 * 600):
        b.step()
        if wo.state == "in_progress":
            break
    assert any(o.topic.endswith("CP-01/cmd/service") for o in h.mqtt)
    b.run(30)
    air = b.sim.core.get("air")
    assert air.compressors["CP-01"].state == "stopped"  # out for service
    b.run(200)
    assert wo.state == "done" and air.compressors["CP-01"].service_hours < 1
    assert air.bar > 5.8  # the standby covered


def test_peak_demand_sheds_and_restores(h: Harness) -> None:
    b = Bridge(h, ["PM-01", "PM-02", "PM-03", "PM-04", "PM-05", "PM-06", "PM-07", "PM-08", "MM-01", "MM-02"], hour=21.0)
    e = h.engine
    e.devices.cfg["utilities"]["peak_kw"] = 60.0  # a low limit so the night load trips it
    b.run(420)  # the 15-min demand needs 5 min of register history
    c = e.control.c
    assert c.shed and any(o.topic.endswith("PM-04/cmd/shed") for o in h.mqtt)
    assert b.sim.core.get("power").shed
    ev = b.sim.core.q.power_kw["EV chargers"]
    assert ev == b.sim.params.f("loads.ev.base_kw")
    e.devices.cfg["utilities"]["peak_kw"] = 1000.0
    b.run(11 * 60)
    assert not c.shed and not b.sim.core.get("power").shed
    shed_act = next(a for a in c.actions if a.action.startswith("BMS asked to shed"))
    assert shed_act.result and "demand fell" in shed_act.result


def test_fire_alarm_asks_a_person_to_call_the_fire_brigade(h: Harness) -> None:
    b = Bridge(h, ["FP-01"], hour=10.5)
    b.run(5)
    b.beat("fire_alarm")
    b.run(15)
    c = h.engine.control.c
    assert any(r.kind == "emergency_call" for r in c.recs.values())
    decide(b, "emergency_call")
    assert any("confirmed calling the fire brigade" in a.action for a in c.actions)


def test_plant_interlocks_in_the_simulator() -> None:
    """The plant's own interlocks (PLC): gas alarm -> extract fan full and hot work stopped; fire alarm -> fire doors
    close; cold room door open too long -> local alarm. Logged with their causes."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    from site_sim import SiteSim  # type: ignore[import-not-found]
    s = SiteSim(CFG, [], seed=2)
    s.verbose = False
    s.local_hour = lambda: 10.5  # type: ignore[method-assign]
    for _ in range(40):
        s.step(0.25)
    q, p = s.core.q, s.params
    assert q.power_kw["Welding (hot work)"] > 0
    s.core.command("GD-04", "leak", {})
    for _ in range(4 * 60):
        s.step(0.25)
    assert "FAC01_HAZMAT" in q.flags["gas_alarm_zones"]
    assert q.power_kw["Extract fan GD-04"] == p.f("gas.fan_kw") and q.power_kw["Welding (hot work)"] == 0
    s.core.command("FP-01", "alarm", {})
    for _ in range(8):
        s.step(0.25)
    doors = s.core.get("doors").doors
    assert all(not doors[d]["open"] for d in p.v("doors.fire_doors"))
    s.core.command("DR-01", "door_open", {"seconds": 200})
    for _ in range(4 * 130):
        s.step(0.25)
    assert q.flags["cold_door_alarm"]
    names = [e.name for e in s.core.log]
    for n in ("hot work stopped", "FAC01_HAZMAT extract fan full speed", "fire door holds released", "cold room door alarm sounding"):
        assert n in names, n
    assert all(e.cause for e in s.core.log)
    assert json.dumps([d for d in DEF])  # noqa: imported names stay used
