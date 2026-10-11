"""R1: physically grounded utilities. Steady state, the pressure-band cycle, the standby compressor, leaks, the
generator's start and retransfer sequence, the energy balance, and water and effluent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SITES, SiteSim  # noqa: E402

CFG = json.loads(SITES.read_text())


def core_sim(hour: float = 12.0, seed: int = 21) -> SiteSim:
    """The whole campus's true state, no devices publishing."""
    s = SiteSim(CFG, [], seed=seed)
    s.verbose = False
    s.local_hour = lambda: hour  # type: ignore[method-assign]
    return s


def run(s: SiteSim, seconds: float, each=None) -> None:  # type: ignore[no-untyped-def]
    for _ in range(round(seconds / 0.25)):
        s.step(0.25)
        if each:
            each(s)


def balance(s: SiteSim) -> float:
    """Supply − load (kW): what came in from the grid, the roof, the generator and the UPS minus what is consuming."""
    pw = s.core.get("power")
    return pw.import_kw + pw.solar_kw + pw.gen_kw + pw.ups_kw - pw.load_kw


# ------------------------------------------------------------------ compressed air

def test_air_steady_state_holds_the_band_with_the_duty_compressor() -> None:
    s = core_sim()
    run(s, 300)
    air = s.core.get("air")
    lo, hi = [], []
    run(s, 1800, lambda s: (lo.append(air.bar), hi.append(air.bar)))
    assert 6.3 <= min(lo) and max(hi) <= 7.6, (min(lo), max(hi))
    assert air.compressors["CP-02"].state == "stopped"  # the standby is not needed
    assert 0.4 < (air.demand + air.leak) / s.params.f("air.compressors.CP-01.fad_nm3_min") < 1.0  # duty is enough


def test_pressure_band_cycle() -> None:
    """The duty compressor loads at the lower limit and unloads at the upper one; the cycle time follows from the
    receiver volume and the flows: t_up = ΔP·V·60 / (P_atm·(FAD − D)), t_down = ΔP·V·60 / (P_atm·D)."""
    s = core_sim()
    run(s, 120)
    air = s.core.get("air")
    events: list[tuple[float, str, float]] = []
    s.core.listeners.append(lambda e: events.append((e.t, e.name, air.bar)) if e.name.startswith("CP-01 ") else None)
    run(s, 900)
    loads = [(t, b) for t, n, b in events if n == "CP-01 loaded"]
    unloads = [(t, b) for t, n, b in events if n == "CP-01 unloaded"]
    assert len(loads) >= 5 and len(unloads) >= 5
    assert all(b <= 6.5 + 0.02 for _, b in loads) and all(b >= 7.5 - 0.02 for _, b in unloads)
    period = (loads[-1][0] - loads[0][0]) / (len(loads) - 1)
    p = s.params
    dp, v, atm = 1.0, p.f("air.receiver_m3"), p.f("air.p_atm_bar")
    fad = p.f("air.compressors.CP-01.fad_nm3_min")
    demand = air.demand + air.leak
    expected = dp * v * 60 / atm * (1 / (fad - demand) + 1 / demand)
    assert abs(period - expected) / expected < 0.35, (period, expected)  # machine demand varies a little between cycles


def test_duty_trip_starts_the_standby_and_low_air_stops_the_line() -> None:
    s = core_sim()
    run(s, 120)
    air, prod = s.core.get("air"), s.core.get("production")
    s.core.command("CP-01", "fault", {})
    tripped_at = None
    standby_loaded_at = None
    start = s.core.t
    for _ in range(4 * 120):
        running = {m.id for m in prod.machines.values() if m.state == "running"}
        s.step(0.25)
        if air.trip and tripped_at is None:
            tripped_at = s.core.t - start
            s.step(0.25)  # production reads the trip on its next step
            assert running and all(m.state == "fault" and m.alarm == "Low air pressure" for m in prod.machines.values() if m.id in running)
        if air.compressors["CP-02"].loaded and standby_loaded_at is None:
            standby_loaded_at = s.core.t - start
    p = s.params
    assert standby_loaded_at is not None and standby_loaded_at >= p.f("air.standby_start_delay_s") + p.f("air.star_delta_s")
    assert not air.trip and air.bar > p.f("air.trip_reset_bar")  # the standby recovered it
    assert all(m.state != "fault" or m.alarm != "Low air pressure" for m in prod.machines.values())
    names = [e.name for e in s.core.log]
    assert names.index("low air pressure trip") < names.index("low air pressure trip cleared")


def test_leaks_grow_and_a_leak_fix_resets_them() -> None:
    s = core_sim()
    air = s.core.get("air")
    start = air.leak_share
    run(s, 3600)
    grown = air.leak_share
    assert grown > start + 0.002
    s.core.command("CP-01", "fix_leaks", {})
    assert air.leak_share == s.params.f("air.leaks.after_fix_share") < start


# ------------------------------------------------------------------ electrical

