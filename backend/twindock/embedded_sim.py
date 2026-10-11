"""The site simulator (tools/site_sim.py) running inside the backend, for deploys without a broker.

Locally the simulator is its own process talking to Mosquitto. A hosted deploy (the container) has no broker, so every
SIM device would stay "never seen". In embedded mode the same SiteSim runs in the backend's event loop: its
messages go straight to `Engine.on_mqtt` on the same twin/<site>/<device>/<channel> topics (so they pass the
same schema checks and land in the device registry, never in the board's state), and the engine's site commands
go straight back to it. Only sim devices are simulated; GW-01 is never touched, so the board still shows
"Waiting for device" until a real board publishes.
"""

from __future__ import annotations

import json
import logging
import socket
import sys
from pathlib import Path
from typing import Any

from .engine import Engine

log = logging.getLogger("twindock.sim")

_SIM_DIRS = (Path(__file__).resolve().parents[2] / "tools",)  # the repo's tools/, also copied into the container

STEP_S = 0.25  # same period as the standalone simulator


def broker_reachable(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _import_site_sim() -> Any:
    for d in _SIM_DIRS:
        if (d / "site_sim.py").is_file():
            if str(d) not in sys.path:
                sys.path.insert(0, str(d))
            import site_sim  # type: ignore[import-not-found]
            return site_sim
    raise RuntimeError("tools/site_sim.py not found")


class EmbeddedSim:
    def __init__(self, engine: Engine, seed: int | None = None) -> None:
        ss = _import_site_sim()
        self.engine = engine
        cfg = engine.devices.cfg
        self.sim = ss.SiteSim(cfg, ss.select_devices(cfg, None, None), seed)
        self.sim.verbose = False
        self.sim.sink = self._deliver

    def _deliver(self, topic: str, payload: bytes, retain: bool) -> None:
        assert not topic.startswith("twin/gateway/"), "the embedded simulator never speaks for the board"
        self.engine.on_mqtt(topic, payload, retain)

    def start(self) -> None:
        self.engine.sim_attached = True
        self.sim.hellos()
        log.info("embedded site simulator: %d SIM devices, no broker needed", len(self.sim.models))

    def step(self, dt: float) -> None:
        self.sim.step(dt)

    def command(self, topic: str, payload: dict[str, Any]) -> bool:
        """Engine output for a sim device (twin/<site>/<device>/cmd/<action>); False if it isn't one."""
        if topic.startswith("twin/gateway/") or "/cmd/" not in topic:
            return False
        self.sim.on_command(topic, json.dumps(payload).encode())
        return True
