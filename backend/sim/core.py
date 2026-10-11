"""The simulation core: one clock, continuous models on a fixed step, discrete events on a queue.

    core = SimCore(params, seed, hour_of_day)
    core.add(model)            # in dependency order: a model reads what earlier models wrote this step
    core.advance(seconds)      # runs whole fixed steps (params core.dt_s); events fire at their time

Models couple only through physical quantities on the bus (`core.q`): electrical load in kW per consumer,
compressed-air demand in Nm³/min per consumer, heat, material counts, people. A model reads the bus, updates its own
true state and writes its outputs. Discrete things (a cycle completes, a bearing fails, a truck arrives, a shift
changes) are events scheduled on the queue, each with the cause that scheduled it, and every event that happens is
logged with that cause, so "why did this happen" always has an answer (R7 checks no event lacks a cause).
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

from .params import Params
from .rand import Rng


@dataclass
class Quantities:
    """The bus. Every value is a true physical quantity at the current step; sensors read these."""
    power_kw: dict[str, float] = field(default_factory=dict)        # consumer -> electrical load (kW)
    power_zone: dict[str, str] = field(default_factory=dict)        # consumer -> zone it is wired in
    air_demand_nm3_min: dict[str, float] = field(default_factory=dict)  # consumer -> compressed air (Nm³/min)
    heat_kw: dict[str, float] = field(default_factory=dict)         # zone -> heat released into the room (kW)
    people_in_zone: dict[str, int] = field(default_factory=dict)    # zone -> people there now
    zone_powered: dict[str, bool] = field(default_factory=dict)     # zone -> has mains power (grid or generator)
    air_pressure_bar: float = 0.0                                   # header pressure seen by the machines (bar g)
    flags: dict[str, Any] = field(default_factory=dict)             # named states other models may read (fire_alarm, ...)

    def powered(self, zone: str) -> bool:
        return self.zone_powered.get(zone, True)


@dataclass(order=True)
class _Queued:
    at: float
    seq: int
    name: str = field(compare=False)
    cause: str = field(compare=False)
    fn: Callable[[], None] = field(compare=False)
    cancelled: bool = field(default=False, compare=False)


@dataclass
class LoggedEvent:
    t: float
    name: str
    cause: str
    detail: str = ""

    def wire(self) -> dict[str, Any]:
        return {"t": round(self.t, 3), "name": self.name, "cause": self.cause, "detail": self.detail}


class Model:
    """Base for every true-state model. Subclasses set `key` and `title`, and describe themselves for /model."""
    key = "model"
    title = "Model"
    equations: tuple[str, ...] = ()       # plain-language equations, shown on /model
    reads: tuple[str, ...] = ()           # bus quantities it reads
    writes: tuple[str, ...] = ()          # bus quantities it writes
    params_prefix: tuple[str, ...] = ()   # parameter groups it uses

    def bind(self, core: "SimCore") -> None:
        self.core = core

    def step(self, dt: float) -> None:
        pass

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        """A simulator command addressed to something this model owns. True if handled."""
        return False

    def describe(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "equations": list(self.equations), "reads": list(self.reads),
                "writes": list(self.writes), "params": list(self.params_prefix)}


class SimCore:
    def __init__(self, params: Params, seed: int, hour_of_day: Callable[[], float]) -> None:
        self.p = params
        self.seed = seed
        self.rng = Rng(seed, params)
        self.dt = params.f("core.dt_s")
        self.t = 0.0                      # simulated seconds since the core started
        self._acc = 0.0
        self.hour_of_day = hour_of_day    # local hour on the simulation clock (solar, shifts, tariffs)
        self.q = Quantities()
        self.models: list[Model] = []
        self.by_key: dict[str, Model] = {}
        self._queue: list[_Queued] = []
        self._seq = 0
        self.log: deque[LoggedEvent] = deque(maxlen=int(params.v("core.event_log_max")))
        self.listeners: list[Callable[[LoggedEvent], None]] = []

    def add(self, model: Model) -> Model:
        model.bind(self)
        self.models.append(model)
        self.by_key[model.key] = model
        return model

    def get(self, key: str) -> Any:
        return self.by_key[key]

    # ------------------------------------------------------------------ events

    def schedule(self, delay_s: float, name: str, cause: str, fn: Callable[[], None]) -> _Queued:
        """Run fn after delay_s simulated seconds. `cause` is recorded with the event when it fires."""
        self._seq += 1
        item = _Queued(self.t + max(0.0, delay_s), self._seq, name, cause, fn)
        heapq.heappush(self._queue, item)
        return item

    def cancel(self, item: _Queued | None) -> None:
        if item is not None:
            item.cancelled = True

    def record(self, name: str, cause: str, detail: str = "") -> LoggedEvent:
        """Log something that happened inside a continuous model (a threshold crossed, a state change)."""
        ev = LoggedEvent(self.t, name, cause, detail)
        self.log.append(ev)
        for f in self.listeners:
            f(ev)
        return ev

    def _fire_due(self) -> None:
        while self._queue and self._queue[0].at <= self.t + 1e-9:
            item = heapq.heappop(self._queue)
            if item.cancelled:
                continue
            item.fn()
            self.record(item.name, item.cause)

    # ------------------------------------------------------------------ time

    def advance(self, seconds: float) -> int:
        """Advance by whole fixed steps; a remainder carries over. Returns the number of steps run."""
        self._acc += seconds
        n = 0
        while self._acc >= self.dt - 1e-9:
            self._acc -= self.dt
            self.t += self.dt
            self._fire_due()
            for m in self.models:
                m.step(self.dt)
            n += 1
        return n

    def command(self, target: str, action: str, data: dict[str, Any]) -> bool:
        for m in self.models:
            if m.command(target, action, data):
                return True
        return False

    def describe(self) -> list[dict[str, Any]]:
        return [m.describe() for m in self.models]
