"""Sites, zones and the device registry (site twin, SITE_PROMPTS.md S0).

Two kinds of device:
- GW-01, the real SiWx917 board. It is never stored here. Its entry is derived on demand from
  the GatewayStore, which only the board's own twin/gateway/* messages can change.
- Simulated devices (tools/site_sim.py) on twin/<site>/<device>/<channel>. Their payloads carry
  source "sim" (schema const), and this module rejects any site-topic message that names a
  device whose registered source is "device".

Nothing in this module can reach the gateway store, LEDs or outgoing MQTT: it has no reference
to them. test_site_isolation.py checks that from the engine side.
"""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contract import def_validator, first_error, validator
from .ble_tracker import BleTracker
from .gateway import GatewayStore

SITES_FILE = Path(__file__).resolve().parents[1] / "world" / "sites.json"

# Same rule as the board (hardware.STALE_AFTER_MS): no message for 15 s is stale. After 60 s a
# device counts as offline: long enough to ride out a simulator restart, short enough to notice.
STALE_AFTER_MS = 15_000
OFFLINE_AFTER_MS = 60_000
HISTORY_POINTS = 240  # per channel; ~4 min of 1 s readings, enough for the side-panel chart

_SITE_TOPIC = re.compile(r"^twin/([A-Z]{2,4}-[0-9]{2})/([A-Z]{2,3}-[0-9]{2})/([a-z][a-z0-9_]*)$")


def parse_site_topic(topic: str) -> tuple[str, str, str] | None:
    """twin/<site>/<device>/<channel> -> (site, device, channel). Board topics never match:
    "gateway" is not a valid site id."""
    m = _SITE_TOPIC.match(topic)
    return (m.group(1), m.group(2), m.group(3)) if m else None


def device_status(last_seen_ms: int | None, now: int, fault: str | None = None) -> str:
    if fault:
        return "fault"
    if last_seen_ms is None:
        return "offline"
    age = now - last_seen_ms
    if age <= STALE_AFTER_MS:
        return "online"
    if age <= OFFLINE_AFTER_MS:
        return "stale"
    return "offline"


def load_sites(path: Path = SITES_FILE) -> dict[str, Any]:
    cfg: dict[str, Any] = json.loads(path.read_text())
    for s in cfg["sites"]:
        err = first_error(def_validator("site"), s)
        if err:
            raise ValueError(f"sites.json site {s.get('id')}: {err}")
    seen: set[str] = set()
    zones = {z["id"] for s in cfg["sites"] for z in s["zones"]}
    for d in cfg["devices"]:
        if d["id"] in seen:
            raise ValueError(f"sites.json: duplicate device {d['id']}")
        seen.add(d["id"])
        if d["zone_id"] not in zones:
            raise ValueError(f"sites.json: device {d['id']} in unknown zone {d['zone_id']}")
    return cfg


