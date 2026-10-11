"""Auto mode also runs the campus: raw material trucks unload at the raw store, FL-05 feeds the factory, the line uses it up."""

from __future__ import annotations

import pytest
from conftest import Harness

from twindock import planner


def test_auto_mode_runs_the_raw_material_flow(h: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(planner, "line_running", lambda _w: True)  # no machine monitors here: pretend the line runs
    h.client({"type": "set_auto_mode", "cmd_id": "a", "enabled": True})
    w = h.world
    seen: set[str] = set()
    events: list[str] = []
    for _ in range(80):  # 20 minutes of 15 s chunks
        h.run(15)
        seen |= {u.state for u in w.of_kind("truck") if u.id == "TR-03"}
        events = [e["text"] for e in h.of_type("event")]
        if any("used up raw material" in t for t in events) and "docked" in seen:
            break
    t = w.entities["TR-03"]
    assert "docked" in seen, f"TR-03 never docked: {seen}"
    assert any("FL-05: pick at" in e and "Raw" in e for e in events), "FL-05 never unloaded the truck"
    assert any("used up raw material" in e for e in events), "the line never used a raw pallet"
    # nothing from the raw flow ever goes to the warehouse forklifts, and they never drive into the raw store
    assert not any(e.startswith(("FL-01", "FL-02", "FL-03", "FL-04")) and "Raw" in e for e in events)
    assert t.kind == "truck"
