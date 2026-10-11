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
from .models.production import Production
from .models.utilities import CampusLoads, CompressedAir, Electrical, Tanks
from .models.vehicles import DockBays, Telematics
from .params import Params

__all__ = ["Params", "SimCore", "build_core"]


def build_core(cfg: dict[str, Any], layout: dict[str, Any], params: Params, seed: int,
               hour_of_day: Callable[[], float]) -> SimCore:
    """The whole campus's true state, in dependency order: events and flags first, then the things that consume
    (machines, people, vehicles, other loads), then the supplies that react to consumption (air, power, tanks), then
    the rooms and effluent that react to everything else."""
    core = SimCore(params, seed, hour_of_day)
    nodes = {n["id"]: n for n in layout["nodes"]}
    line = (layout.get("production_line") or {}).get("machines", [])
    for m in (Doors(cfg), Occupancy(cfg), FirePanels(cfg), Gas(cfg), Leaks(cfg), AssetTags(cfg), Helmets(cfg),
              People(cfg, nodes), Production(cfg, line), Telematics(cfg), DockBays(cfg), CampusLoads(cfg),
              CompressedAir(cfg), Electrical(cfg), Tanks(cfg), Rooms(cfg), WaterQuality(cfg)):
        core.add(m)
    return core
