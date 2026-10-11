"""FastAPI app: WebSocket hub at /ws, REST helpers under /api, 20 Hz tick, MQTT bridge, and (in the container)
the built frontend.

Run from the repo root:
    .venv/bin/uvicorn twindock.main:app --app-dir backend --host 0.0.0.0 --port 8000

The world lives in this process's memory, so it must run as exactly one worker that stays up
(docs/deploy_diagnosis.md): a container, a VM or a laptop, never serverless functions.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .embedded_sim import STEP_S, EmbeddedSim, broker_reachable
from .engine import Engine, MqttOut, WsOut
from .graph import DEFAULT_LAYOUT, load_layout
from .hub import Hub
from .mqtt_bridge import BrokerConfig, MqttBridge
from .wiring import KitNotFound, WiringInvalid, kit_summary, load_kit, load_kits, load_wiring

log = logging.getLogger("twindock")

TICK_HZ = float(os.environ.get("TWINDOCK_TICK_HZ", "20"))  # CLAUDE.md: movement engine at 20 Hz
TICK_WARN_HZ = 15.0  # below this the 3D twin visibly stutters; logged so a too-small host shows up in the logs
TICK_REPORT_S = 5.0  # achieved tick rate is measured over this window
# Broker: MQTT_URL (mqtt://host:1883, mqtts://user:pass@host:8883) wins; otherwise the local Mosquitto from
# TWINDOCK_MQTT_HOST/PORT, unless TWINDOCK_MQTT=0 (the container's default: no broker configured).
MQTT_URL = os.environ.get("MQTT_URL", "").strip()
MQTT_ENABLED = bool(MQTT_URL) or os.environ.get("TWINDOCK_MQTT", "1") != "0"
BROKER = BrokerConfig.from_url(MQTT_URL) if MQTT_URL else BrokerConfig(
    os.environ.get("TWINDOCK_MQTT_HOST", "127.0.0.1"), int(os.environ.get("TWINDOCK_MQTT_PORT", "1883")))
MQTT_CLIENT_ID = os.environ.get("TWINDOCK_MQTT_CLIENT_ID", "twindock-backend")
# Site simulator: "external" (tools/site_sim.py through the broker), "embedded" (inside this process) or "auto":
# embedded when no local broker is reachable at startup or the broker is a remote one from MQTT_URL (nobody runs
# tools/site_sim.py next to a hosted backend), external otherwise.
SIM_MODE = os.environ.get("TWINDOCK_SIM", "auto")
# The built frontend (vite build). The container serves it from here; locally Vite serves it instead.
STATIC_DIR = Path(os.environ.get("TWINDOCK_STATIC_DIR") or Path(__file__).resolve().parents[2] / "frontend" / "dist")


class App:
    def __init__(self) -> None:
        self.layout_json: dict[str, Any] = json.loads(DEFAULT_LAYOUT.read_text())
        self.engine = Engine(load_layout())
        self.hub = Hub()
        self.mqtt = MqttBridge(self.engine, self.flush, BROKER, MQTT_CLIENT_ID)
        self.sim: EmbeddedSim | None = None
        self.started_wall = time.time()
        self.tick_hz: float | None = None  # achieved over the last TICK_REPORT_S

    def flush(self) -> None:
        for o in self.engine.drain():
            if isinstance(o, WsOut):
                self.hub.send(o.to, o.msg)
            elif isinstance(o, MqttOut):
                if self.sim is not None and self.sim.command(o.topic, o.payload):
                    continue  # a command for a simulated device, handled in-process
                self.mqtt.publish(o.topic, o.payload)

    async def tick_loop(self) -> None:
        period = 1.0 / TICK_HZ
        last = time.monotonic()
        window_start, ticks = last, 0
        while True:
            await asyncio.sleep(max(0.0, last + period - time.monotonic()))
            now = time.monotonic()
            # Cap dt so a stalled loop (laptop sleep) doesn't teleport units across the map.
            self.engine.tick(min(now - last, 0.25))
            last = now
            self.flush()
            ticks += 1
            if now - window_start >= TICK_REPORT_S:
                self.tick_hz = ticks / (now - window_start)
                if self.tick_hz < TICK_WARN_HZ:
                    log.warning("tick loop at %.1f Hz (target %.0f Hz): the host is too slow or overloaded", self.tick_hz, TICK_HZ)
                window_start, ticks = now, 0

    async def sim_loop(self) -> None:
        assert self.sim is not None
        self.sim.start()
        self.flush()
        last = time.monotonic()
        while True:
            await asyncio.sleep(STEP_S)
            now = time.monotonic()
            self.sim.step(min(now - last, 1.0))
            last = now
            self.flush()


state = App()


def _want_embedded_sim() -> bool:
    if SIM_MODE == "embedded":
        return True
    if SIM_MODE == "external":
        return False
    return not MQTT_ENABLED or bool(MQTT_URL) or not broker_reachable(BROKER.host, BROKER.port)


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    tasks = [asyncio.create_task(state.tick_loop())]
    if MQTT_ENABLED:
        tasks.append(asyncio.create_task(state.mqtt.run()))
    else:
        log.warning("MQTT disabled (TWINDOCK_MQTT=0): the board twin will show Waiting for device")
    if _want_embedded_sim():
        try:
            state.sim = EmbeddedSim(state.engine)
            tasks.append(asyncio.create_task(state.sim_loop()))
        except Exception:  # noqa: BLE001 - a missing simulator only leaves the SIM devices offline
            log.exception("embedded site simulator unavailable; SIM devices will show offline")
            state.sim = None
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="TwinDock backend", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Liveness for the host's health check, plus what an operator needs to see that the process is really running."""
    e = state.engine
    now = e.clock()
    devices = [d for d in e.devices.wire(e.gw, now, e.ble) if d["source"] == "sim"]
    return {"ok": True, "uptime_s": round(time.time() - state.started_wall, 1),
            "tick_hz": None if state.tick_hz is None else round(state.tick_hz, 1), "tick_target_hz": TICK_HZ,
            "sim": "embedded" if state.sim else "external",
            "sim_clock_s": round(state.sim.sim.t, 1) if state.sim else None,
            "devices_online": sum(d["status"] == "online" for d in devices), "devices_total": len(devices),
            "mqtt": str(BROKER) if MQTT_ENABLED else None, "mqtt_connected": e.mqtt_connected,
            "gateway_online": e.gw.online, "gateway_fake": e.gw.fake, "clients": len(state.hub.clients), "auto_mode": e.auto_mode}


