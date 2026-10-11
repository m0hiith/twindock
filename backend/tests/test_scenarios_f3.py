"""F3: each campus scenario end to end: simulated devices (tools/site_sim.py physics) -> MQTT -> rules -> alerts ->
monitoring summary, with the backend and the simulator wired together in one process."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from conftest import Harness

from twindock.devices import load_sites

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SiteSim  # noqa: E402

CFG = load_sites()
DEF = {d["id"]: d for d in CFG["devices"]}


class Bridge:
    """The engine and a SiteSim for some devices, both advanced by `step`: the sim's publishes go to the engine's MQTT
    input and the engine's site commands go back to the sim."""

    def __init__(self, h: Harness, ids: list[str], hour: float = 12.0, sun: float = 0.8) -> None:
        self.h = h
        h.engine.set_mqtt_connected(True)
        h.engine._sun = lambda _now: sun  # type: ignore[method-assign]
        self.sim = SiteSim(CFG, [DEF[i] for i in ids], seed=11)
        self.sim.local_hour = lambda: hour  # type: ignore[method-assign]
        self.out: list[tuple[str, dict]] = []  # type: ignore[type-arg]
        self.sim.publish = lambda m, ch, p, retain=False: self.out.append((f"twin/{m.d['site_id']}/{m.id}/{ch}", p))  # type: ignore[method-assign]
        self.sim.hellos()
        self.cmd_seen = 0

    def step(self, dt: float = 0.25) -> None:
        h = self.h
        h.clock.ms += int(dt * 1000)
        self.sim.step(dt)
        for topic, payload in self.out:
            h.engine.on_mqtt(topic, json.dumps(payload).encode(), False)
        self.out.clear()
        h.engine.tick(dt)
        h.collect()
        for o in h.mqtt[self.cmd_seen:]:
            self.sim.on_command(o.topic, json.dumps(o.payload).encode())
        self.cmd_seen = len(h.mqtt)

    def run(self, seconds: float) -> None:
        for _ in range(round(seconds / 0.25)):
            self.step()

    def beat(self, beat: str) -> None:
        self.h.client({"type": "scenario_command", "cmd_id": f"b-{beat}", "beat": beat})
        assert self.h.last_ack()["ok"], self.h.last_ack()

    def open_alerts(self) -> dict[str, list[dict]]:  # type: ignore[type-arg]
        out: dict[str, list[dict]] = {}  # type: ignore[type-arg]
        for a in self.h.engine.rules.wire()["alerts"]:
            if a["state"] != "resolved":
                out.setdefault(a["rule_id"], []).append(a)
        return out


POWER = ["PM-01", "PM-02", "PM-03", "PM-04", "PM-05", "PM-06", "PM-07", "TL-02"]


def test_grid_failure_chain(h: Harness) -> None:
    b = Bridge(h, POWER + ["MM-01", "MM-02", "CV-01", "FP-03", "GD-04"])
    b.run(30)
    p = h.engine.power_summary()
    assert p["grid_ok"] is True and p["solar_kw"] > 100 and (p["generator_kw"] or 0) < 1
    assert "grid_failure" not in b.open_alerts()
    zone_kw = {z["meter"]: z["kw"] for z in p["by_zone"]}
    assert all(v is not None and v > 0 for v in zone_kw.values()), zone_kw

    b.beat("grid_failure")
    b.run(14)
    assert [a["severity"] for a in b.open_alerts()["grid_failure"]] == ["critical"]  # devices -> rules -> alerts
    p = h.engine.power_summary()
    assert p["grid_ok"] is False and p["solar_kw"] == 0.0  # no solar without the grid (islanding protection)
    assert (p["generator_kw"] or 0) > 1, "the generator should have picked up the critical loads"
    assert h.engine.devices.wire_device("FP-03", h.engine.gw, h.clock.ms, h.engine.ble)["status"] == "online"  # critical zone stays on
    assert h.engine.devices.wire_device("GD-04", h.engine.gw, h.clock.ms, h.engine.ble)["status"] == "online"
    b.run(28)
    assert h.engine.devices.wire_device("MM-01", h.engine.gw, h.clock.ms, h.engine.ble)["status"] in ("stale", "offline")  # mains lost elsewhere
    assert "devices_without_power" in b.open_alerts()
    inc = next(i for i in h.engine.monitor_summary()["incidents"] if i["rule_id"] == "grid_failure")  # monitoring centre has it
    assert inc["severity"] == "critical"
    # critical load only: far less than the whole campus
    assert (h.engine.power_summary()["generator_kw"] or 0) < 60

    b.beat("reset")
    b.run(30)
    assert "grid_failure" not in b.open_alerts() and h.engine.power_summary()["grid_ok"] is True
    assert h.engine.devices.wire_device("MM-01", h.engine.gw, h.clock.ms, h.engine.ble)["status"] == "online"


