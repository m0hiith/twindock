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
import random
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .embedded_sim import STEP_S, EmbeddedSim, broker_reachable
from .engine import Engine, MqttOut, WsOut
from .graph import DEFAULT_LAYOUT, load_layout
from .hub import Hub
from .model_card import model_card
from .report import shift_report, shift_report_pdf, shift_window
from .models import WarmStart
from .mqtt_bridge import BrokerConfig, MqttBridge
from .simclock import SimClock, day_seed
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
MAX_STEP_S = 0.05  # one live tick at 20 Hz; at x5/x20 one tick is cut into slices this long
# Warm start (D3), embedded simulator only: fast-forward this many simulated minutes before serving, so a host that
# was asleep wakes up into a running factory. 0 switches it off (tests, local work against the real board).
WARM_START_MIN = float(os.environ.get("TWINDOCK_WARM_START_MIN", "45"))
# Engine and simulator step during the warm start. Movement is reservation-based (a unit never skips a node it
# hasn't been granted) and every sensor reports at 1 s or slower, so 1 s slices only make the fast-forward
# coarser, never wrong; they keep it well inside its 10 s budget with the historian recording.
WARM_STEP_S = 1.0
WARM_CHUNK_S = 10.0  # simulated seconds between drains of the (discarded) output
# After a warm start auto mode stays on (the hosted demo is a working factory); TWINDOCK_AUTO=0 turns it off.
AUTO_AFTER_WARM = os.environ.get("TWINDOCK_AUTO", "1") != "0"
# "Hosted demo" banner (D2): on (1), off (0), or auto: on when the simulator runs inside the backend and no broker was
# configured (no real board can reach this backend). The container sets auto; a local run defaults to off.
HOSTED = os.environ.get("TWINDOCK_HOSTED", "0")
# The built frontend (vite build). The container serves it from here; locally Vite serves it instead.
STATIC_DIR = Path(os.environ.get("TWINDOCK_STATIC_DIR") or Path(__file__).resolve().parents[2] / "frontend" / "dist")


class App:
    def __init__(self) -> None:
        self.layout_json: dict[str, Any] = json.loads(DEFAULT_LAYOUT.read_text())
        self.clock = SimClock()
        self.engine = Engine(load_layout(), clock=self.clock)
        self.hub = Hub()
        self.mqtt = MqttBridge(self.engine, self.flush, BROKER, MQTT_CLIENT_ID)
        self.sim: EmbeddedSim | None = None
        self.started_wall = time.time()
        self.tick_hz: float | None = None  # achieved over the last TICK_REPORT_S
        self._sim_acc = 0.0

    def flush(self) -> None:
        for o in self.engine.drain():
            if isinstance(o, WsOut):
                self.hub.send(o.to, o.msg)
            elif isinstance(o, MqttOut):
                if self.sim is not None and self.sim.command(o.topic, o.payload):
                    continue  # a command for a simulated device, handled in-process
                self.mqtt.publish(o.topic, o.payload)

    def advance(self, sim_dt: float, step: float = MAX_STEP_S, sim_step: float = STEP_S) -> None:
        """Move simulated time forward by sim_dt: the clock, the simulator (fixed STEP_S steps) and the engine, in
        slices of at most `step` so movement and traffic never jump. Used by the live loop and the warm start."""
        while sim_dt > 1e-9:
            h = min(sim_dt, step)
            sim_dt -= h
            self.clock.advance(h)
            if self.sim is not None:
                self._sim_acc += h
                while self._sim_acc >= sim_step - 1e-9:
                    self._sim_acc -= sim_step
                    self.sim.step(sim_step)
            self.engine.tick(h)
            self.flush()

    def start_sim(self, seed: int) -> None:
        self.sim = EmbeddedSim(self.engine, seed)
        self.sim.start()
        self.flush()

    def warm_start(self, minutes: float, seed: int) -> None:
        """Fast-forward `minutes` of simulated time before serving (D3): machines learn their baselines, the
        compressor cycles, trucks are mid-route. The clock was started that long ago, so it ends a few seconds behind
        the wall clock (the time the fast-forward took). Exactly `minutes` are simulated, so the same seed and start
        time give the same factory."""
        t0 = time.perf_counter()
        start_ms = self.clock.sim_ms
        self.engine.historian.delete_from(start_ms)  # a restart within the day re-simulates this stretch
        e = self.engine
        e.fast_forward, e.auto_mode = True, True
        assert self.sim is not None
        self.sim.sim.validate = False  # in-process and trusted; the engine still validates every message
        try:
            target = start_ms + int(minutes * 60_000)
            while self.clock.sim_ms < target:
                self.advance(min(WARM_CHUNK_S, (target - self.clock.sim_ms) / 1000), step=WARM_STEP_S, sim_step=WARM_STEP_S)
                e.drain()  # nobody is connected yet
        finally:
            self.sim.sim.validate = True
            e.fast_forward = False
        wall = time.perf_counter() - t0
        e.warm_start = WarmStart(sim_s=round((self.clock.sim_ms - start_ms) / 1000, 1), wall_s=round(wall, 2), seed=seed)
        e.event("info", f"Warm start: {e.warm_start.sim_s / 60:.0f} simulated minutes in {wall:.1f} s (seed {seed})", "sim")
        log.info("warm start: %.0f simulated s in %.2f s (seed %d)", e.warm_start.sim_s, wall, seed)

    async def run_loop(self) -> None:
        """The live loop: 20 Hz, each tick advances simulated time by real time x speed."""
        period = 1.0 / TICK_HZ
        last = time.monotonic()
        window_start, ticks = last, 0
        while True:
            await asyncio.sleep(max(0.0, last + period - time.monotonic()))
            now = time.monotonic()
            # Cap real dt so a stalled loop (laptop sleep, a frozen host) doesn't teleport units across the map.
            self.advance(min(now - last, 0.25) * self.clock.speed)
            last = now
            ticks += 1
            if now - window_start >= TICK_REPORT_S:
                self.tick_hz = ticks / (now - window_start)
                if self.tick_hz < TICK_WARN_HZ:
                    log.warning("tick loop at %.1f Hz (target %.0f Hz): the host is too slow or overloaded", self.tick_hz, TICK_HZ)
                window_start, ticks = now, 0


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
    if MQTT_ENABLED:
        mqtt_task = asyncio.create_task(state.mqtt.run())
    else:
        log.warning("MQTT disabled (TWINDOCK_MQTT=0): the board twin will show Waiting for device")
    if _want_embedded_sim():
        seed = int(os.environ["TWINDOCK_SEED"]) if os.environ.get("TWINDOCK_SEED") else day_seed(time.strftime("%Y-%m-%d"))
        if not os.environ.get("TWINDOCK_AUTO_SEED"):
            state.engine.rng = random.Random(seed + 1)
        try:
            if WARM_START_MIN > 0:
                state.clock.sim_ms = int(time.time() * 1000) - int(WARM_START_MIN * 60_000)
            state.start_sim(seed)
            if WARM_START_MIN > 0:
                state.warm_start(WARM_START_MIN, seed)
                state.engine.auto_mode = AUTO_AFTER_WARM
        except Exception:  # noqa: BLE001 - a missing simulator only leaves the SIM devices offline
            log.exception("embedded site simulator unavailable; SIM devices will show offline")
            state.sim = None
            state.engine.fast_forward = False
    tasks = [asyncio.create_task(state.run_loop())] + ([mqtt_task] if MQTT_ENABLED else [])
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
            "sim_clock_ms": state.clock.sim_ms, "sim_speed": state.clock.speed,
            "warm_start": e.warm_start.model_dump() if e.warm_start else None,
            "devices_online": sum(d["status"] == "online" for d in devices), "devices_total": len(devices),
            "mqtt": str(BROKER) if MQTT_ENABLED else None, "mqtt_connected": e.mqtt_connected,
            "hosted": HOSTED == "1" or (HOSTED == "auto" and state.sim is not None and not MQTT_URL),
            "gateway_online": e.gw.online, "gateway_fake": e.gw.fake, "clients": len(state.hub.clients), "auto_mode": e.auto_mode}


