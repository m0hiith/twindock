from fastapi.testclient import TestClient

from conftest import Harness


def test_auto_mode_is_off_by_default_and_moves_nothing(h: Harness) -> None:
    before = {u.id: (u.x, u.z) for u in h.world.of_kind("forklift")}
    h.run(10)
    assert {u.id: (u.x, u.z) for u in h.world.of_kind("forklift")} == before


def test_auto_mode_gives_idle_forklifts_tasks_marked_auto(h: Harness) -> None:
    h.client({"type": "set_auto_mode", "cmd_id": "a1", "enabled": True})
    assert h.last_ack()["ok"]
    h.run(5)
    auto = [u for u in h.world.of_kind("forklift") if u.source == "auto"]
    assert auto and any(u.moving for u in auto)
    h.run(240)  # let the loop run: loads, departures, returns
    assert all(e["level"] != "error" for e in h.of_type("event"))
    h.client({"type": "set_auto_mode", "cmd_id": "a2", "enabled": False})
    h.run(60)
    assert all(u.source == "manual" for u in h.world.of_kind("forklift") if not u.moving and not u.busy)


def test_websocket_snapshot_selection_and_ack() -> None:
    from twindock.main import app

    with TestClient(app) as c, c.websocket_connect("/ws") as a, c.websocket_connect("/ws") as b:
        snap = a.receive_json()
        assert snap["type"] == "world_snapshot" and snap["auto_mode"] is False
        assert any(u["id"] == "GW-01" and u["source"] == "device" for u in snap["units"])
        assert b.receive_json()["type"] == "world_snapshot"
        a.send_json({"type": "select_unit", "cmd_id": "s1", "unit_id": "FL-03"})

        def until(ws, t):  # type: ignore[no-untyped-def]
            while True:
                m = ws.receive_json()
                if m["type"] == t:
                    return m

        assert until(a, "command_ack")["ok"]
        assert until(b, "selection_changed")["selected_unit_id"] == "FL-03"
        assert c.get("/api/layout").json()["version"] == snap["layout_version"]
        assert c.post("/api/reset").json() == {"ok": True}
        assert until(b, "world_snapshot")["selected_unit_id"] is None
