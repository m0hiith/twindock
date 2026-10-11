"""FastAPI app: WebSocket hub at /ws, REST helpers under /api, 20 Hz tick, MQTT bridge.

Run from the repo root:
    .venv/bin/uvicorn twindock.main:app --app-dir backend --host 0.0.0.0 --port 8000
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

from .engine import Engine, MqttOut, WsOut
from .graph import DEFAULT_LAYOUT, load_layout
from .hub import Hub
from .mqtt_bridge import MqttBridge
from .wiring import KitNotFound, WiringInvalid, kit_summary, load_kit, load_kits, load_wiring

log = logging.getLogger("twindock")

TICK_HZ = float(os.environ.get("TWINDOCK_TICK_HZ", "20"))  # CLAUDE.md: movement engine at 20 Hz
MQTT_ENABLED = os.environ.get("TWINDOCK_MQTT", "1") != "0"
MQTT_HOST = os.environ.get("TWINDOCK_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("TWINDOCK_MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.environ.get("TWINDOCK_MQTT_CLIENT_ID", "twindock-backend")


class App:
    def __init__(self) -> None:
        self.layout_json: dict[str, Any] = json.loads(DEFAULT_LAYOUT.read_text())
        self.engine = Engine(load_layout())
        self.hub = Hub()
        self.mqtt = MqttBridge(self.engine, self.flush, MQTT_HOST, MQTT_PORT, MQTT_CLIENT_ID)

    def flush(self) -> None:
        for o in self.engine.drain():
            if isinstance(o, WsOut):
                self.hub.send(o.to, o.msg)
            elif isinstance(o, MqttOut):
                self.mqtt.publish(o.topic, o.payload)

    async def tick_loop(self) -> None:
        period = 1.0 / TICK_HZ
        last = time.monotonic()
        while True:
            await asyncio.sleep(max(0.0, last + period - time.monotonic()))
            now = time.monotonic()
            # Cap dt so a stalled loop (laptop sleep) doesn't teleport units across the map.
            self.engine.tick(min(now - last, 0.25))
            last = now
            self.flush()


state = App()


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    tasks = [asyncio.create_task(state.tick_loop())]
    if MQTT_ENABLED:
        tasks.append(asyncio.create_task(state.mqtt.run()))
    else:
        log.warning("MQTT disabled (TWINDOCK_MQTT=0): the board twin will show Waiting for device")
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="TwinDock backend", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict[str, Any]:
    e = state.engine
    return {"ok": True, "mqtt_connected": e.mqtt_connected, "gateway_online": e.gw.online,
            "gateway_fake": e.gw.fake, "clients": len(state.hub.clients), "auto_mode": e.auto_mode}


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
