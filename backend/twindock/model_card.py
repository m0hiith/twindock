"""GET /api/model: every simulation model, its equations in plain language, its parameters with sources, every
simulated sensor (part, period, noise, resolution, range) and every random distribution. Built from the same params
and core the simulator runs, so the page can't drift from the code.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from sim import Params, build_core  # noqa: E402
from sim.sensors import SensorSpec  # noqa: E402

SOURCE_KIND = (("datasheet:", "datasheet"), ("standard:", "standard"), ("typical industry value", "typical"), ("assumption", "assumption"))


def source_kind(src: str) -> str:
    return next(k for prefix, k in SOURCE_KIND if src.startswith(prefix))


@lru_cache(maxsize=1)
def _static(sites_json: str, layout_json: str) -> dict[str, Any]:
    cfg = json.loads(sites_json)
    params = Params.load()
    core = build_core(cfg, json.loads(layout_json), params, 0, lambda: 12.0)
    models = []
    for m in core.models:
        d = m.describe()
        d["parameters"] = [{**lf.wire(), "kind": source_kind(lf.source)} for pre in d["params"] for lf in params.under(pre) if not lf.dist]
        d["distributions"] = [{**lf.wire(), "kind": source_kind(lf.source)} for pre in d["params"] for lf in params.under(pre) if lf.dist]
        models.append(d)
    sensors = []
    by_type: dict[str, list[str]] = {}
    kit_of: dict[str, str] = {}
    for d in cfg["devices"]:
        if d["source"] == "sim":
            by_type.setdefault(d["type"], []).append(d["id"])
            kit_of.setdefault(d["type"], d.get("kit") or "")
    for t in sorted(by_type):
        if f"sensors.{t}" not in {".".join(p.split(".")[:2]) for p in params.leaves}:
            continue
        channels = []
        for ch in params.children(f"sensors.{t}"):
            spec = SensorSpec.from_params(params, t, ch)
            channels.append({"channel": ch, "unit": spec.unit, "period_s": spec.period_s, "sigma": spec.sigma,
                             "resolution": spec.resolution, "range": None if spec.lo is None else [spec.lo, spec.hi],
                             "dropout_p": spec.dropout_p, "part": spec.part, "source": spec.source, "kind": source_kind(spec.source)})
        sensors.append({"device_type": t, "kit": kit_of[t], "devices": by_type[t], "channels": channels})
    counts: dict[str, int] = {}
    for lf in params.leaves.values():
        k = source_kind(lf.source)
        counts[k] = counts.get(k, 0) + 1
    return {"models": models, "sensors": sensors, "counts": {"parameters": len(params.leaves), "by_source": counts},
            "core": [{**lf.wire(), "kind": source_kind(lf.source)} for lf in params.under("core")],
            "devices": [{**lf.wire(), "kind": source_kind(lf.source)} for lf in params.under("devices")]}


def model_card(sites_cfg: dict[str, Any], layout: dict[str, Any], running: Any | None) -> dict[str, Any]:
    """`running` is the backend's EmbeddedSim (or None when the simulator is an external process)."""
    out = dict(_static(json.dumps(sites_cfg, sort_keys=True), json.dumps(layout, sort_keys=True)))
    if running is None:
        out["run"] = {"mode": "external", "seed": None, "t_s": None, "recent_events": []}
    else:
        core = running.sim.core
        out["run"] = {"mode": "embedded", "seed": core.seed, "t_s": round(core.t, 1),
                      "recent_events": [e.wire() for e in list(core.log)[-40:]][::-1]}
    return out
