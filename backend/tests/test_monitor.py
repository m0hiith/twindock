"""K4: incident log (ack/response/resolution times) and energy (today vs yesterday, never invented)."""

from __future__ import annotations

import time

from conftest import Harness

from twindock.rules import Rules, load_rules

ZONE = {"id": "FAC01_PRODUCTION"}


def test_incident_log_has_ack_and_resolution_times() -> None:
    r = Rules(load_rules())
    t0 = 1_700_000_000_000
    facts = {"worker": [{"id": "WK-01", "unit_id": "WK-01", "role_text": "press operator", "sos": True, "zone_name": "Production",
                         "first_aider_text": "none on site", "x": 1.0, "z": 2.0, "site_id": "FAC-01"}]}
    raised, _ = r.evaluate(facts, t0)
    assert [a.rule_id for a in raised] == ["sos"]
    assert r.acknowledge(raised[0].id, "Monitor", t0 + 12_000) is None
    r.evaluate({"worker": [{**facts["worker"][0], "sos": None}]}, t0 + 90_000)
    inc = r.incidents(t0 + 100_000)
    assert len(inc) == 1 and inc[0]["response_s"] == 12.0 and inc[0]["resolution_s"] == 90.0 and inc[0]["acknowledged_by"] == "Monitor"
    assert r.incidents(t0 + 25 * 3_600_000) == []  # only the last 24 h


def test_energy_today_vs_yesterday_is_not_invented(h: Harness) -> None:
    e = h.engine
    now = h.clock.ms
    st = e.devices.sim["PM-04"]
    from twindock.devices import Reading
    st.last_seen_ms = now
    st.readings["energy_kwh"] = Reading(5200.0, now, "kWh")
    st.readings["power_kw"] = Reading(40.0, now, "kW")
    feeder = e.devices.sim["PM-01"]  # a feeder is already inside the incomer's reading: never added on top
    feeder.last_seen_ms = now
    feeder.readings["energy_kwh"] = Reading(900.0, now, "kWh")
    feeder.readings["power_kw"] = Reading(25.0, now, "kW")
    e._tick_energy()
    s = e.monitor_summary()["energy"]
    assert s["kw_now"] == 40.0 and s["today_kwh"] == 0.0 and s["yesterday_kwh"] is None
    assert s["meters"] == ["PM-04"]
    st.readings["energy_kwh"] = Reading(5210.5, now, "kWh")
    assert e.monitor_summary()["energy"]["today_kwh"] == 10.5
    # a day later the old total becomes yesterday
    day = time.strftime("%Y-%m-%d", time.localtime(now / 1000))
    e._energy["PM-04"]["day"] = "2000-01-01"
    st.readings["energy_kwh"] = Reading(5300.0, now, "kWh")
    e._tick_energy()
    assert e._energy["PM-04"]["day"] == day
    s = e.monitor_summary()["energy"]
    assert s["yesterday_kwh"] == 100.0 and s["today_kwh"] == 0.0
