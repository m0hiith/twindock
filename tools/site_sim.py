#!/usr/bin/env python3
"""TwinDock site simulator: every simulated device of the site twin in one process.

    .venv/bin/python tools/site_sim.py                       # all sim devices
    .venv/bin/python tools/site_sim.py --zones production    # only some zones (id or kind)
    .venv/bin/python tools/site_sim.py --site FAC-01

Publishes on twin/<site>/<device>/<channel> through the same broker, with source "sim" and
fw_version "sim-x.y", validated against shared/schemas/mqtt/site_*.json before sending.
It never publishes under twin/gateway/ and refuses devices whose source is "device" (GW-01,
the real board). Stopping it (Ctrl-C) only stops publishing: the retained hellos stay, so the
twin shows the devices going stale, then offline.
"""

from __future__ import annotations

import argparse
import json
import random
import signal
import sys
import time
from pathlib import Path
from typing import Any, Callable

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))  # the simulation core lives in backend/sim (shared with the embedded simulator)
from sim import Params, build_core  # noqa: E402
from sim.devices import Device, make_device  # noqa: E402

SITES = BACKEND / "world" / "sites.json"
LAYOUT = BACKEND / "world" / "layout.json"
SCHEMAS = ROOT / "shared" / "schemas"


def load_validators() -> dict[str, jsonschema.Draft202012Validator]:
    res = []
    by: dict[str, Any] = {}
    for f in SCHEMAS.glob("*/*.json"):
        s = json.loads(f.read_text())
        by[f"{f.parent.name}/{f.stem}"] = s
        res.append((s["$id"], Resource.from_contents(s)))
    reg = Registry().with_resources(res)
    return {k: jsonschema.Draft202012Validator(by[f"mqtt/site_{k}"], registry=reg) for k in ("hello", "status", "reading", "cmd")}


def select_devices(cfg: dict[str, Any], site: str | None, zones: list[str] | None) -> list[dict[str, Any]]:
    kind_of = {z["id"]: z["kind"] for s in cfg["sites"] for z in s["zones"]}
    out = []
    for d in cfg["devices"]:
        if d["source"] != "sim":
            continue  # the real board is never simulated here
        if site and d["site_id"] != site:
            continue
        if zones and d["zone_id"] not in zones and kind_of.get(d["zone_id"]) not in zones:
            continue
        out.append(d)
    return out


def wall_hour() -> float:
    lt = time.localtime()
    return lt.tm_hour + lt.tm_min / 60.0


