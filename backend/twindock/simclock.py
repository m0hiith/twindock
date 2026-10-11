"""The simulation clock: one time base for the engine, the embedded simulator and everything they timestamp.

At speed 1 it runs at real time. It starts `warm_start_s` in the past and the warm start fast-forwards it
to "now" before the backend serves (D3), so a freshly started (or woken) host shows a factory that has been
running for a while. At ×5 or ×20 it runs ahead of the wall clock; every server message carries its time
(`server_ts_ms`), and the UI measures ages on that clock, so "12s ago" stays true in simulated seconds.

The real board never runs on fast time: speeds other than 1 are refused while it is online (engine.py).
"""

from __future__ import annotations

import time
import zlib
from dataclasses import dataclass, field

SPEEDS = (1, 5, 20)
BASE_SEED = 917  # fixed part of the warm start's seed (SiWx917); the date makes each day different


def day_seed(day: str) -> int:
    """Fixed seed plus the date: every restart on the same day replays the same warm start, other days differ."""
    return BASE_SEED * 100_000 + zlib.crc32(day.encode()) % 100_000


@dataclass
class SimClock:
    sim_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    speed: int = 1

    def __call__(self) -> int:
        return self.sim_ms

    def advance(self, dt_s: float) -> None:
        self.sim_ms += int(round(dt_s * 1000))

    def hour(self) -> float:
        """Local hour of day on the simulation clock (solar, shifts, tariffs)."""
        lt = time.localtime(self.sim_ms / 1000)
        return lt.tm_hour + lt.tm_min / 60 + lt.tm_sec / 3600

    def wire(self) -> dict[str, int]:
        return {"sim_ms": self.sim_ms, "speed": self.speed}
