"""TwinDock's simulation core (REALISM_DEPLOY_PROMPTS.md R0), shared by tools/site_sim.py (standalone, through a
broker) and backend/twindock/embedded_sim.py (inside the backend).

    from sim import build_core, Params
    core = build_core(sites_cfg, layout_json, Params.load(), seed, hour_of_day)

docs/sim_architecture.md explains the design; /model lists every model, its equations and its parameters.
"""

from __future__ import annotations

from typing import Any, Callable

from .core import SimCore
from .models.environment import AssetTags, Doors, FirePanels, Gas, Helmets, Leaks, Occupancy, Rooms, WaterQuality
from .models.people import People
from .models.production import Production, Shifts
from .models.utilities import CampusLoads, CompressedAir, Electrical, Water, Weather
from .models.vehicles import DockBays, Telematics
from .params import Params

__all__ = ["Params", "SimCore", "build_core"]


def build_core(cfg: dict[str, Any], layout: dict[str, Any], params: Params, seed: int,
               hour_of_day: Callable[[], float]) -> SimCore:
    """The whole campus's true state, in dependency order: weather, events and flags first, then the things that
    consume (machines, people, vehicles, rooms, other loads), then the supplies that react to consumption (air, water,
    power), then the effluent that reacts to everything else."""
    core = SimCore(params, seed, hour_of_day)
    line = (layout.get("production_line") or {}).get("machines", [])
    for m in (Weather(), Shifts(), Doors(cfg), Occupancy(cfg), FirePanels(cfg), Gas(cfg), Leaks(cfg), AssetTags(cfg), Helmets(cfg),
              People(cfg, layout), Production(cfg, line), Telematics(cfg), DockBays(cfg), CampusLoads(cfg),
              Rooms(cfg), CompressedAir(cfg), Water(cfg), Electrical(cfg), WaterQuality(cfg)):
        core.add(m)
    return core
