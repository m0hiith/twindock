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
from typing import Any

import jsonschema
import paho.mqtt.client as mqtt
from referencing import Registry, Resource

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_models import Model, make  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITES = ROOT / "backend" / "world" / "sites.json"
LAYOUT = ROOT / "backend" / "world" / "layout.json"
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


class SiteSim:
    def __init__(self, cfg: dict[str, Any], devices: list[dict[str, Any]], seed: int | None = None) -> None:
        self.cfg = cfg
        self.rng = random.Random(seed)
        devices = [self.with_routes(d) for d in devices]
        self.models: dict[str, Model] = {d["id"]: make(d, self.rng) for d in devices}
        self.v = load_validators()
        self.t = 0.0  # simulated seconds since start (advanced by step(dt), so tests run fast)
        self.client: mqtt.Client | None = None
        self.sent = 0

    def with_routes(self, d: dict[str, Any]) -> dict[str, Any]:
        """Badges walk their worker's routes: node ids from sites.json -> layout coordinates."""
        w = next((w for w in self.cfg.get("workers", []) if w["badge"] == d["id"]), None)
        if w is None:
            return d
        nodes = {n["id"]: n for n in json.loads(LAYOUT.read_text())["nodes"]}
        routes = {name: [(nid, float(nodes[nid]["x"]), float(nodes[nid]["z"])) for nid in ids]
                  for name, ids in w["routes"].items()}
        return {**d, "_routes": routes, "_walk_speed": self.cfg.get("safety", {}).get("walk_speed_mps", 1.3)}

    def topic(self, m: Model, channel: str) -> str:
        assert m.d["source"] == "sim", "refusing to publish for a real device"
        t = f"twin/{m.d['site_id']}/{m.id}/{channel}"
        assert not t.startswith("twin/gateway/")
        return t

    def publish(self, m: Model, channel: str, payload: dict[str, Any], retain: bool = False) -> None:
        kind = channel if channel in ("hello", "status") else "reading"
        self.v[kind].validate(payload)
        if self.client is not None:
            self.client.publish(self.topic(m, channel), json.dumps(payload, separators=(",", ":")), qos=0, retain=retain)
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
            print(f"[sim] ignored invalid command on {topic}: {e}")
            return
        t = self.t
        action = parts[4]
        if action == "silence":
            m.silent = bool(data.get("on", True))
        elif action == "door_open" and hasattr(m, "force_open"):
            m.force_open(t, float(data.get("seconds", 90)))  # type: ignore[attr-defined]
        elif action == "route" and hasattr(m, "command"):
            m.command(action, t, int(t * 1000), data)  # type: ignore[attr-defined]
        elif hasattr(m, "command"):
            m.command(action, t, int(t * 1000))  # type: ignore[attr-defined]
        print(f"[sim] {m.id}: {action} ({data.get('cmd_id')})")

    def hellos(self) -> None:
        for m in self.models.values():
            self.publish(m, "hello", m.hello(), retain=True)

    def couple(self) -> None:
        """Cross-device physics: a cold room's env sensors feel its door."""
        doors = [m for m in self.models.values() if m.d["type"] == "door_sensor"]
        for m in self.models.values():
            if m.d["type"] == "env_sensor":
                m.door_open = any(getattr(dm, "open", False) for dm in doors if dm.d["zone_id"] == m.d["zone_id"])  # type: ignore[attr-defined]

    def step(self, dt: float) -> None:
        self.t += dt
        t = self.t
        ts_ms = int(t * 1000)
        self.couple()
        for m in self.models.values():
            out = m.step(t, dt, ts_ms)
            if m.silent:
                continue
            for channel, payload in out:
                self.publish(m, channel, payload)
            if m.every("status", t, 10.0):
                self.publish(m, "status", m.status(ts_ms))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--site", help="only this site (WH-01, FAC-01)")
    ap.add_argument("--zones", help="comma-separated zone ids or kinds (production, cold_room, ...)")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
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
