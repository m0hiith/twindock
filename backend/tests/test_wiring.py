from fastapi.testclient import TestClient

from twindock.main import app
from twindock.wiring import load_wiring


def test_wiring_file_matches_schema() -> None:
    w = load_wiring()
    status = {p["id"]: p["status"] for p in w["parts"]}
    # Parts the board itself connects are wired; nothing is verified before firmware reads a value.
    assert {status[p] for p in ("si7021", "veml6035", "icm40627")} == {"wired"}
    assert {status[p] for p in ("vl53l1x", "nau7802", "load_cell")} == {"planned"}
    assert "verified" not in status.values()
    for c in w["connections"]:
        assert c["status"] == ("wired" if c["medium"] == "pcb" else "planned"), c["id"]


def test_board_drawing_points_at_real_parts() -> None:
    w = load_wiring()
    ids = {p["id"] for p in w["parts"]}
    assert all(f["part"] in ids for f in w["board_drawing"]["features"] if f["part"] is not None)
    assert (w["board_drawing"]["width_mm"], w["board_drawing"]["height_mm"]) == (30.4, 55.0)  # UG581 Figure 1.1


def test_get_api_wiring_serves_the_file() -> None:
    r = TestClient(app).get("/api/wiring")
    assert r.status_code == 200
    assert r.json() == load_wiring()