def test_gas_leak_in_the_hazardous_store_chain(h: Harness) -> None:
    b = Bridge(h, ["GD-04", "BG-06"])
    e = h.engine
    badge = b.sim.core.get("people").walkers["BG-06"]  # a maintenance worker (allowed in the store) is inside it, standing still
    badge.x, badge.z, badge.still_until = 203.0, 70.0, 1e9
    b.run(30)
    wk = e.safety.workers["WK-06"]
    assert wk.zone_id == "FAC01_HAZMAT" and wk.fresh
    assert "gas_alarm" not in b.open_alerts() and wk.evacuate is None
    b.beat("gas_leak")
    b.run(12)
    assert [a["severity"] for a in b.open_alerts()["gas_alarm"]] == ["critical"]
    assert e.safety.gas_zones == ["FAC01_HAZMAT"]
    # the worker leaves at once, so the alert may already be resolved: the incident log keeps it
    ev = [i for i in e.monitor_summary()["incidents"] if i["rule_id"] == "evacuate_worker" and i["subject_id"] == "WK-06"]
    assert ev and "gas alarm nearby" in ev[0]["message"] and ev[0]["severity"] == "critical"
    assert any(m.topic == "twin/FAC-01/BG-06/cmd/goto" for m in h.mqtt)  # the badge is sent to a muster point
    su = h.of_type("safety_update")[-1]
    route = next(r for r in su["routes"] if r["zone_id"] == "FAC01_HAZMAT")
    mp = next(m for m in CFG["muster_points"] if m["id"] == route["muster_id"])
    assert ((mp["x"] - 203) ** 2 + (mp["z"] - 70) ** 2) ** 0.5 >= 40  # a muster point away from the hazard, not the nearest
    assert route["points"][-1] == [e.ped.nodes[mp["node"]][0], e.ped.nodes[mp["node"]][1]]
    assert any(i["rule_id"] == "gas_alarm" for i in e.monitor_summary()["incidents"])
    b.run(45)  # the badge walked to the muster point; the worker is out of the store
    assert ((e.safety.workers["WK-06"].x - 203) ** 2 + (e.safety.workers["WK-06"].z - 70) ** 2) ** 0.5 > 20
    b.beat("reset")
    b.run(60)
    assert "gas_alarm" not in b.open_alerts()


def test_fire_alarm_in_the_warehouse_chain(h: Harness) -> None:
    b = Bridge(h, ["FP-01", "FP-03", "PM-07", "PM-04", "PM-01", "PM-02", "PM-03", "PM-05", "PM-06", "TL-02"])
    e = h.engine
    b.run(20)
    assert e.safety.evacuation is None
    before = h.engine.power_summary()["by_zone"]
    b.beat("fire_alarm")
    b.run(20)
    fire = b.open_alerts()["fire_alarm"]
    assert [a["subject_id"] for a in fire] == ["FP-01"] and fire[0]["severity"] == "critical"
    assert e.safety.evacuation is not None and e.safety.evacuation.reason.startswith("fire alarm")  # K3 evacuation, started by the alarm
    assert e.safety.evacuation.by == "Fire panel bridge"
    hc = h.of_type("safety_update")[-1]["evacuation"]
    assert hc is not None and hc["reason"].startswith("fire alarm")
    pump = next(z for z in e.power_summary()["by_zone"] if z["meter"] == "PM-07")["kw"]
    assert pump > 30, "the fire pump runs while a fire panel is in alarm"
    assert next(z for z in before if z["meter"] == "PM-07")["kw"] < 5
    # advice only: it closes nothing, so there is no command to anything but badges and the simulated panel
    assert all("/cmd/" in o.topic and not o.topic.startswith("twin/gateway") for o in h.mqtt)
    su = h.of_type("safety_update")[-1]
    assert su["routes"], "routes to the nearest muster point are shown during the evacuation"
    assert all(r["points"] and r["muster_id"] in {m["id"] for m in CFG["muster_points"]} for r in su["routes"])
    assert any(i["rule_id"] == "fire_alarm" for i in e.monitor_summary()["incidents"])
    b.beat("reset")
    b.run(10)
    assert "fire_alarm" not in b.open_alerts() and e.safety.evacuation is None


