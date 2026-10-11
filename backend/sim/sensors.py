"""The measurement layer: models hold the true state, sensors read it the way the real part in the kit would.

A sensor spec (params/sensors.yaml) gives, for one channel of one device type:

    period_s     how often the device samples and publishes (its firmware's report interval)
    sigma        measurement noise, one standard deviation, in the channel's unit
    resolution   the smallest step the part reports (an ADC LSB, a register's resolution)
    range        [min, max] the part can physically report; a true value outside it is clipped (and flagged)
    dropout_p    chance that one sample is lost (bus error, radio retry gave up)
    part         the real part this channel stands for

Noise, rounding and clipping happen here and nowhere else. A reading is always:
clip(round_to_resolution(true + noise)).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .params import Params
from .rand import Rng


@dataclass(frozen=True)
class SensorSpec:
    channel: str
    unit: str | None
    period_s: float
    sigma: float
    resolution: float
    lo: float | None
    hi: float | None
    dropout_p: float
    part: str
    source: str

    @classmethod
    def from_params(cls, p: Params, device_type: str, channel: str) -> "SensorSpec":
        lf = p.leaf(f"sensors.{device_type}.{channel}")
        v = lf.value
        rng = v.get("range")
        return cls(channel, None if lf.unit in ("", "1", "-") else lf.unit, float(v["period_s"]), float(v.get("sigma", 0.0)),
                   float(v.get("resolution", 0.0)), None if rng is None else float(rng[0]), None if rng is None else float(rng[1]),
                   float(v.get("dropout_p", 0.0)), str(v.get("part", "")), lf.source)


class Sensor:
    """One sampled channel. `due(t)` says when the next sample is taken; `read(true)` turns the true value into
    the number the device publishes (or None when the sample is lost)."""

    def __init__(self, spec: SensorSpec, rng: Rng, stream: str) -> None:
        self.spec = spec
        self.rng = rng
        self.stream = stream
        # Devices boot at different moments, so their sample clocks are spread over one period.
        self.next_t = rng.stream(stream + ".phase").uniform(0.0, spec.period_s)
        self.clipped = 0

    def due(self, t: float) -> bool:
        if t + 1e-9 < self.next_t:
            return False
        self.next_t += self.spec.period_s
        if self.next_t <= t:  # we fell behind (a long step): resynchronise, never burst
            self.next_t = t + self.spec.period_s
        return True

    def force(self, t: float) -> None:
        """Sample again now (an event the firmware reports immediately, e.g. a door contact)."""
        self.next_t = t

    def read(self, true: float) -> float | None:
        s = self.spec
        if s.dropout_p and self.rng.chance(self.stream + ".dropout", s.dropout_p):
            return None
        x = true + self.rng.gauss(self.stream, s.sigma)
        if s.lo is not None and x < s.lo:
            x = s.lo
            self.clipped += 1
        if s.hi is not None and x > s.hi:
            x = s.hi
            self.clipped += 1
        if s.resolution > 0:
            x = round(x / s.resolution) * s.resolution
            decimals = max(0, -int(math.floor(math.log10(s.resolution))))
            x = round(x, decimals)
        return x

    def wire(self) -> dict[str, Any]:
        s = self.spec
        return {"channel": s.channel, "unit": s.unit, "period_s": s.period_s, "sigma": s.sigma, "resolution": s.resolution,
                "range": None if s.lo is None else [s.lo, s.hi], "dropout_p": s.dropout_p, "part": s.part, "source": s.source}