RANGES_S = {"15m": 15 * 60, "1h": 3600, "8h": 8 * 3600, "24h": 24 * 3600}


def _history_window(range_: str) -> tuple[int, int]:
    """[t0, t1] in simulated ms: a fixed span back from now, or the current shift ("shift")."""
    now = state.engine.clock()
    if range_ == "shift":
        from sim import Params
        _, t0, _ = shift_window(Params.load().v("production.shifts.calendar"), now)
        return t0, now
    if range_ not in RANGES_S:
        raise HTTPException(status_code=400, detail=f"range must be one of {', '.join([*RANGES_S, 'shift'])}")
    return now - RANGES_S[range_] * 1000, now


@app.get("/api/history")
def history(device: str, channel: str, range: str = "1h", buckets: int = 240) -> dict[str, Any]:
    """Historian series for a chart: [bucket start ms, avg, min, max, n] (simulated time; SIM devices and the board's RSSI)."""
    t0, t1 = _history_window(range)
    return {"device_id": device, "channel": channel, "range": range, "from_ms": t0, "to_ms": t1,
            "points": state.engine.historian.series(device, channel, t0, t1, max(10, min(buckets, 2000)))}


@app.get("/api/history.csv")
def history_csv(device: str, channel: str, range: str = "1h", raw: bool = False) -> Response:
    """The same series as CSV (or every stored point with raw=true), for any chart's download link."""
    t0, t1 = _history_window(range)
    h = state.engine.historian
    if raw:
        lines = ["time,value"] + [f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t / 1000))},{v}" for t, v in h.raw(device, channel, t0, t1)]
    else:
        lines = ["time,avg,min,max,samples"] + [f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t / 1000))},{a},{lo},{hi},{n}"
                                                for t, a, lo, hi, n in h.series(device, channel, t0, t1, 240)]
    name = f"{device}_{channel}_{range}.csv"
    return Response("\n".join(lines) + "\n", media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/report/shift")
def report_shift(which: str = "current") -> dict[str, Any]:
    """The shift report's data (which = current or previous)."""
    if which not in ("current", "previous"):
        raise HTTPException(status_code=400, detail="which must be current or previous")
    return shift_report(state.engine, which)


@app.get("/api/report/shift.pdf")
def report_shift_pdf(which: str = "current") -> Response:
    r = report_shift(which)
    name = f"twindock_shift_{r['shift']}_{time.strftime('%Y%m%d', time.localtime(r['from_ms'] / 1000))}.pdf"
    return Response(shift_report_pdf(r), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/model")
def model() -> dict[str, Any]:
    """The simulation's model card for /model: models, equations, parameters with sources, sensors, distributions."""
    return model_card(state.engine.devices.cfg, state.layout_json, state.sim)


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
