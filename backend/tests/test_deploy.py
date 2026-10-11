"""D1: one production container. Broker config from MQTT_URL, /api/health, the built frontend served by FastAPI."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from twindock.mqtt_bridge import BrokerConfig


def test_mqtt_url_parsing() -> None:
    b = BrokerConfig.from_url("mqtts://user%40td:s3cret@abc.s1.eu.hivemq.cloud")
    assert (b.host, b.port, b.username, b.password, b.tls) == ("abc.s1.eu.hivemq.cloud", 8883, "user@td", "s3cret", True)
    assert "s3cret" not in str(b), "the password is never logged"
    assert BrokerConfig.from_url("mqtt://10.0.0.5") == BrokerConfig("10.0.0.5", 1883)
    with pytest.raises(ValueError):
        BrokerConfig.from_url("http://example.com")


def test_health_reports_process_state() -> None:
    from twindock.main import app
    with TestClient(app) as c:
        h = c.get("/api/health").json()
    assert h["ok"] is True
    assert h["sim"] == "embedded"  # tests run without a broker
    for k in ("uptime_s", "tick_hz", "tick_target_hz", "sim_clock_ms", "sim_speed", "devices_online", "devices_total"):
        assert k in h
    assert h["devices_total"] > 50


def test_built_frontend_is_served_with_spa_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>TwinDock</title>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "brand.png").write_bytes(b"png")
    monkeypatch.setenv("TWINDOCK_STATIC_DIR", str(tmp_path))
    import twindock.main as main
    m = importlib.reload(main)
    try:
        c = TestClient(m.app)
        assert "TwinDock" in c.get("/").text
        assert "TwinDock" in c.get("/control").text  # a client-side route
        assert "TwinDock" in c.get("/wiring/fl01_sensor_pack").text
        assert c.get("/assets/app.js").text == "console.log(1)"
        assert c.get("/brand.png").content == b"png"
        assert c.get("/api/layout").json()["nodes"]  # the API still wins
        assert c.get("/api/nope").status_code == 404  # an unknown API path is not the app
        assert "TwinDock" in c.get("/../../etc/passwd").text  # never a file outside dist
    finally:
        monkeypatch.delenv("TWINDOCK_STATIC_DIR")
        importlib.reload(main)