def test_generator_start_sequence_timing() -> None:
    """Mains fail → start delay → crank → accelerate → transfer: the critical bus is on the generator within 10 s
    (ISO 8528-12 / NFPA 110 type 10). Non-critical zones are shed. Grid back → retransfer after its delay → cool-down → off."""
    s = core_sim()
    run(s, 60)
    pw, prod = s.core.get("power"), s.core.get("production")
    seen: dict[str, float] = {}
    s.core.listeners.append(lambda e: seen.setdefault(e.name, e.t))
    t0 = s.core.t
    s.core.command("PM-04", "grid_failure", {})
    run(s, 30)
    p = s.params
    rel = {k: round(v - t0, 2) for k, v in seen.items()}
    assert rel["generator start delay"] <= 0.25
    assert abs(rel["generator cranking"] - p.f("power.generator.mains_fail_delay_s")) <= 0.5
    on_gen = rel["transfer switch to generator"]
    assert on_gen == rel["generator running"] and on_gen <= 10.0, rel
    assert pw.transfer == "generator" and pw.gen_kw > 0 and pw.import_kw == 0 and pw.solar_kw == 0
    assert not s.core.q.powered("FAC01_PRODUCTION") and s.core.q.powered("FAC01_FIREPUMP")
    assert all(m.unpowered for m in prod.machines.values())  # the line is shed
    assert abs(pw.rpm - p.f("power.generator.rated_rpm")) < 50
    assert pw.fuel_lph > p.f("power.generator.idle_lph")
    c0 = pw.coolant_c
    run(s, 120)
    assert pw.coolant_c > c0  # warming up under load
    diesel = s.core.get("water").tanks["TL-02"]
    lvl = diesel.level_pct
    t1 = s.core.t
    s.core.command("PM-04", "grid_restore", {})
    run(s, p.f("power.generator.retransfer_delay_s") + p.f("power.generator.cooldown_s") + 10)
    rel = {k: round(v - t1, 2) for k, v in seen.items() if v >= t1}
    assert abs(rel["transfer switch to mains"] - p.f("power.generator.retransfer_delay_s")) <= 0.5
    assert abs(rel["generator off"] - rel["generator cooldown"] - p.f("power.generator.cooldown_s")) <= 0.5
    assert pw.gen_state == "off" and pw.transfer == "mains" and diesel.level_pct < lvl
    assert all(not m.unpowered for m in prod.machines.values())  # the line runs again


def test_energy_balance_in_every_state() -> None:
    """Supply equals load at every step: normal, the transfer gap, on generator, retransfer."""
    s = core_sim(hour=12.0)
    worst = [0.0]
    run(s, 120, lambda s: worst.__setitem__(0, max(worst[0], abs(balance(s)))))
    s.core.command("PM-04", "grid_failure", {})
    run(s, 60, lambda s: worst.__setitem__(0, max(worst[0], abs(balance(s)))))
    s.core.command("PM-04", "grid_restore", {})
    run(s, 240, lambda s: worst.__setitem__(0, max(worst[0], abs(balance(s)))))
    assert worst[0] < 1e-6, worst


def test_solar_never_exports_and_follows_the_day() -> None:
    noon, night = core_sim(hour=12.0), core_sim(hour=23.0)
    run(noon, 120)
    run(night, 120)
    pn, pm = noon.core.get("power"), night.core.get("power")
    assert pn.solar_kw > 50 and pm.solar_kw == 0.0
    assert pn.import_kw >= noon.params.f("power.solar.min_import_kw") - 1e-6  # the limiter keeps a small import
    assert pn.solar_kw <= pn.solar_available_kw + 1e-9


def test_power_factor_is_physical() -> None:
    """Feeders show their loads' PF. At night the APFC bank holds the incomer near its target; at midday solar
    supplies real power only, so the incomer's PF falls even with the bank in (a real effect at solar-heavy sites)."""
    night, noon = core_sim(hour=22.0), core_sim(hour=12.0)
    run(night, 120)
    run(noon, 120)
    for s in (night, noon):
        pw = s.core.get("power")
        for m in ("PM-01", "PM-06"):
            pf = pw.meter_pf(m)
            assert pf is not None and 0.8 < pf <= 1.0, (m, pf)
    pn = night.core.get("power")
    assert pn.meter_pf("PM-04") > 0.93 and pn.apfc_kvar > 0
    pm = noon.core.get("power")
    assert pm.meter_pf("PM-04") < pn.meter_pf("PM-04")


# ------------------------------------------------------------------ water

def test_water_steady_state_and_pumps() -> None:
    s = core_sim(hour=12.5)  # lunch: the canteen draws most
    w = s.core.get("water")
    seen_on: set[str] = set()
    run(s, 4 * 3600, lambda s: seen_on.update(t.id for t in w.tanks.values() if t.pumping))
    assert "TL-01" in seen_on  # the day tank was refilled by the transfer pump
    for tk in w.tanks.values():
        assert 0.0 < tk.level_pct <= 100.0, tk
    assert w.flows["canteen_m3h"] == s.params.f("water.canteen.meal_m3h")
    assert w.flows["cooling_m3h"] > 0


def test_etp_overload_raises_outflow_turbidity() -> None:
    s = core_sim(hour=12.5)
    w, eff = s.core.get("water"), s.core.get("effluent")
    etp = w.by_kind["etp"]
    run(s, 120)
    normal = next(p["ntu"] for p in eff.probes.values() if not p["inflow"])
    etp.level_pct = 99.0  # equalisation tank at overflow: more effluent than the plant can take
    run(s, 120)
    over = next(p["ntu"] for p in eff.probes.values() if not p["inflow"])
    assert over > normal + 15