def point_in_polygon(x: float, z: float, poly: list[list[float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            inside = not inside
        j = i
    return inside


@dataclass
class Reading:
    value: Any
    received_ms: int
    unit: str | None = None

    def wire(self) -> dict[str, Any]:
        d: dict[str, Any] = {"value": self.value, "received_ms": self.received_ms}
        if self.unit:
            d["unit"] = self.unit
        return d


@dataclass
class SimDevice:
    """State built only from the simulator's messages for one commissioned device."""
    hello: dict[str, Any] | None = None
    last_seen_ms: int | None = None
    battery_pct: float | None = None
    rssi_dbm: int | None = None
    fault: str | None = None
    x: float | None = None  # badges report their position; others stay where commissioned
    z: float | None = None
    readings: dict[str, Reading] = field(default_factory=dict)
    history: dict[str, deque[tuple[int, float]]] = field(default_factory=dict)


@dataclass
class Note:
    level: str
    text: str


class DeviceRegistry:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.sites: list[dict[str, Any]] = cfg["sites"]
        self.defs: dict[str, dict[str, Any]] = {d["id"]: d for d in cfg["devices"]}
        self.real_ids = {i for i, d in self.defs.items() if d["source"] == "device"}
        self.sim: dict[str, SimDevice] = {i: SimDevice() for i, d in self.defs.items() if d["source"] == "sim"}
        self.real_history: dict[str, dict[str, deque[tuple[int, float]]]] = {i: {} for i in self.real_ids}
        self._warned: set[tuple[str, str]] = set()
        self.zone_by_id = {z["id"]: z for s in self.sites for z in s["zones"]}
        self.layout_nodes: dict[str, tuple[float, float]] = {}  # set by the engine (real badge zones)
        self.real_tags = {d["ble_tag"]: i for i, d in self.defs.items() if d.get("ble_tag")}

    # ------------------------------------------------------------------ zones

    def zone_at(self, x: float, z: float, site_id: str | None = None) -> dict[str, Any] | None:
        """Most specific zone containing the point (a zone listed later wins: sub-zones follow)."""
        hit = None
        for s in self.sites:
            if site_id and s["id"] != site_id:
                continue
            for zn in s["zones"]:
                if point_in_polygon(x, z, zn["polygon"]):
                    hit = zn
        return hit

    # ------------------------------------------------------------------ MQTT in (sim only)

    def _warn_once(self, notes: list[Note], dev: str, key: str, text: str) -> None:
        if (dev, key) not in self._warned:
            self._warned.add((dev, key))
            notes.append(Note("warn", text))

    def on_mqtt(self, topic: str, payload: bytes, now: int) -> tuple[list[Note], str | None]:
        """Handle a twin/<site>/<device>/<channel> message. Returns (notes, changed device id)."""
        notes: list[Note] = []
        parsed = parse_site_topic(topic)
        if parsed is None:
            self._warn_once(notes, topic, "topic", f"Ignored unknown topic {topic}")
            return notes, None
        site, dev, channel = parsed
        d = self.defs.get(dev)
        if d is None:
            self._warn_once(notes, dev, "unknown", f"Dropped {topic}: {dev} is not commissioned")
            return notes, None
        if dev in self.real_ids:
            # The real board only speaks on twin/gateway/*. Anything else naming it is rejected.
            self._warn_once(notes, dev, "real", f"Dropped {topic}: {dev} is a real device, sim topics can't write it")
            return notes, None
        if d["site_id"] != site:
            self._warn_once(notes, dev, "site", f"Dropped {topic}: {dev} belongs to {d['site_id']}")
            return notes, None
        st = self.sim[dev]
        if not payload:
            if channel == "hello":  # retained hello cleared: device decommissioned on the sim side
                st.hello = None
                return notes, dev
            return notes, None
        try:
            data = json.loads(payload)
        except ValueError:
            self._warn_once(notes, dev, "json", f"Dropped {topic}: not JSON")
            return notes, None
        schema = {"hello": "mqtt/site_hello", "status": "mqtt/site_status"}.get(channel, "mqtt/site_reading")
        err = first_error(validator(schema), data)
        if err:
            self._warn_once(notes, dev, f"schema:{channel}", f"Dropped invalid {topic}: {err}")
            return notes, None
        if channel == "hello":
            if data["type"] != d["type"] or data["protocol"] != d["protocol"]:
                self._warn_once(notes, dev, "hello",
                                f"Dropped hello from {dev}: says {data['type']}/{data['protocol']}, "
                                f"commissioned as {d['type']}/{d['protocol']}")
                return notes, None
            st.hello = data
            st.last_seen_ms = now
            return notes, dev
        if st.hello is None:
            self._warn_once(notes, dev, "nohello", f"Dropped {topic}: no hello from {dev} yet")
            return notes, None
        st.last_seen_ms = now
        if channel == "status":
            st.battery_pct = data.get("battery_pct", st.battery_pct)
            st.rssi_dbm = data.get("rssi_dbm", st.rssi_dbm)
            if "fault" in data:
                st.fault = data["fault"]
            return notes, dev
        if channel not in st.hello["capabilities"]:
            self._warn_once(notes, dev, f"cap:{channel}", f"Dropped {topic}: {channel} not in {dev}'s hello")
            return notes, None
        value = data["value"]
        st.readings[channel] = Reading(value, now, data.get("unit"))
        if channel == "position" and isinstance(value, list):
            st.x, st.z = float(value[0]), float(value[1])
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            self._push(st.history, channel, now, float(value))
        elif isinstance(value, bool):
            self._push(st.history, channel, now, 1.0 if value else 0.0)
        return notes, dev

    @staticmethod
    def _push(hist: dict[str, deque[tuple[int, float]]], channel: str, now: int, v: float) -> None:
        hist.setdefault(channel, deque(maxlen=HISTORY_POINTS)).append((now, v))

    def record_real(self, dev: str, channel: str, now: int, value: float) -> None:
        """History of a real device value (board RSSI), fed by the engine from the board's status."""
        self._push(self.real_history[dev], channel, now, value)

    # ------------------------------------------------------------------ wire

    def _gw01(self, d: dict[str, Any], gw: GatewayStore, now: int) -> dict[str, Any]:
        status = gw.status.data if gw.status else {}
        readings: dict[str, Any] = {}
        if gw.status:
            for k in ("wifi_rssi_dbm", "uptime_s", "msgs_sent"):
                if k in status:
                    readings[k] = {"value": status[k], "received_ms": gw.status.received_ms}
        # Same 15 s rule as gateway.online, measured on the board's last status (replays included).
        st = device_status(gw.last_status_ms, now)
        fw = (gw.hello.data.get("fw_version") if gw.hello else None) or status.get("fw_version")
        return {**self._base(d), "x": d["x"], "z": d["z"], "battery_pct": None, "fw_version": fw,
                "rssi_dbm": status.get("wifi_rssi_dbm"), "last_seen_ms": gw.last_status_ms,
                "status": st, "fault": None, "readings": readings}

    @staticmethod
    def _base(d: dict[str, Any]) -> dict[str, Any]:  # noqa: D102
        out = {k: d[k] for k in ("id", "site_id", "zone_id", "type", "protocol", "capabilities", "source", "label")}
        if d.get("attached_to"):
            out["attached_to"] = d["attached_to"]
        return out

    def _real_badge(self, d: dict[str, Any], ble: BleTracker | None, now: int) -> dict[str, Any]:
        """A phone or tag advertising TD-BADGE-xx, seen by the REAL board's BLE scan (twin/gateway/ble).
        Everything here comes from the board's scans via the BLE tracker (same RSSI smoothing as the
        live forklifts). Without a calibrated zone its position is only "near GW-01"."""
        t = ble.tracks.get(d["ble_tag"]) if ble else None
        readings: dict[str, Any] = {}
        last = t.last_seen_ms if t else None
        if t and t.avg is not None:
            readings["rssi_dbm"] = {"value": round(t.avg, 1), "unit": "dBm", "received_ms": t.last_seen_ms}
        x, z = d["x"], d["z"]
        if t and t.zone and self.layout_nodes and t.zone in self.layout_nodes:
            x, z = self.layout_nodes[t.zone]
            readings["ble_zone"] = {"value": t.zone, "received_ms": t.last_seen_ms}
        return {**self._base(d), "x": x, "z": z, "battery_pct": None, "fw_version": None,
                "rssi_dbm": t.last_rssi if t else None, "last_seen_ms": last,
                "status": device_status(last, now), "fault": None, "readings": readings}

    def wire_device(self, dev: str, gw: GatewayStore, now: int, ble: BleTracker | None = None) -> dict[str, Any]:
        d = self.defs[dev]
        if dev in self.real_ids:
            if d.get("ble_tag"):
                return self._real_badge(d, ble, now)
            return self._gw01(d, gw, now)
        st = self.sim[dev]
        out = self._base(d)
        if st.hello:
            out["capabilities"] = list(st.hello["capabilities"])
        zone_id = d["zone_id"]
        if st.x is not None and st.z is not None:
            zn = self.zone_at(st.x, st.z, d["site_id"])
            zone_id = zn["id"] if zn else zone_id
        out.update({"zone_id": zone_id, "x": st.x if st.x is not None else d["x"],
                    "z": st.z if st.z is not None else d["z"], "battery_pct": st.battery_pct,
                    "fw_version": st.hello["fw_version"] if st.hello else None, "rssi_dbm": st.rssi_dbm,
                    "last_seen_ms": st.last_seen_ms,
                    "status": device_status(st.last_seen_ms if st.hello else None, now, st.fault),
                    "fault": st.fault, "readings": {k: r.wire() for k, r in st.readings.items()}})
        return out

    def wire(self, gw: GatewayStore, now: int, ble: BleTracker | None = None) -> list[dict[str, Any]]:
        return [self.wire_device(i, gw, now, ble) for i in self.defs]

    def history(self, dev: str, channel: str) -> list[tuple[int, float]]:
        if dev in self.real_ids:
            return list(self.real_history[dev].get(channel, ()))
        st = self.sim.get(dev)
        return list(st.history.get(channel, ())) if st else []
