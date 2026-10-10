"""FAC-01 production analytics, built only from the machine monitors' (simulated) readings.

- Vibration baseline: each machine learns its own mean and spread of vibration RMS while it is
  running, over the first `baseline_s` seconds (and at least `baseline_min_samples` readings).
  After that, the rolling mean of the last `window_samples` running readings is compared with
  the baseline: z = (rolling mean - baseline mean) / baseline std. Above `z_threshold` the
  machine is flagged "abnormal vibration compared with baseline"; it clears below `z_clear`
  (hysteresis, so it doesn't flicker). It is a comparison with the machine's own normal, never
  a failure prediction.
- OEE (per machine): availability = running time / planned time (planned = time with data,
  excluding maintenance); performance = ideal cycle time x units made / running time;
  quality = good units / all units. OEE = A x P x Q.
- Zone OEE: mean availability x mean performance x product of qualities (a reject at any
  machine is lost).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

MACHINE_STATES = ("running", "idle", "fault", "maintenance")


@dataclass
class Welford:
    """Running mean and standard deviation without storing samples."""
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, x: float) -> None:
        self.n += 1
        d = x - self.mean
        self.mean += d / self.n
        self.m2 += d * (x - self.mean)

    @property
    def std(self) -> float:
        return math.sqrt(self.m2 / (self.n - 1)) if self.n > 1 else 0.0


@dataclass
class Baseline:
    """Per-machine vibration baseline and rolling z-score (see module doc)."""
    baseline_s: float
    min_samples: int
    window: int
    z_threshold: float
    z_clear: float
    stats: Welford = field(default_factory=Welford)
    learn_started_ms: int | None = None
    learned: bool = False
    recent: deque[float] = field(default_factory=deque)
    z: float | None = None
    abnormal: bool = False

    def add(self, v: float, now: int) -> str | None:
        """Add a running-state reading. Returns "raised", "cleared" or None."""
        if not self.learned:
            if self.learn_started_ms is None:
                self.learn_started_ms = now
            self.stats.add(v)
            if self.stats.n >= self.min_samples and now - self.learn_started_ms >= self.baseline_s * 1000:
                self.learned = True
            return None
        self.recent.append(v)
        while len(self.recent) > self.window:
            self.recent.popleft()
        if len(self.recent) < self.window:
            return None
        sd = max(self.stats.std, 1e-6)
        self.z = (sum(self.recent) / len(self.recent) - self.stats.mean) / sd
        if not self.abnormal and self.z > self.z_threshold:
            self.abnormal = True
            return "raised"
        if self.abnormal and self.z < self.z_clear:
            self.abnormal = False
            return "cleared"
        return None


def oee(running_ms: float, planned_ms: float, ideal_cycle_s: float, good: int, rejects: int) -> dict[str, float | None]:
    """A, P, Q and OEE as fractions (None until there is enough data to say)."""
    total = good + rejects
    a = running_ms / planned_ms if planned_ms > 0 else None
    p = min(1.0, ideal_cycle_s * total / (running_ms / 1000)) if running_ms > 0 else None
    q = good / total if total > 0 else None
    o = a * p * q if a is not None and p is not None and q is not None else None
    return {"availability": a, "performance": p, "quality": q, "oee": o}


@dataclass
class Machine:
    id: str
    device_id: str
    label: str
    ideal_cycle_s: float
    base: Baseline
    state: str = "no_data"
    state_since_ms: int | None = None
    running_ms: float = 0.0
    planned_ms: float = 0.0
    good: int = 0
    rejects: int = 0
    units_offset: int | None = None  # the monitor's counter at our first reading (simulator restarts)
    cycle_time_s: float | None = None
    current_a: float | None = None
    vibration_rms: float | None = None
    data_ms: int | None = None
    last_fault: dict[str, Any] | None = None
    pending_alarm: str | None = None


class Production:
    def __init__(self, cfg: dict[str, Any], machines: list[dict[str, Any]], devices: list[dict[str, Any]]) -> None:
        self.cfg = cfg
        by_unit = {d.get("attached_to"): d["id"] for d in devices if d["type"] == "machine_monitor"}
        self.machines: dict[str, Machine] = {}
        for m in machines:
            dev = by_unit.get(m["id"])
            if dev is None:
                continue
            self.machines[m["id"]] = Machine(
                m["id"], dev, m["label"], float(cfg["ideal_cycle_s"][m["id"]]),
                Baseline(cfg["baseline_s"], cfg["baseline_min_samples"], cfg["window_samples"],
                         cfg["z_threshold"], cfg["z_clear"]))
        self.by_device = {m.device_id: m for m in self.machines.values()}
        self.units_per_pallet = int(cfg["units_per_pallet"])
        self.finished_by = cfg["finished_by"]
        self.outbound_node = cfg["outbound_node"]
        self.units_toward_pallet = 0
        self.pallets_waiting = 0   # full pallets the line made that found no free outbound spot
        self.pallets_made = 0
        self._last_tick_ms: int | None = None

    # ------------------------------------------------------------------ readings

    def on_reading(self, device_id: str, channel: str, value: Any, now: int) -> list[tuple[str, str, str]]:
        """Update machine state from one reading. Alerts and their events come from the rules engine
        (backend/rules/production.yaml); this returns no events itself."""
        m = self.by_device.get(device_id)
        if m is None:
            return []
        ev: list[tuple[str, str, str]] = []
        m.data_ms = now
        if channel == "state" and isinstance(value, str) and value in MACHINE_STATES and value != m.state:
            prev = m.state
            m.state, m.state_since_ms = value, now
            if value == "fault":
                m.last_fault = {"text": m.pending_alarm or "Fault", "at_ms": now}
            del prev  # transitions are turned into alerts by the rules engine (machine_fault)
            m.pending_alarm = None
        elif channel == "alarm" and isinstance(value, str):
            if m.state == "fault" and m.last_fault:
                m.last_fault["text"] = value
            else:
                m.pending_alarm = value
        elif channel == "vibration_rms" and isinstance(value, (int, float)):
            m.vibration_rms = float(value)
            if m.state == "running":
                m.base.add(float(value), now)  # sets abnormal; the abnormal_vibration rule raises the alert
        elif channel == "current_a" and isinstance(value, (int, float)):
            m.current_a = float(value)
        elif channel == "cycle_time_s" and isinstance(value, (int, float)):
            m.cycle_time_s = float(value)
        elif channel in ("units", "rejects") and isinstance(value, int) and not isinstance(value, bool):
            if channel == "units":
                if m.units_offset is None or value < m.units_offset:
                    m.units_offset = value - m.good  # first reading, or the simulator restarted
                new = value - m.units_offset
                made = max(0, new - m.good)
                m.good = new
                if m.id == self.finished_by and made:
                    self.units_toward_pallet += made
                    while self.units_toward_pallet >= self.units_per_pallet:
                        self.units_toward_pallet -= self.units_per_pallet
                        self.pallets_waiting += 1
            else:
                m.rejects = max(m.rejects, value)
        return ev

    def tick(self, now: int, fresh: dict[str, bool]) -> None:
        """Account running/planned time. fresh[device] says whether that monitor is online:
        time without data counts as neither running nor planned (we don't know)."""
        last = self._last_tick_ms
        self._last_tick_ms = now
        if last is None:
            return
        dt = now - last
        for m in self.machines.values():
            if not fresh.get(m.device_id) or m.state in ("no_data", "maintenance"):
                continue
            m.planned_ms += dt
            if m.state == "running":
                m.running_ms += dt

    def machine_state(self, machine_id: str, fresh: bool) -> str:
        m = self.machines[machine_id]
        return m.state if fresh else "no_data"

    # ------------------------------------------------------------------ wire

    def zone_oee(self) -> dict[str, float | None]:
        ms = [oee(m.running_ms, m.planned_ms, m.ideal_cycle_s, m.good, m.rejects) for m in self.machines.values()]
        av = [x["availability"] for x in ms if x["availability"] is not None]
        pf = [x["performance"] for x in ms if x["performance"] is not None]
        qs = [x["quality"] for x in ms if x["quality"] is not None]
        a = sum(av) / len(av) if av else None
        p = sum(pf) / len(pf) if pf else None
        q = math.prod(qs) if qs else None
        return {"availability": a, "performance": p, "quality": q,
                "oee": a * p * q if a is not None and p is not None and q is not None else None}

    def wire(self, fresh: dict[str, bool]) -> dict[str, Any]:
        def r(x: float | None, n: int = 4) -> float | None:
            return None if x is None else round(x, n)
        machines = []
        for m in self.machines.values():
            o = oee(m.running_ms, m.planned_ms, m.ideal_cycle_s, m.good, m.rejects)
            b = m.base
            machines.append({
                "id": m.id, "device_id": m.device_id, "label": m.label,
                "state": m.state if fresh.get(m.device_id) else "no_data",
                "state_since_ms": m.state_since_ms, "data_ms": m.data_ms,
                "cycle_time_s": m.cycle_time_s, "ideal_cycle_s": m.ideal_cycle_s,
                "current_a": m.current_a, "vibration_rms": m.vibration_rms,
                "baseline": {"learned": b.learned, "samples": b.stats.n, "mean": r(b.stats.mean) if b.stats.n else None,
                             "std": r(b.stats.std) if b.stats.n > 1 else None},
                "z": r(b.z, 2), "abnormal": b.abnormal,
                "units_today": m.good, "rejects_today": m.rejects, "last_fault": m.last_fault,
                **{k: r(v) for k, v in o.items()},
            })
        z = self.zone_oee()
        fin = self.machines.get(self.finished_by)
        return {
            "machines": machines,
            "line": {"units_today": fin.good if fin else 0, "pallets_made": self.pallets_made,
                     "pallets_waiting": self.pallets_waiting,
                     "units_toward_pallet": self.units_toward_pallet, **{k: r(v) for k, v in z.items()}},
            "config": {"z_threshold": self.cfg["z_threshold"], "z_clear": self.cfg["z_clear"],
                       "baseline_s": self.cfg["baseline_s"], "window_samples": self.cfg["window_samples"],
                       "units_per_pallet": self.units_per_pallet},
        }
