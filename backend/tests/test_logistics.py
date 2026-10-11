"""R3: logistics. Weighbridge tickets match the cargo, inventory never goes negative, forklift batteries balance in
amp-hours, trucks follow their schedule through gate, weighbridge, queue, dock and paperwork, orders ship with an
on-time KPI, the reorder point calls the supplier, and forklifts top up in breaks.

One three-hour auto-mode run is shared by the observation tests (it is the expensive part)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from conftest import Harness

from twindock.world import PACE, logistics_params, pallet_kg


def auto(h: Harness, hour: float = 10.5) -> None:
    h.engine._hour = lambda: hour  # type: ignore[method-assign]  # mid-shift A unless a test says otherwise
    h.client({"type": "set_auto_mode", "cmd_id": "a", "enabled": True})


@dataclass
class Run:
    h: Harness
    tickets: list[tuple[dict[str, Any], list[str]]] = field(default_factory=list)
    stages: dict[str, list[str]] = field(default_factory=dict)
    inventory_ok: bool = True
    pallets_match: bool = True
    battery_start: dict[str, float] = field(default_factory=dict)


@pytest.fixture(scope="module")
def run3h() -> Run:
    h = Harness()
    auto(h)
    w, lg = h.world, h.engine.logistics
    r = Run(h, battery_start={f.id: f.battery or 0.0 for f in w.of_kind("forklift")})
    for i in range(6):  # finished pallets from the line wait in the warehouse for orders
        assert w.spawn_pallet("ZONE_B", {"sku": f"FG-{i:04d}"}) is not None
    lg.next_order_t = w.time  # an order straight away
    real = lg._ticket

    def spy(t, direction, kg, now):  # type: ignore[no-untyped-def]
        r.tickets.append(({"truck": t.id, "direction": direction, "kg": kg}, list(t.cargo or [])))
        real(t, direction, kg, now)
    lg._ticket = spy  # type: ignore[method-assign]
    for _ in range(int(3 * 3600 / PACE / 10)):
        h.run(10, dt=0.5)
        for tid, v in lg.visits.items():
            seq = r.stages.setdefault(tid, [])
            if not seq or seq[-1] != v.stage:
                seq.append(v.stage)
        inv = lg.inventory()
        r.inventory_ok &= all(n >= 0 for g in inv.values() for n in g.values())
        r.pallets_match &= sum(n for g in inv.values() for n in g.values()) == len(w.of_kind("pallet"))
    return r


def test_weighbridge_tickets_match_the_cargo(run3h: Run) -> None:
    assert {"in", "out"} <= {s["direction"] for s, _ in run3h.tickets}
    tare = logistics_params().v("logistics.trucks.tare_kg")
    w = run3h.h.world
    kg = logistics_params().v("logistics.pallets.kg")
    for s, cargo in run3h.tickets:
        # pallets delivered since (finished goods) have left the world: weigh them by their SKU group
        expect = tare[s["truck"]] + sum(pallet_kg(w.entities[p]) if p in w.entities else float(kg["FG-"]) for p in cargo)
        assert abs(s["kg"] - expect) < 1e-6, (s, cargo)


def test_inventory_never_goes_negative_and_every_pallet_is_somewhere(run3h: Run) -> None:
    assert run3h.inventory_ok and run3h.pallets_match


def test_battery_amp_hours_balance(run3h: Run) -> None:
    cap = logistics_params().f("logistics.forklift.capacity_ah")
    fls = run3h.h.world.of_kind("forklift")
    for f in fls:
        lost_ah = (run3h.battery_start[f.id] - (f.battery or 0.0)) / 100 * cap
        assert abs((f.ah_used - f.ah_charged) - lost_ah) < 1e-6, f.id
    assert any(f.ah_used > 1.0 for f in fls)


def test_trucks_follow_the_schedule_through_every_stage(run3h: Run) -> None:
    tr = run3h.stages["TR-02"]
    after = tr[tr.index("gate"):]  # its first visit through the gate (it may start in the yard queue)
    assert after[:4] == ["gate", "weighbridge", "queue", "dock"], tr
    assert "paperwork" in tr and tr.index("paperwork") < len(tr) - 1
    k = run3h.h.engine.logistics.kpis()
    assert k["turnaround_min"] is not None and k["turnaround_min"] > 0
    assert k["arrivals_on_schedule"] is not None and k["dock_to_stock_min"] is not None
    assert k["forklift_utilisation"] is not None and 0 < k["forklift_utilisation"] < 1
    assert all(abs(d) < 120 for d in run3h.h.engine.logistics.samples["arrival_delay"])  # delays are minutes


def test_orders_ship_finished_goods_and_report_on_time(run3h: Run) -> None:
    lg = run3h.h.engine.logistics
    k = lg.kpis()
    assert k["orders_shipped"] >= 1 and k["on_time_dispatch"] is not None
    assert any(o.done_t is not None and o.shipped >= o.pallets for o in lg.orders)


def test_reorder_point_calls_the_supplier() -> None:
    h = Harness()
    auto(h)
    lg, w = h.engine.logistics, h.world
    t = w.entities["TR-03"]
    for pid in list(t.cargo or []):  # the supplier has delivered and gone; the presses used nearly everything
        w.entities.pop(pid)
    t.cargo, t.inbound, t.state, t.docked_at = [], False, "gone", None
    lg.visits["TR-03"].stage = "offsite"
    h.run(5, dt=0.5)
    assert lg.raw_on_order and lg.visits["TR-03"].arrive_t is not None
    assert any("reorder point" in e["text"] for e in h.of_type("event"))
    h.run((lg.visits["TR-03"].arrive_t - w.time) + 30, dt=0.5)
    assert t.inbound and t.cargo and all(p.startswith("RM-") for p in t.cargo)


def test_forklifts_top_up_in_breaks() -> None:
    h = Harness()
    auto(h, hour=12.2)  # A-shift lunch break
    for f in h.world.of_kind("forklift"):
        if f.meta.get("area") != "raw":
            f.battery = 60.0
    h.run(180, dt=0.5)
    reasons = {f.charge_reason for f in h.world.of_kind("forklift") if f.state == "charging"}
    assert "opportunity" in reasons, reasons