class SiteSim:
    """The whole campus's true state (backend/sim core) plus the selected SIM devices that publish readings of it.
    `models` maps device id -> its simulated device (kept under that name for the tools and tests that use it)."""

    def __init__(self, cfg: dict[str, Any], devices: list[dict[str, Any]], seed: int | None = None,
                 params: Params | None = None) -> None:
        self.cfg = cfg
        self.params = params or Params.load()
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.local_hour: Callable[[], float] = wall_hour  # the backend points this at its simulation clock
        self.core = build_core(cfg, json.loads(LAYOUT.read_text()), self.params, self.seed, lambda: self.local_hour())
        for d in devices:
            assert d["source"] == "sim", "refusing to simulate a real device"
        self.models: dict[str, Device] = {d["id"]: make_device(d, self.core) for d in devices}
        self.v = load_validators()
        self.t = 0.0  # simulated seconds since start (advanced by step(dt), so tests run fast)
        self.client: Any = None  # paho client when publishing to a broker
        self.sink: Callable[[str, bytes, bool], None] | None = None  # in-process delivery as MQTT bytes
        self.sink_obj: Callable[[str, dict[str, Any], bool], None] | None = None  # in-process delivery of the payload object
        self.sent = 0
        self.verbose = True
        # Schema check before sending. The backend's warm start turns it off while it fast-forwards in-process:
        # the engine still validates every message it receives, so nothing unchecked reaches the twin.
        self.validate = True

    def topic(self, m: Device, channel: str) -> str:
        assert m.d["source"] == "sim", "refusing to publish for a real device"
        t = f"twin/{m.d['site_id']}/{m.id}/{channel}"
        assert not t.startswith("twin/gateway/")
        return t

    def publish(self, m: Device, channel: str, payload: dict[str, Any], retain: bool = False) -> None:
        kind = channel if channel in ("hello", "status") else "reading"
        if self.validate:
            self.v[kind].validate(payload)
        if self.sink_obj is not None:
            self.sink_obj(self.topic(m, channel), payload, retain)
        if self.sink is not None or self.client is not None:
            data = json.dumps(payload, separators=(",", ":"))
            if self.sink is not None:
                self.sink(self.topic(m, channel), data.encode(), retain)
            if self.client is not None:
                self.client.publish(self.topic(m, channel), data, qos=0, retain=retain)
        self.sent += 1

    def on_command(self, topic: str, payload: bytes) -> None:
        """twin/<site>/<device>/cmd/<action> from the backend (sim devices only)."""
        parts = topic.split("/")
        if len(parts) != 5 or parts[3] != "cmd":
            return
        m = self.models.get(parts[2])
        if m is None or m.d["site_id"] != parts[1]:
            return
        try:
            data = json.loads(payload)
            self.v["cmd"].validate(data)
        except (ValueError, jsonschema.ValidationError) as e:
            if self.verbose:
                print(f"[sim] ignored invalid command on {topic}: {e}")
            return
        self.command(m.id, parts[4], data)

    def command(self, device_id: str, action: str, data: dict[str, Any] | None = None) -> bool:
        """A command to one simulated device: the device itself (silence) or the true-state model behind it."""
        data = data or {}
        m = self.models[device_id]
        ok = m.command(action, data) or self.core.command(device_id, action, data)
        if self.verbose:
            print(f"[sim] {device_id}: {action} ({data.get('cmd_id')}){'' if ok else ' (not handled)'}")
        return ok

    def hellos(self) -> None:
        for m in self.models.values():
            self.publish(m, "hello", m.hello(), retain=True)

    def step(self, dt: float) -> None:
        self.t += dt
        self.core.advance(dt)
        t = self.core.t
        ts_ms = int(self.t * 1000)
        for m in self.models.values():
            out, status_due = m.step(t, dt, ts_ms)
            if m.silent or m.power_off or m.dormant:
                continue
            for channel, payload in out:
                self.publish(m, channel, payload)
            if status_due:
                self.publish(m, "status", m.status(ts_ms))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--site", help="only this site (WH-01, FAC-01)")
    ap.add_argument("--zones", help="comma-separated zone ids or kinds (production, cold_room, ...)")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    import paho.mqtt.client as mqtt  # only the standalone simulator needs a broker client
    cfg = json.loads(SITES.read_text())
    devices = select_devices(cfg, a.site, a.zones.split(",") if a.zones else None)
    if not devices:
        sys.exit("no simulated devices match --site/--zones")
    s = SiteSim(cfg, devices, a.seed)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"twindock-site-sim-{random.randint(0, 99999)}")
    c.on_message = lambda _c, _u, msg: s.on_command(msg.topic, msg.payload)
    c.on_connect = lambda cl, *_: cl.subscribe("twin/+/+/cmd/#", qos=1)
    c.connect(a.host, a.port, keepalive=30)
    c.loop_start()
    s.client = c
    print(f"[sim] SIMULATED devices only ({len(devices)}): {', '.join(d['id'] for d in devices)}")
    print("[sim] the real board (GW-01) is never simulated; Ctrl-C stops publishing")
    s.hellos()
    stop = False

    def on_sig(*_: Any) -> None:
        nonlocal stop
        stop = True
    signal.signal(signal.SIGINT, on_sig)
    signal.signal(signal.SIGTERM, on_sig)
    period = 0.25
    last = time.monotonic()
    while not stop:
        time.sleep(period)
        now = time.monotonic()
        s.step(now - last)
        last = now
    c.loop_stop()
    c.disconnect()
    print(f"[sim] stopped after {s.sent} messages; devices will show stale, then offline")


if __name__ == "__main__":
    main()
