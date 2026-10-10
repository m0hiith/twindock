"""S3: proximity rule (moving vs parked forklift), thresholds, restricted zones, badges, real badge path."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from conftest import Harness

from twindock.devices import load_sites
from twindock.safety import Safety

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from site_sim import SiteSim, select_devices  # noqa: E402

CFG = load_sites()
ZONES = {z["id"]: z for s in CFG["sites"] for z in s["zones"]}
BADGE_HELLO = {"type": "badge", "protocol": "ble", "fw_version": "sim-3.0", "source": "sim", "capabilities": ["position"]}


def safety() -> Safety:
    return Safety.build(CFG["safety"], CFG["workers"])


def place(s: Safety, wid: str, x: float, z: float, zone: str | None = None) -> None:
    s.set_position(wid, x, z, ZONES.get(zone or ""), 0)


FRESH = {f"BG-0{i}": True for i in range(1, 5)}


def test_parked_forklift_never_triggers() -> None:
    s = safety()
    place(s, "WK-02", 100.0, 14.0, "FAC01_PRODUCTION")
    ev = s.evaluate(0, [("FL-01", 100.5, 14.0, 0.0)], FRESH, ZONES)  # 0.5 m away but parked
    assert ev == [] and s.workers["WK-02"].near is None


def test_moving_forklift_thresholds_and_hysteresis() -> None:
    s = safety()
    place(s, "WK-02", 100.0, 14.0, "FAC01_PRODUCTION")
    assert s.evaluate(0, [("FL-01", 103.4, 14.0, 4.0)], FRESH, ZONES) == []           # 3.4 m: fine
    ev = s.evaluate(1, [("FL-01", 102.8, 14.0, 4.0)], FRESH, ZONES)                    # 2.8 m: warning
    assert [e[0] for e in ev] == ["warn"] and s.workers["WK-02"].near.level == "warning"  # type: ignore[union-attr]
    ev = s.evaluate(2, [("FL-01", 101.2, 14.0, 4.0)], FRESH, ZONES)                    # 1.2 m: critical
    assert [e[0] for e in ev] == ["error"] and s.workers["WK-02"].near.level == "critical"  # type: ignore[union-attr]
    assert s.evaluate(3, [("FL-01", 103.3, 14.0, 4.0)], FRESH, ZONES) == []           # 3.3 m: still near (hysteresis)
    assert s.workers["WK-02"].near is not None
    ev = s.evaluate(4, [("FL-01", 103.8, 14.0, 4.0)], FRESH, ZONES)                    # 3.8 m: cleared
    assert [e[0] for e in ev] == ["info"] and s.workers["WK-02"].near is None
    assert s.today.warnings == 1 and s.today.criticals == 1 and s.today.closest_m == 1.2


def test_forklift_stopping_clears_the_warning() -> None:
    s = safety()
    place(s, "WK-02", 100.0, 14.0)
    s.evaluate(0, [("FL-01", 102.0, 14.0, 3.0)], FRESH, ZONES)
    assert s.workers["WK-02"].near is not None
    s.evaluate(1, [("FL-01", 102.0, 14.0, 0.0)], FRESH, ZONES)
    assert s.workers["WK-02"].near is None


def test_stale_badge_claims_nothing() -> None:
    s = safety()
    place(s, "WK-02", 100.0, 14.0)
    ev = s.evaluate(0, [("FL-01", 100.5, 14.0, 4.0)], {**FRESH, "BG-02": False}, ZONES)
    assert ev == [] and s.workers["WK-02"].near is None


def test_restricted_zones_by_role() -> None:
    s = safety()
    place(s, "WK-04", 122.0, 12.2, "FAC01_PRESS")   # visitor in the press area
    place(s, "WK-01", 122.0, 12.2, "FAC01_PRESS")   # press operator: allowed
    place(s, "WK-02", 135.0, 21.0, "FAC01_COLD")    # logistics in the cold room: allowed
    place(s, "WK-03", 135.0, 21.0, "FAC01_COLD")    # QC inspector in the cold room: not allowed
    ev = s.evaluate(0, [], FRESH, ZONES)
    texts = sorted(t for _, t, _ in ev)
    assert len(ev) == 2 and all(lvl == "error" for lvl, _, _ in ev)
    assert any("WK-04" in t and "Press area" in t for t in texts)
    assert any("WK-03" in t and "Cold room" in t for t in texts)
    assert s.evaluate(1, [], FRESH, ZONES) == []  # raised once, not every tick
    place(s, "WK-04", 110.0, 14.0, "FAC01_PRODUCTION")
    ev = s.evaluate(2, [], FRESH, ZONES)
    assert any("WK-04 left" in t for _, t, _ in ev) and s.today.restricted == 2


def test_zone_lookup_prefers_the_sub_zone(h: Harness) -> None:
    assert h.engine.devices.zone_at(122.0, 12.2, "FAC-01")["id"] == "FAC01_PRESS"  # type: ignore[index]
    assert h.engine.devices.zone_at(110.0, 14.0, "FAC-01")["id"] == "FAC01_PRODUCTION"  # type: ignore[index]


def badge_pos(h: Harness, dev: str, x: float, z: float) -> None:
    h.engine.on_mqtt(f"twin/FAC-01/{dev}/position",
                     json.dumps({"ts_ms": 1, "value": [x, z], "unit": "m", "source": "sim"}).encode())
    h.collect()


def test_engine_workers_follow_badges_and_warn_near_moving_forklift(h: Harness) -> None:
    for i in range(1, 5):
        h.engine.on_mqtt(f"twin/FAC-01/BG-0{i}/hello", json.dumps(BADGE_HELLO).encode())
    assert h.world.entities["WK-02"].state == "no_data"
    # FL-04 drives to the factory outbound; WK-02 stands next to the lane it uses
    assert h.world.command("FL-04", "FAC_OUT", "goto", source="manual").ok
    hit = False
    for _ in range(200):
        f = h.world.entities["FL-04"]
        badge_pos(h, "BG-02", 75.0, 20.2)  # 1.4 m beside the link lane (z = 18.8)
        h.run(0.25)
        if h.engine.safety.workers["WK-02"].near is not None:
            hit = True
            break
    assert hit, "no proximity warning while FL-04 drove past"
    badge_pos(h, "BG-02", 75.0, 20.2)
    h.run(0.6)  # let the next safety_update go out
    assert h.world.entities["WK-02"].x == 75.0 and h.world.entities["WK-02"].source == "sim"
    texts = [e["text"] for e in h.of_type("event")]
    assert any("Pedestrian near forklift: WK-02" in t and "FL-04" in t for t in texts)
    su = h.of_type("safety_update")[-1]  # schema-checked by the harness
    assert any(w["id"] == "WK-02" and w["near"] for w in su["workers"])
    assert all("name" not in w for w in su["workers"])  # privacy: no names on the wire
    assert f.id == "FL-04"


def test_real_badge_comes_only_from_the_boards_ble(h: Harness) -> None:
    h.board_online()
    h.mqtt_in("twin/gateway/ble", {"ts_ms": 2000, "sightings": [{"name": "TD-BADGE-01", "addr": "AA:BB:CC:00:11:22", "rssi_dbm": -61}]})
    rb = h.engine.devices.wire_device("RB-01", h.engine.gw, h.clock.ms, h.engine.ble)
    assert rb["source"] == "device" and rb["status"] == "online" and rb["rssi_dbm"] == -61
    assert rb["readings"]["rssi_dbm"]["value"] == -61
    assert not any("TD-BADGE-01 has no matching forklift" in e["text"] for e in h.of_type("event"))
    # the simulator can't write it
    h.engine.on_mqtt("twin/WH-01/RB-01/hello", json.dumps(BADGE_HELLO).encode())
    h.collect()
    assert any("RB-01 is a real device" in e["text"] for e in h.of_type("event"))
    h.run(16.0)  # the BLE tracker drops a tag after lost_after_s (10 s): no data means offline
    assert h.engine.devices.wire_device("RB-01", h.engine.gw, h.clock.ms, h.engine.ble)["status"] == "offline"


def test_simulated_badges_walk_their_routes() -> None:
    cfg = json.loads((Path(__file__).resolve().parents[1] / "world" / "sites.json").read_text())
    s = SiteSim(cfg, select_devices(cfg, "FAC-01", None), seed=4)
    sent: list[tuple[str, dict]] = []
    s.publish = lambda m, ch, p, retain=False: sent.append((s.topic(m, ch), p))  # type: ignore[method-assign]
    for _ in range(240):  # 60 s
        s.step(0.25)
    pos = [p["value"] for t, p in sent if t == "twin/FAC-01/BG-02/position"]
    assert len(pos) >= 50
    moved = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pos, pos[1:]))
    assert moved > 10  # walked somewhere
    assert all(84 < p[0] < 142 and -2 < p[1] < 42 for p in pos)  # stayed on FAC-01
    random.seed(0)