def test_compressor_fault_chain(h: Harness) -> None:
    """R1: the duty compressor trips -> pressure falls -> below 6 bar the low-pressure alert, below 5 bar the line
    stops on low air -> the standby compressor starts after its sequencer delay and loads -> pressure recovers and
    the line restarts. Every step is a consequence of the one before, through the air header."""
    b = Bridge(h, ["CP-01", "CP-02", "MM-01", "MM-02", "PM-06", "PM-04", "PM-05", "TL-02", "PM-01", "PM-02", "PM-03", "PM-07"])
    e = h.engine
    b.run(80)
    assert e.production.machines["M-01"].cycle_time_s is not None and "compressor_fault" not in b.open_alerts()
    b.beat("compressor_fault")
    b.run(40)  # 7.5 → 6 bar takes ~25 s at the line's demand, then the 10 s the rule waits
    alerts = b.open_alerts()
    assert [a["severity"] for a in alerts["compressor_fault"]] == ["critical"]
    assert "low_air_pressure" in alerts  # pressure stayed below 6 bar for 10 s
    cp1, cp2 = e.devices.sim["CP-01"].readings, e.devices.sim["CP-02"].readings
    assert cp1["current_a"].value < 1.0 and cp1["loaded"].value is False  # a tripped compressor draws nothing
    stopped = [m for m in e.production.machines.values() if m.last_fault and m.last_fault["text"] == "Low air pressure"]
    assert stopped, "the air trip stopped the pneumatic machines"
    b.run(10)
    assert cp2["loaded"].value is True  # the standby started (sequencer delay + star-delta) and took over
    b.run(80)
    assert e.devices.sim["CP-01"].readings["tripped"].value is True
    assert e.devices.sim["CP-02"].readings["pressure_bar"].value > 6.0
    assert "low_air_pressure" not in b.open_alerts()
    assert all(e.production.machines[m].state in ("running", "idle", "fault") for m in ("M-01", "M-02"))
    assert e.production.machines["M-01"].state != "fault" or e.production.machines["M-01"].last_fault["text"] != "Low air pressure"
    pm06 = next(z for z in e.power_summary()["by_zone"] if z["meter"] == "PM-06")["kw"]
    assert 1 < pm06 < 25  # one 15 kW compressor (loaded or unloaded) carries the load, never two
    b.beat("reset")
    b.run(30)
    assert "compressor_fault" not in b.open_alerts()


def test_energy_dashboard_numbers_and_peak_warning(h: Harness) -> None:
    b = Bridge(h, POWER + ["MM-01", "MM-02", "CV-01"])
    b.run(150)
    p = h.engine.power_summary()
    assert p["demand_kw"] > 50 and 0 < p["solar_share"] <= 1 and p["solar_kw"] > 0
    assert p["kwh_per_unit"] is not None and p["kwh_per_unit"] > 0 and p["units_today"] > 0
    assert p["other_kw"] is not None and p["other_kw"] >= 0
    # peak warning: with a low limit the grid import trips it after 30 s
    h.engine._sun = lambda _now: 0.0  # type: ignore[method-assign]
    b.sim.local_hour = lambda: 0.0  # type: ignore[method-assign]  # night: no solar, so everything is grid import
    h.engine.devices.cfg["utilities"]["peak_kw"] = 20.0
    b.run(50)
    assert "peak_demand" in b.open_alerts()
    assert h.engine.power_summary()["peak_exceeded"] is True


def test_etp_outflow_out_of_band_warning(h: Harness) -> None:
    b = Bridge(h, ["WQ-01", "WQ-02"])
    b.run(40)
    assert "etp_outflow_ph" not in b.open_alerts()
    b.sim.command("WQ-02", "upset")
    b.run(120)
    a = b.open_alerts()
    assert "etp_outflow_ph" in a and "etp_outflow_turbidity" in a
    assert not any(x["subject_id"] == "WQ-01" for v in a.values() for x in v)  # the inflow is allowed to be rough


def test_evacuating_badges_follow_the_walkways(h: Harness) -> None:
    """The route a badge walks is the pedestrian graph's, not a straight line through buildings."""
    b = Bridge(h, ["BG-08"])
    e = h.engine
    badge = b.sim.core.get("people").walkers["BG-08"]
    b.run(5)
    badge.x, badge.z = 194.5, 22.0  # at the ETP door
    mp = next(m for m in CFG["muster_points"] if m["id"] == "MP-3")
    path = e._walk_path("BG-08", mp)
    assert path and path[0][0] in (194.5, 192) and path[-1] == [e.ped.nodes[mp["node"]][0], e.ped.nodes[mp["node"]][1]]
    nodes = [e.ped.nearest(x, z) for x, z in path]
    assert "XS3" in nodes or "XN3" in nodes  # it uses the marked crossing X3 over the service road
    b.sim.command("BG-08", "goto", {"x": mp["x"], "z": mp["z"], "path": path})
    seen_corridor = False
    for _ in range(400):
        b.step()
        seen_corridor = seen_corridor or abs(badge.x - 192) < 0.6
    assert seen_corridor and abs(badge.x - mp["x"]) < 1 and abs(badge.z - mp["z"]) < 1
