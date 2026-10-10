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
from .wiring import WiringInvalid, load_wiring

log = logging.getLogger("twindock")

TICK_HZ = float(os.environ.get("TWINDOCK_TICK_HZ", "20"))  # CLAUDE.md: movement engine at 20 Hz
MQTT_ENABLED = os.environ.get("TWINDOCK_MQTT", "1") != "0"
MQTT_HOST = os.environ.get("TWINDOCK_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("TWINDOCK_MQTT_PORT", "1883"))


class App:
    def __init__(self) -> None:
        self.layout_json: dict[str, Any] = json.loads(DEFAULT_LAYOUT.read_text())
        self.engine = Engine(load_layout())
        self.hub = Hub()
        self.mqtt = MqttBridge(self.engine, self.flush, MQTT_HOST, MQTT_PORT)

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


@app.get("/api/snapshot")
def snapshot() -> dict[str, Any]:
    return state.engine.snapshot().model_dump(mode="json")


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
