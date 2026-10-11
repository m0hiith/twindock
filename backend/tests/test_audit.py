"""S10 value-source audit, backend side: only real things carry source "device"."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import Harness

from twindock.contract import validator

SITES = json.loads((Path(__file__).resolve().parents[1] / "world" / "sites.json").read_text())


def test_site_topics_cannot_claim_to_be_real() -> None:
    for name in ("mqtt/site_hello", "mqtt/site_status", "mqtt/site_reading"):
        schema = validator(name).schema
        assert schema["properties"]["source"] == {**schema["properties"]["source"], "const": "sim"}
        assert "source" in schema["required"]


def test_only_real_things_are_device_sourced(h: Harness) -> None:
    h.board_online()
    for d in SITES["devices"]:
        if d["source"] != "sim":
            continue
        hello = {"type": d["type"], "protocol": d["protocol"], "capabilities": d["capabilities"],
                 "fw_version": "sim-1.0", "source": "sim"}
        h.engine.on_mqtt(f"twin/{d['site_id']}/{d['id']}/hello", json.dumps(hello).encode())
        ch = d["capabilities"][0]
        value = [100.0, 14.0] if ch == "position" else ("running" if ch == "state" else 1)
        h.engine.on_mqtt(f"twin/{d['site_id']}/{d['id']}/{ch}",
                         json.dumps({"ts_ms": 1, "value": value, "source": "sim"}).encode())
    h.run(2.0)
    h.engine.on_connect("client-9")
    h.collect()
    snap = h.of_type("world_snapshot")[-1]
    real_units = {u["id"] for u in snap["units"] if u["source"] == "device"}
    assert real_units == {"GW-01"}  # forklifts become device-sourced only via a calibrated BLE tag
    assert {d["id"] for d in snap["devices"] if d["source"] == "device"} == {"GW-01", "RB-01"}
    for u in snap["units"]:
        if u["kind"] in ("machine", "worker"):
            assert u["source"] == "sim"
    for m in h.of_type("device_update"):
        for d in m["devices"]:
            assert d["source"] == ("device" if d["id"] in ("GW-01", "RB-01") else "sim")
