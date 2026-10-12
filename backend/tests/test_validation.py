"""R7: the simulation is sane over four simulated hours (with a grid failure and a compressor trip in it)."""

from __future__ import annotations

from sim.validate import run


def test_four_hour_run_passes_every_check() -> None:
    r = run(hours=4, seed=7)
    failed = {k: v for k, v in r["checks"].items() if not v["ok"]}
    assert r["all_ok"], failed
    c = r["checks"]
    assert c["material_conservation"]["good"] > 1000
    assert c["events_have_causes"]["events"] > 1000
