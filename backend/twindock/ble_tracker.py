"""BLE tags to forklift zones.

The board scans for advertisers named TD-* every 2 s and reports their RSSI. A tag named TD-FL01
belongs to forklift FL-01. With a single gateway, RSSI only says how far a tag is from the board,
so zones are distance bands: ble_zones.json lists waypoint nodes from nearest (strongest signal)
to farthest, each with the weakest smoothed RSSI that still counts as "there". The thresholds are
measured on site with the /device calibration helper; with no zones configured nothing is tracked.

RSSI is noisy (a body or a forklift mast in the way costs 5-10 dB), so:
- each tag's RSSI is a moving average of its last `window` readings, and
- the committed zone changes only after the new zone has been the answer for `stable_s` seconds.

Pure logic with an injected clock: the engine feeds sightings and applies the results.
"""

from __future__ import annotations

import json
import os
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# TWINDOCK_BLE_ZONES points at another file, e.g. to try thresholds without touching the real one.
CONFIG_PATH = Path(os.environ.get("TWINDOCK_BLE_ZONES") or Path(__file__).resolve().parents[1] / "world" / "ble_zones.json")
TAG_RE = re.compile(r"^TD-FL(\d{2})$")


def unit_for_tag(name: str) -> str | None:
    """TD-FL01 -> FL-01. Other TD- tags are reported but not mapped to a unit."""
    m = TAG_RE.match(name)
    return f"FL-{m.group(1)}" if m else None


@dataclass(frozen=True)
class Zone:
    node: str
    min_rssi_dbm: float


@dataclass(frozen=True)
class BleConfig:
    window: int = 5
    stable_s: float = 3.0
    lost_after_s: float = 10.0
    zones: tuple[Zone, ...] = ()

    @staticmethod
    def load(path: Path = CONFIG_PATH, valid_nodes: set[str] | None = None) -> BleConfig:
        if not path.exists():
            return BleConfig()
        raw: dict[str, Any] = json.loads(path.read_text())
        zones = tuple(Zone(str(z["node"]), float(z["min_rssi_dbm"])) for z in raw.get("zones", []))
        cfg = BleConfig(window=int(raw.get("window", 5)), stable_s=float(raw.get("stable_s", 3.0)),
                        lost_after_s=float(raw.get("lost_after_s", 10.0)), zones=zones)
        cfg.check(valid_nodes)
        return cfg

    def check(self, valid_nodes: set[str] | None) -> None:
        """Fail at startup on a bad hand-edited config rather than mis-place forklifts later."""
        if self.window < 1 or self.stable_s < 0 or self.lost_after_s <= 0:
            raise ValueError("ble_zones.json: window >= 1, stable_s >= 0, lost_after_s > 0")
        for a, b in zip(self.zones, self.zones[1:]):
            if b.min_rssi_dbm >= a.min_rssi_dbm:
                raise ValueError(f"ble_zones.json: zones must go from strongest to weakest threshold "
                                 f"({a.node} {a.min_rssi_dbm} then {b.node} {b.min_rssi_dbm})")
        if valid_nodes is not None:
            for z in self.zones:
                if z.node not in valid_nodes:
                    raise ValueError(f"ble_zones.json: {z.node} is not a forklift node in layout.json")
        if len({z.node for z in self.zones}) != len(self.zones):
            raise ValueError("ble_zones.json: each node may appear once")

    def zone_for(self, rssi: float) -> str | None:
        """First (nearest) zone whose threshold the signal reaches; None = beyond every zone."""
        for z in self.zones:
            if rssi >= z.min_rssi_dbm:
                return z.node
        return None


@dataclass
class Track:
    name: str
    addr: str
    unit_id: str | None
    readings: deque[int] = field(default_factory=deque)
    last_rssi: int = 0
    last_seen_ms: int = 0
    zone: str | None = None             # committed (after hysteresis)
    has_zone: bool = False              # a zone (possibly "beyond every zone") was ever committed
    pending: str | None = None
    pending_since_ms: int | None = None

    @property
    def avg(self) -> float | None:
        return sum(self.readings) / len(self.readings) if self.readings else None


@dataclass
class ZoneChange:
    tag: str
    unit_id: str | None
    zone: str | None
    first: bool  # first commit since the tag was (re)acquired


class BleTracker:
    def __init__(self, config: BleConfig) -> None:
        self.config = config
        self.tracks: dict[str, Track] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.config.zones)

    def raw_zone(self, t: Track) -> str | None:
        avg = t.avg
        return None if avg is None else self.config.zone_for(avg)

    def update(self, sightings: list[dict[str, Any]], now_ms: int) -> list[ZoneChange]:
        """Feed one scan. Returns zone commits caused by it."""
        changes: list[ZoneChange] = []
        for s in sightings:
            name = str(s["name"])
            t = self.tracks.get(name)
            if t is None:
                t = self.tracks[name] = Track(name, str(s["addr"]), unit_for_tag(name),
                                              deque(maxlen=self.config.window))
            t.addr = str(s["addr"])
            t.readings.append(int(s["rssi_dbm"]))
            t.last_rssi, t.last_seen_ms = int(s["rssi_dbm"]), now_ms
            if not self.enabled:
                continue
            want = self.raw_zone(t)
            if t.has_zone and want == t.zone:
                t.pending, t.pending_since_ms = None, None
                continue
            if want != t.pending or t.pending_since_ms is None:
                t.pending, t.pending_since_ms = want, now_ms
            if now_ms - t.pending_since_ms >= self.config.stable_s * 1000:
                first = not t.has_zone
                t.zone, t.has_zone = want, True
                t.pending, t.pending_since_ms = None, None
                changes.append(ZoneChange(name, t.unit_id, want, first))
        return changes

    def expire(self, now_ms: int) -> list[Track]:
        """Drop tags not seen for lost_after_s. Returns the dropped tracks."""
        lost = [t for t in self.tracks.values() if now_ms - t.last_seen_ms > self.config.lost_after_s * 1000]
        for t in lost:
            del self.tracks[t.name]
        return lost

    def forget_zones(self) -> None:
        """After a world reset: units are back at their seed spots, so zones must be re-committed."""
        for t in self.tracks.values():
            t.zone, t.has_zone, t.pending, t.pending_since_ms = None, False, None, None

    def wire(self) -> dict[str, Any]:
        c = self.config
        return {
            "config": {"window": c.window, "stable_s": c.stable_s, "lost_after_s": c.lost_after_s,
                       "zones": [{"node": z.node, "min_rssi_dbm": z.min_rssi_dbm} for z in c.zones]},
            "tracks": [{
                "name": t.name, "addr": t.addr, "unit_id": t.unit_id, "last_rssi_dbm": t.last_rssi,
                "avg_rssi_dbm": None if t.avg is None else round(t.avg, 1), "readings": len(t.readings),
                "last_seen_ms": t.last_seen_ms, "raw_zone": self.raw_zone(t) if self.enabled else None,
                "zone": t.zone if t.has_zone else None, "has_zone": t.has_zone,
                "pending_zone": t.pending, "pending_since_ms": t.pending_since_ms,
            } for t in sorted(self.tracks.values(), key=lambda t: t.name)],
        }
