"""R0: the simulation core. Parameters with sources, no magic numbers, seeded named randomness, the measurement layer,
and causes on every event."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

from sim import Params
from sim.params import SOURCE_KINDS, ParamError
from sim.rand import Rng
from sim.sensors import Sensor, SensorSpec

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SITES, SiteSim, select_devices  # noqa: E402

SIM = Path(__file__).resolve().parents[1] / "sim"
CFG = json.loads(SITES.read_text())
# Numbers that are arithmetic, not model parameters: 0, 1, 2 (halves, √ via **0.5), unit conversions (60 s, 3600 s,
# 1000 W, 100 %, 24 h a day), and tiny tolerances for float comparisons.
ALLOWED = {0, 1, 2, 3, 0.5, 24, 60, 100, 1000, 3600, 1e-9, 1e-6}


def test_every_parameter_has_a_value_unit_and_source() -> None:
    p = Params.load()
    assert len(p.leaves) > 150
    for lf in p.leaves.values():
        assert lf.source.startswith(SOURCE_KINDS), lf
        assert lf.unit, lf
        assert len(lf.source) > len("assumption"), f"{lf.path}: say why, not just the kind of source"


def test_a_parameter_without_a_source_is_rejected() -> None:
    with pytest.raises(ParamError):
        Params({"x": {"y": {"value": 1, "unit": "s", "source": "because"}}})
    with pytest.raises(ParamError):
        Params({"x": {"value": 1, "unit": "s"}})


def test_no_magic_numbers_in_the_models() -> None:
    """Every model number comes from params; the code only holds arithmetic constants."""
    files = [*sorted((SIM / "models").glob("*.py")), SIM / "devices.py", SIM / "sensors.py", SIM / "core.py"]
    bad = []
    for f in files:
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                if node.value not in ALLOWED:
                    bad.append(f"{f.name}:{node.lineno} {node.value}")
    assert not bad, "numbers that belong in backend/sim/params:\n" + "\n".join(bad)


def run(devices: list[dict], seed: int, seconds: float = 120) -> list[tuple[str, str, object]]:
    s = SiteSim(CFG, devices, seed=seed)
    s.verbose = False
    out: list[tuple[str, str, object]] = []
    s.publish = lambda m, ch, p, retain=False: out.append((m.id, ch, p.get("value", p.get("rssi_dbm"))))  # type: ignore[method-assign]
    for _ in range(round(seconds / 0.25)):
        s.step(0.25)
    return out


def test_same_seed_same_run_other_seed_other_run() -> None:
    devs = select_devices(CFG, "FAC-01", None)
    assert run(devs, 5) == run(devs, 5)
    assert run(devs, 5) != run(devs, 6)


def test_streams_are_independent_of_which_devices_publish() -> None:
    """Adding devices never changes the dice another device sees: each draw has its own named stream."""
    mm = [d for d in CFG["devices"] if d["id"] == "MM-01"]
    more = mm + [d for d in CFG["devices"] if d["id"] in ("CP-01", "EN-04", "BG-02")]
    alone = [r for r in run(mm, 9) if r[0] == "MM-01"]
    with_others = [r for r in run(more, 9) if r[0] == "MM-01"]
    assert alone == with_others


def test_sensor_noise_resolution_range_and_dropout() -> None:
    p = Params.load()
    rng = Rng(1, p)
    spec = SensorSpec("x", "bar", 2.0, 0.05, 0.01, 0.0, 10.0, 0.0, "test", "assumption: test")
    s = Sensor(spec, rng, "t")
    reads = [s.read(7.0) for _ in range(2000)]
    assert all(r is not None and abs(r * 100 - round(r * 100)) < 1e-9 for r in reads)  # 0.01 resolution
    mean = sum(r for r in reads if r is not None) / len(reads)
    sd = (sum((r - mean) ** 2 for r in reads if r is not None) / len(reads)) ** 0.5
    assert abs(mean - 7.0) < 0.01 and 0.04 < sd < 0.06
    assert s.read(42.0) == 10.0 and s.clipped == 1  # clipped to what the part can report
    drop = Sensor(SensorSpec("x", None, 1.0, 0, 0, None, None, 0.5, "", ""), rng, "d")
    lost = sum(drop.read(1.0) is None for _ in range(2000))
    assert 850 < lost < 1150
    due = [t / 4 for t in range(41) if s.due(t / 4)]
    assert len(due) == 5 and all(abs((b - a) - 2.0) < 1e-9 for a, b in zip(due, due[1:]))  # every period_s


def test_every_event_has_a_cause() -> None:
    s = SiteSim(CFG, select_devices(CFG, None, None), seed=4)
    s.verbose = False
    s.publish = lambda *a, **k: None  # type: ignore[method-assign]
    s.command("CP-01", "fault")
    s.command("PM-04", "grid_failure")
    for _ in range(4 * 300):
        s.step(0.25)
    log = list(s.core.log)
    assert len(log) > 20
    assert all(e.cause and e.name for e in log)
    names = " ".join(e.name for e in log)
    assert "generator running" in names and "CP-01 fault" in names


def test_model_descriptions_are_complete() -> None:
    s = SiteSim(CFG, [], seed=1)
    for d in s.core.describe():
        assert d["title"] and d["equations"], d["key"]


def test_backend_and_simulator_agree_on_ideal_cycle_times() -> None:
    """OEE's ideal cycle (what the plant configures, sites.json) is the machine's real ideal cycle (sim params)."""
    p = Params.load()
    for mid, ideal in CFG["production"]["ideal_cycle_s"].items():
        assert p.f(f"production.machines.{mid}.ideal_cycle_s") == ideal, mid
