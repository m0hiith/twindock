"""Device kits (hardware/kits/*.json): schema, electrical checks and the BOM, for every kit."""

import json

import pytest
from fastapi.testclient import TestClient

from twindock.devices import load_sites
from twindock.main import app
from twindock.wiring import KITS_DIR, KitNotFound, kit_ids, load_kit, load_kits, validate_kit

IDS = kit_ids()


def test_fl01_is_the_only_built_kit() -> None:
    built = [k["kit"]["id"] for k in load_kits() if k["kit"]["status"] == "built"]
    assert built == ["fl01_sensor_pack"]


@pytest.mark.parametrize("kit_id", IDS)
def test_kit_is_valid(kit_id: str) -> None:
    assert validate_kit(load_kit(kit_id)) == []


@pytest.mark.parametrize("kit_id", IDS)
def test_every_sim_kit_is_attached_to_a_device(kit_id: str) -> None:
    used = {d.get("kit") for d in load_sites()["devices"]}
    if load_kit(kit_id)["kit"]["status"] == "reference" and kit_id not in ATTACH_LATER:
        assert kit_id in used, f"{kit_id} is not attached to any device in sites.json"


ATTACH_LATER: set[str] = set()


def _break(kit: dict, fn) -> list[str]:  # type: ignore[type-arg]
    k = json.loads(json.dumps(kit))
    fn(k)
    return validate_kit(k)


def test_validator_catches_each_kind_of_mistake() -> None:
    base = load_kit("fl01_sensor_pack")
    p = lambda k, i: next(x for x in k["parts"] if x["id"] == i)  # noqa: E731

    assert any("address" in e for e in _break(base, lambda k: p(k, "vl53l1x").pop("runtime_address")))
    assert any("different signals" in e for e in _break(base, lambda k: k["connections"].append(
        {**k["connections"][0], "id": "x", "signal": "MOSI"})))
    assert any("driven twice" in e for e in _break(base, lambda k: k["connections"].append(
        {**next(c for c in k["connections"] if c["id"] == "loadcell_exc_p"), "id": "x"})))
    assert any("allows" in e for e in _break(base, lambda k: next(b for b in k["buses"] if b["id"] == "vmcu").update(voltage_v=5.0)))
    assert any("not in the bill" in e for e in _break(base, lambda k: k["bom"].pop()))
    assert any("unknown part" in e for e in _break(base, lambda k: k["bom"][0]["covers"].append("ghost")))
    assert any("unknown pin" in e for e in _break(base, lambda k: k["connections"][0].update(to="soc.NOPE")))
    assert any("only the FL-01" in e for e in _break(base, lambda k: k["kit"].update(id="other")))


def test_kit_files_match_their_ids() -> None:
    assert sorted(p.stem for p in KITS_DIR.glob("*.json")) == IDS
    with pytest.raises(KitNotFound):
        load_kit("../etc")


def test_kit_endpoints() -> None:
    c = TestClient(app)
    idx = c.get("/api/kits").json()
    fl = next(k for k in idx if k["id"] == "fl01_sensor_pack")
    assert fl["status"] == "built" and fl["devices"] == ["GW-01"] and fl["part_count"] == 4
    assert c.get("/api/kits/fl01_sensor_pack").json() == load_kit("fl01_sensor_pack")
    assert c.get("/api/kits/nope").status_code == 404
    assert c.get("/api/wiring").json() == load_kit("fl01_sensor_pack")


def test_sites_json_rejects_an_unknown_kit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from twindock.devices import SITES_FILE
    cfg = json.loads(SITES_FILE.read_text())
    cfg["devices"][0]["kit"] = "nope"
    f = tmp_path / "sites.json"
    f.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="unknown kit"):
        load_sites(f)
