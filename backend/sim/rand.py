"""Seeded randomness, only through named streams and named distributions from the params.

Every random draw in the simulation names its stream ("MM-01.failure", "BG-03.walk", ...). Each stream is its own
generator seeded from the run seed and the stream name, so adding a device or a draw in one model never changes the
dice another model sees, and a run with the same seed is the same run.
"""

from __future__ import annotations

import math
import random
import zlib
from typing import Any

from .params import Params


class Rng:
    def __init__(self, seed: int, params: Params) -> None:
        self.seed = seed
        self.p = params
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        r = self._streams.get(name)
        if r is None:
            r = self._streams[name] = random.Random((self.seed * 1_000_003) ^ zlib.crc32(name.encode()))
        return r

    def draw(self, dist_path: str, stream: str, scale: float = 1.0) -> Any:
        """One sample from the distribution parameter at dist_path. `scale` stretches a time-like distribution
        (e.g. a worn bearing shortens the time to failure: scale < 1)."""
        lf = self.p.leaf(dist_path)
        if lf.dist is None:
            raise ValueError(f"{dist_path} is not a distribution")
        a = lf.value
        r = self.stream(stream)
        if lf.dist == "weibull":
            return r.weibullvariate(float(a["scale"]) * scale, float(a["shape"]))
        if lf.dist == "exponential":
            return r.expovariate(1.0 / (float(a["mean"]) * scale))
        if lf.dist == "normal":
            return r.gauss(float(a["mean"]), float(a["sigma"]))
        if lf.dist == "lognormal":
            return r.lognormvariate(math.log(float(a["median"]) * scale), float(a["sigma_log"]))
        if lf.dist == "uniform":
            return r.uniform(float(a["low"]) * scale, float(a["high"]) * scale)
        if lf.dist == "bernoulli":
            return r.random() < float(a["p"])
        raise ValueError(lf.dist)

    def gauss(self, stream: str, sigma: float) -> float:
        """Measurement noise: zero-mean normal with the sensor's sigma (from its params)."""
        return self.stream(stream).gauss(0.0, sigma) if sigma > 0 else 0.0

    def chance(self, stream: str, p: float) -> bool:
        return self.stream(stream).random() < p
