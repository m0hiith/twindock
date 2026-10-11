"""Auto mode also runs the campus: raw material trucks unload at the raw store, FL-05 feeds the press infeed, and the
presses use the raw pallets up: the engine counts the blanks from their monitors' part counters (R2)."""

from __future__ import annotations

from conftest import Harness

from twindock.embedded_sim import EmbeddedSim


def test_auto_mode_runs_the_raw_material_flow(h: Harness) -> None:
    sim = EmbeddedSim(h.engine, seed=5)
    sim.sim.local_hour = lambda: 10.5  # type: ignore[method-assign]  # mid-shift A: the line runs
    sim.start()
    prod = h.engine.production
    prod.kit_blanks, prod.blanks_per_pallet = 0, 24  # small pallets so the test sees one used up within minutes
    h.client({"type": "set_auto_mode", "cmd_id": "a", "enabled": True})
    w = h.world
    seen: set[str] = set()
    events: list[str] = []
    feeds = 0
    for _ in range(4 * 60 * 25):  # up to 25 minutes
        h.clock.ms += 250
        sim.step(0.25)
        h.engine.tick(0.25)
        for o in h.engine.drain():
            if hasattr(o, "topic"):
                feeds += o.topic.endswith("/cmd/feed")
                sim.command(o.topic, o.payload)
            elif o.msg.get("type") == "event":
                events.append(o.msg["text"])
        seen |= {u.state for u in w.of_kind("truck") if u.id == "TR-03"}
        if any("used up raw pallet" in t for t in events) and "docked" in seen:
            break
    assert "docked" in seen, f"TR-03 never docked: {seen}"
    assert any("FL-05: pick at" in e and "Raw" in e for e in events), "FL-05 never unloaded the truck"
    assert feeds >= 1, "a raw pallet at the infeed was never announced to the presses"
    assert any("The presses used up raw pallet" in e for e in events), "the presses never used a raw pallet"
    # nothing from the raw flow ever goes to the warehouse forklifts, and they never drive into the raw store
    assert not any(e.startswith(("FL-01", "FL-02", "FL-03", "FL-04")) and "Raw" in e for e in events)
