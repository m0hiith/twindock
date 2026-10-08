# TwinDock

A browser-based digital twin of a small warehouse ("Riverside Logistics Hub"), driven by a real
Silicon Labs **SiWx917 Dev Kit (BRD2605A)** over Wi-Fi/MQTT, plus a phone-friendly Control Room for
moving forklifts and trucks by hand.

> Design inspiration: the visual language is inspired by **Dilum Sanjaya's "WareTrack"** concept.
> TwinDock does not use its name, logo, wordmarks or truck branding.

## Repo layout

| Path | What |
|---|---|
| `firmware/` | Simplicity Studio project (WiSeConnect SDK, C) |
| `backend/` | FastAPI + aiomqtt: world state, movement engine, WebSocket hub |
| `frontend/` | Vite + React + TS + React Three Fiber: `/twin`, `/control` (phone) and `/device` |
| `shared/` | `schema.md` and JSON Schemas for every MQTT and WebSocket message |
| `broker/` | Mosquitto config |
| `tools/fake_board.py` | **Development-only** board simulator |
| `HARDWARE.md` | Verified inventory of the physical board |

## Status

| Step | State |
|---|---|
| 0. HARDWARE.md | Done (SDK-verified; a few physical checks open) |
| 1. Scaffold + contract | Done |
| 2. Firmware | Not started |
| 3. Backend world engine | Done (verified end to end with the fake board) |
| 4. 3D scene | Done |
| 5. HUD (`/twin`) | Done |
| 6. Control Room (`/control`) | Done |
| 7. Board twin | Blocked: needs `frontend/public/board/top.jpg` and the hotspot table in HARDWARE.md |
| 8. BLE tags as live forklifts | Done; zones need on-site calibration at `/device` |
| 9. Demo hardening | Done: [DEMO.md](DEMO.md), reset button, data audit, 15-minute soak (60 fps throughout, no memory growth; Apple M1) |

## Running

### Prerequisites

- Mosquitto: `brew install mosquitto`
- Python 3.11+ (the Homebrew Python on the dev Mac is currently broken, so we use python.org 3.13):
  ```sh
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -m venv .venv
  .venv/bin/pip install -r tools/requirements.txt -r backend/requirements.txt
  ```

### 1. Broker

```sh
./scripts/run_broker.sh
```

It listens on `0.0.0.0:1883` so the board can connect over the LAN. The script prints the laptop's IP;
put that in the firmware config. Watch traffic with:

```sh
mosquitto_sub -v -t 'twin/#'
```

### 2. Board

Either flash the real firmware (see `firmware/`, coming in step 2) or, **for development only**:

```sh
.venv/bin/python tools/fake_board.py
```

The fake board prints a FAKE BOARD banner and sends `board: "FAKE"`, `fw_version: "fake"`. The backend
marks the gateway as fake and the UI shows a FAKE BOARD banner. Type `b0`/`b1` to press buttons,
`h0`/`h1` to hold, `off 20` to simulate a 20 s Wi-Fi drop (buffer + flush), `q` to quit.
It validates every payload against `shared/schemas/mqtt` before sending. **Never use it in the demo.**

Note: the fake board's retained `hello` stays in the broker. Before a demo, clear it with
`mosquitto_pub -r -n -t twin/gateway/hello` and let the real board publish its own.

### 3. Backend

```sh
./scripts/run_backend.sh          # http://localhost:8000, WebSocket at ws://localhost:8000/ws
(cd backend && ../.venv/bin/python -m pytest -q)
```

| Endpoint | What |
|---|---|
| `GET /api/layout` | Static geometry and waypoint graph (`backend/world/layout.json`) |
| `GET /api/snapshot` | Same payload as the WebSocket `world_snapshot` |
| `POST /api/reset` | Restore the seed world (board data is kept: it is real) |
| `GET /api/health` | Broker connection, board online/fake, client count |
| `WS /ws` | Messages in `shared/schema.md` |

How it works, in `backend/twindock/`:

- `engine.py` is the single source of truth. Client intents, MQTT messages and 20 Hz ticks all go
  through it; it validates every message against `/shared/schemas` and queues outgoing messages.
- `world.py` holds the units and the movement engine: shortest paths on the waypoint graph
  (`graph.py`), forklift 2.2 m/s, truck 3 m/s (1.2 m/s backing into a bay), smooth heading,
  move validation (trucks only to docks/gate, one truck per dock, no picking a carried or
  claimed pallet, one forklift per charger, low battery).
- `gateway.py` keeps board state built only from real messages, each with its receive time;
  offline after 15 s without status. Hardware is limited to `hardware.py` (= HARDWARE.md).
- Physical controls: BTN1 short press selects the next forklift on every screen; BTN0 short press
  runs the selected forklift's next task-list step (refilled by the planner when empty).
  LED0 follows "truck docked at Bay 1"; LED1 is commanded from clients and is only shown on
  after the board confirms.
- `planner.py` is auto mode (off by default): unload inbound trucks to Zone A, put away to the
  racks, load outbound trucks, send full trucks away and bring them back. Units it moves are
  `source: "auto"`.

#### Demo time scale

The world runs at real speed (forklift 2.2 m/s, truck 3 m/s) but some processes are compressed
so they are visible in a few minutes: forklift battery drains and charges about 20x faster than
a real shift (`backend/twindock/world.py`), with a 15% floor so no forklift can strand at 0%
mid-demo; auto-mode trucks return 20 s after leaving (`planner.py`). Board data is never scaled.

Seed: TR-01 is docked at Bay 2 and TR-02 waits on the road, so Bay 1 (and LED0) start free/off.

### 4. Frontend

```sh
cd frontend && npm install && npm run dev    # http://localhost:5173 (proxies /api and /ws to :8000)
npm run gen:types                            # regenerate src/contract/generated.ts after a /shared change
```

- Message types are generated from `/shared/schemas` and every WebSocket message is validated
  at runtime with ajv against the same files the backend uses (`src/contract/`).
- The store (`src/store/`) only changes on server messages; clicks send intents. Units glide
  towards each 20 Hz server position (critically damped, never extrapolated).
- The scene (`src/scene/`) is procedural low-poly: cutaway warehouse (walls facing the camera
  drop to a kerb so the floor stays visible from all four 90° views), roll-up doors D1–D3 that
  open while a truck is docked, racks, instanced pallets, forklifts, box trucks, office, fence
  and gate, trees, containers, and the gateway pole with its violet BLE ring (bright only
  while the board is online). Static scenery is merged per material (~230 draw calls in total).
- Controls: drag to pan, wheel or +/− to zoom (0.6x–2x), rotate in 90° steps, home/center.
  Click a unit to select it on every screen; `?stats` shows FPS and exposes renderer stats.