@app.get("/api/layout")
def layout() -> dict[str, Any]:
    """Static geometry for the 3D scene and the Control Room map."""
    return state.layout_json


@app.get("/api/wiring")
def wiring() -> dict[str, Any]:
    """hardware/wiring.json for the /wiring page (parts, buses, connections, board drawing)."""
    try:
        return load_wiring()
    except WiringInvalid as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/monitor")
def monitor() -> dict[str, Any]:
    """Monitoring centre: energy (kW now, today vs yesterday), the last 24 h of alerts with acknowledgement and
    resolution times, the last evacuation and today's safety counters. Energy comes from the simulated meters."""
    return state.engine.monitor_summary()


@app.get("/api/safety/me/{worker_id}")
def safety_me(worker_id: str) -> dict[str, Any]:
    """A worker's own data: shift hours, breaks and their own incidents (K3 privacy: workers can see their data).
    There is no sign-in in the demo, so this is the worker's link, not a protected page."""
    e = state.engine
    d = e.safety.personal(worker_id, e.clock())
    if d is None:
        raise HTTPException(status_code=404, detail=f"No worker {worker_id}")
    return d


@app.get("/api/safety/shift")
def safety_shift() -> dict[str, Any]:
    """Shift and break overview for the supervisor (hours on shift, breaks due)."""
    e = state.engine
    now = e.clock()
    return {"workers": [e.safety.personal(w, now) for w in e.safety.workers], "retention_days": e.safety.privacy.get("retention_days", 30)}


@app.get("/api/kits")
def kits() -> list[dict[str, Any]]:
    """One summary per device kit (hardware/kits/*.json) with the devices built from it, for /kits and the picker."""
    by_kit: dict[str, list[str]] = {}
    for d in state.engine.devices.defs.values():
        if d.get("kit"):
            by_kit.setdefault(d["kit"], []).append(d["id"])
    try:
        return [kit_summary(k, by_kit.get(k["kit"]["id"])) for k in load_kits()]
    except WiringInvalid as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/kits/{kit_id}")
def kit(kit_id: str) -> dict[str, Any]:
    """One full kit file for /wiring/:kit_id."""
    try:
        return load_kit(kit_id)
    except KitNotFound as e:
        raise HTTPException(status_code=404, detail=f"No kit {kit_id}") from e
    except WiringInvalid as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/snapshot")
def snapshot() -> dict[str, Any]:
    return state.engine.snapshot().model_dump(mode="json")


@app.get("/api/devices/{device_id}/history")
def device_history(device_id: str, channel: str) -> dict[str, Any]:
    """Recent numeric values of one device channel, for the /fleet side panel chart."""
    if device_id not in state.engine.devices.defs:
        raise HTTPException(status_code=404, detail=f"Unknown device {device_id}")
    return {"device_id": device_id, "channel": channel,
            "points": [[t, v] for t, v in state.engine.devices.history(device_id, channel)]}


@app.post("/api/reset")
def reset() -> dict[str, bool]:
    state.engine.reset()
    state.flush()
    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    cid = state.hub.add(ws)
    state.engine.on_connect(cid)
    state.flush()
    try:
        while True:
            text = await ws.receive_text()
            state.engine.handle_client(cid, text)
            state.flush()
    except WebSocketDisconnect:
        pass
    finally:
        state.hub.remove(cid)


# ---------------------------------------------------------------------- the built frontend (container)
# Registered last so /api and /ws always win. Any other path is a page of the single-page app (/twin, /control,
# /device, /wiring/...): a file from dist/ when one exists, index.html otherwise.
if (STATIC_DIR / "index.html").is_file():
    _dist = STATIC_DIR.resolve()
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        f = (_dist / path).resolve()
        if path and f.is_file() and f.is_relative_to(_dist):
            return FileResponse(f)
        return FileResponse(_dist / "index.html", headers={"Cache-Control": "no-cache"})
