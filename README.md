# TwinDock

A browser-based digital twin of a small warehouse ("Riverside Logistics Hub"), driven by a real
Silicon Labs **SiWx917 Dev Kit (BRD2605A)** over Wi-Fi/MQTT, plus a phone-friendly Control Room for
moving forklifts and trucks by hand.

It is also a **site twin**: next to the warehouse (WH-01) sits a factory, FAC-01 "Riverside
Assembly", with a production line, a cold room and workers wearing BLE badges, so every kind of
IoT device appears in one live view. Those factory devices are **simulated** and labelled SIM
everywhere; the SiWx917 board stays the one real (LIVE) device.

> Design inspiration: the visual language is inspired by **Dilum Sanjaya's "WareTrack"** concept.
> TwinDock does not use its name, logo, wordmarks or truck branding.

## Architecture

```
SiWx917 board (REAL, GW-01) ──MQTT twin/gateway/*──┐
                                                    ├─► Mosquitto ◄──► backend (FastAPI)
tools/site_sim.py (SIMULATED devices) ──MQTT ───────┘     │  world + movement engine + planner
   twin/<site>/<device>/<channel>                         │  device registry (sites.json)
      ▲   twin/<site>/<device>/cmd/* (sim only)           │  production analytics, worker safety
      └───────────────────────────────────────────────────┤  rules engine (backend/rules/*.yaml)
   twin/gateway/cmd/led (board LED, real only) ◄──────────┤
                                                          ▼ WebSocket /ws
        /twin  3D view + HUD     /control  phone (move, factory, demo, alerts)
        /fleet every device      /rules    rules + alerts      /device  /wiring
```

The backend routes `twin/gateway/*` to the board code and everything else to the device registry,
which cannot reach the board's state, its LEDs or its commands (`backend/tests/test_sites.py`).

## Real or simulated

| What | Source | Badge |
|---|---|---|
| GW-01 (the SiWx917): status, RSSI, buttons, LEDs, sensors, BLE sightings | Real MQTT from the board | LIVE (violet) |
| RB-01: a phone advertising `TD-BADGE-01`, seen by the board's BLE scan | Real (through the board) | LIVE |
| Forklifts tracked by a calibrated BLE tag | Real (through the board) | LIVE |
| Warehouse units: trucks, forklifts, pallets, docks | Server world state (manual, auto) | none |
| FAC-01 machines (M-01 press, M-02 packer) and their monitors MM-01/02 | `tools/site_sim.py` | SIM (grey) |
| Workers WK-01…04 and badges BG-01…04 | `tools/site_sim.py` | SIM |
| Env, door, occupancy and air-quality sensors | `tools/site_sim.py` | SIM |
| OEE, vibration baselines, proximity, alerts | Computed by the backend from the above | — |

Every value on every page and its source: [docs/value_audit.md](docs/value_audit.md).

## Riverside Campus

WH-01 and FAC-01 are one campus (plan and ASCII map: [docs/campus_plan.md](docs/campus_plan.md)): main gate with
weighbridge, car park with EV chargers, admin block, canteen, first aid, raw material store, a manufacturing hall with two
lines, QC lab, maintenance workshop, utilities (substation, generator, compressor room, water tanks, ETP), a bunded
hazardous materials store, the fire pump house, hydrants, muster points and rooftop solar. Vehicles and people use separate
graphs that meet only at marked crossings. All of it is simulated (SIM) except GW-01.

```
 WAREHOUSE+yard ── gate/weighbridge ── FACTORY (2 lines) ── QC lab ── UTILITIES (substation, generator,
   (WH-01)           main road z=44        cold room         workshop    compressor, tanks, ETP)
 car park · admin · canteen · first aid · raw material store ── fire pump · HAZMAT (far south-east)
```

Pages: `/monitor` (control room wall display), `/energy`, `/kits`, `/wiring/:kit`, `/parts`, `/me/<worker>` (a worker's own data).
Four emergency scenarios run from `/control` → Demo: grid failure, gas leak, fire alarm, compressor fault.

## Device kits

One sensor kit per kind of asset, with a wiring page drawn from real part dimensions. **Only the FL-01 kit is built**
(SiWx917 BRD2605A); every other kit is a **reference design**: real, buyable parts and a correct wiring plan, with simulated data
(`source: "sim"`, never LIVE). Third-party values are marked *unverified* in each kit until checked against a datasheet.

| Kit | Asset | Radio (Silicon Labs) | Status |
|---|---|---|---|
| fl01_sensor_pack | Forklift | Wi-Fi 6 + BLE, SiWG917 | **Built** (real board) |
| truck_telematics, dock_bay, machine_monitor, conveyor_monitor, compressor_monitor, gas_detector_node, energy_meter, fire_panel_bridge, water_quality_node | Trucks, docks, production, utilities | Wi-Fi 6 + BLE, SiWG917 (mains or vehicle powered) | Reference design |
| worker_badge, smart_helmet_clip, pallet_asset_tag | People, pallets | BLE, EFR32BG27 / BG22 (battery) | Reference design |
| env_node, door_access, water_leak_node, tank_level_node | Building and environment | Thread, EFR32MG24 | Reference design |

Plan: [docs/kits_plan.md](docs/kits_plan.md). Credits and part graphics: [CREDITS.md](CREDITS.md).

## Privacy (worker safety)

- **Zone counts by default.** Screens show how many people are in each zone. A worker's position appears only while that worker has an
  active safety condition (a fall or SOS, a forklift too close, a restricted zone, a missed check-in, an evacuation order) or an evacuation is running.
- **No tracking off site or off shift.** Positions outside the site bounds are dropped; a shift starts at the first position on site and ends after 30 minutes
  without data.
- **Roles, never names.** Badges are identified by id and role. This demo has no sign-in, so names are not sent to browsers at all.
- **PPE reminders are not records.** A missing helmet gives the wearer a buzz, at most every 10 minutes; nothing is stored, counted per person or shown with an id.
- **Hours and breaks** are served only to the worker (`/me/<id>`) and the supervisor, never broadcast.
- **Retention.** Incident history (falls, SOS, closed incidents) is deleted after `privacy.retention_days` (30 by default, `backend/world/sites.json`).
- **Workers can see their own data** at `/me/<worker id>`.
- Safety features **advise**: TwinDock never closes, locks or silences anything, and the fire panel and gas nodes only add information next to certified systems.

## Hosted demo and deployment

TwinDock runs as **one always-on container** (`Dockerfile`: the built frontend, `/api` and `/ws` from one FastAPI
process with one worker), never as serverless functions: [docs/deploy_diagnosis.md](docs/deploy_diagnosis.md)
explains why the old Vercel deploy showed no factory data.

```sh
docker build -t twindock . && docker run --rm -p 7860:7860 twindock    # http://localhost:7860
```

Hosted on Hugging Face Spaces or Render it runs the simulated factory, says "Hosted demo" on every page, and starts by
fast-forwarding 45 simulated minutes. Click-by-click steps: [docs/deploy.md](docs/deploy.md); an always-on VM with a
broker and HTTPS: [docs/deploy_vm.md](docs/deploy_vm.md). The simulation itself:
[docs/sim_architecture.md](docs/sim_architecture.md), [docs/model_card.md](docs/model_card.md) and the `/model` page.

## Repo layout

| Path | What |
|---|---|
| `firmware/` | Simplicity Studio project (WiSeConnect SDK, C) |
| `backend/` | FastAPI + aiomqtt: world state, movement engine, WebSocket hub |
| `frontend/` | Vite + React + TS + React Three Fiber: `/twin`, `/monitor`, `/energy`, `/control` (phone), `/fleet`, `/rules`, `/device`, `/kits`, `/wiring/:kit` |
| `shared/` | `schema.md` and JSON Schemas for every MQTT and WebSocket message |
| `broker/` | Mosquitto config |
| `tools/fake_board.py` | **Development-only** board simulator |
| `tools/site_sim.py` | Simulator for every site-twin device (SIM), one process, with the campus physics (power, generator, compressed air) |
| `tools/kits/gen_reference_kits.py`, `tools/campus/gen_campus.py` | Generators for the reference kits and the campus layout (idempotent) |
| `hardware/kits/*.json` | One file per device kit (parts, pins, wires, bill of materials) |
| `backend/world/sites.json` | Sites, zones, commissioned devices, workers, production and safety settings |
| `backend/rules/*.yaml` | Every alert rule, in plain language too |
| `docs/` | `site_plan.md`, `kits_plan.md`, `campus_plan.md`, `value_audit.md`, `perf_report.md` |
| `HARDWARE.md` | Verified inventory of the physical board |

## Status

| Step | State |
|---|---|
| 0. HARDWARE.md | Done (SDK-verified; a few physical checks open) |
| 1. Scaffold + contract | Done |
| 2. Firmware | Steps A–D: written, builds, untested on hardware ([firmware/TESTING.md](firmware/TESTING.md)). Steps E–F: not started |
| 3. Backend world engine | Done (verified end to end with the fake board) |
| 4. 3D scene | Done |
| 5. HUD (`/twin`) | Done |
| 6. Control Room (`/control`) | Done |
| 7. Board twin | Blocked: needs `frontend/public/board/top.jpg` and the hotspot table in HARDWARE.md |
| 8. BLE tags as live forklifts | Done; zones need on-site calibration at `/device` |
| 9. Demo hardening | Done: [DEMO.md](DEMO.md), reset button, data audit, 15-minute soak (60 fps throughout, no memory growth; Apple M1) |
| Site S0 foundation (sites, zones, devices, simulator) | Done ([docs/site_plan.md](docs/site_plan.md)) |
| Site S1 Fleet page (`/fleet`) | Done |
| Site S2 Production line | Done (simulated) |
| Site S3 Worker safety | Done (simulated; real badges via the board's BLE once firmware Step E exists) |
| Site S6 Rules and alerts (`/rules`) | Done |
| Site S10 demo runner, value audit, performance | Done ([DEMO.md](DEMO.md), [RUN_REPORT.md](RUN_REPORT.md)) |
| Site S4, S5, S7, S8, S9 | Not started (roadmap, [SITE_PROMPTS.md](SITE_PROMPTS.md)) |

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

Either flash the real firmware (Steps A–D in `firmware/twindock_gw`, see [firmware/TESTING.md](firmware/TESTING.md)) or, **for development only**:

```sh
.venv/bin/python tools/fake_board.py
```

The fake board prints a FAKE BOARD banner and sends `board: "FAKE"`, `fw_version: "fake"`. The backend
marks the gateway as fake and the UI shows a FAKE BOARD banner. Type `b0`/`b1` to press buttons,
`h0`/`h1` to hold, `off 20` to simulate a 20 s Wi-Fi drop (buffer + flush), `q` to quit.
It validates every payload against `shared/schemas/mqtt` before sending. **Never use it in the demo.**

Note: the fake board's retained `hello` stays in the broker. Before a demo, clear it with
`mosquitto_pub -r -n -t twin/gateway/hello` and let the real board publish its own.

### 2b. Site simulator (SIM devices)

```sh
.venv/bin/python tools/site_sim.py                    # every simulated device
.venv/bin/python tools/site_sim.py --zones cold_room  # only some zones (id or kind)
```

The simulator is a cause-and-effect model of the campus (`backend/sim/`, explained in `docs/sim_architecture.md`):
machines draw air and power because they run, the compressor loads because pressure fell, and every number has a
source in `backend/sim/params/*.yaml`. The `/model` page lists every model, equation, parameter and simulated sensor.
It publishes on `twin/<site>/<device>/<channel>` with `source: "sim"` and `fw_version: "sim-x.y"`,
validated against `shared/schemas/mqtt/site_*.json`. It never touches `twin/gateway/*`. Stop it with
Ctrl-C: the devices then go stale (15 s) and offline (60 s) in the twin, which is the honest outcome.

If the backend can't reach a broker when it starts (the hosted container), it runs the same simulator in-process
(`TWINDOCK_SIM=auto`, the default; force with `embedded` or `external`). The SIM devices then report without
Mosquitto, and the Demo tab works. The real board (GW-01) and its badge (RB-01) still show "Waiting for device".
With the embedded simulator the backend first fast-forwards 45 simulated minutes (about 6 s) so the factory is already
running when the page opens (`TWINDOCK_WARM_START_MIN=0` turns this off). The top bar shows the simulation clock and
its speed (×1 real time, ×5, ×20); only ×1 is allowed while the real board is online.

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
| `GET /api/health` | Uptime, achieved tick rate, simulation clock and speed, warm start, SIM devices online, broker, board online/fake, clients |
| `GET /api/history?device=&channel=&range=15m\|1h\|shift` | Historian series (avg/min/max per bucket) for charts |
| `GET /api/history.csv?...` | The same as CSV (`raw=true`: every stored point) |
| `GET /api/report/shift.pdf?which=current\|previous` | Shift report PDF (`/api/report/shift` for its data) |
| `GET /api/model` | The simulation's model card (models, equations, parameters with sources, sensors) |
| `GET /api/devices/{id}/history?channel=` | Recent values of one device channel (fleet side panel) |
| `WS /ws` | Messages in `shared/schema.md` |

How it works, in `backend/twindock/`:

- `engine.py` is the single source of truth. Client intents, MQTT messages and 20 Hz ticks all go
  through it; it validates every message against `/shared/schemas` and queues outgoing messages.
- `world.py` holds the units and the movement engine: shortest paths on the waypoint graph
  (`graph.py`), forklift 2.2 m/s, truck 3 m/s (1.2 m/s backing into a bay), smooth heading,
  move validation (trucks only to docks/gate, one truck per dock, no picking a carried or
  claimed pallet, one forklift per charger, low battery).
- `traffic.py` keeps vehicles from touching each other or people: a forklift or truck may only
  drive onto nodes and lanes it has reserved (conflicting ones are worked out once from the real
  footprints), so it waits instead of driving into another unit. Head-on and parked blockers move
  aside or make way into a pocket and then resume their task; forklifts stop for a pedestrian on
  their lane. `tests/test_traffic.py` checks zero overlap over 10-minute auto-mode runs.
- `gateway.py` keeps board state built only from real messages, each with its receive time;
  offline after 15 s without status. Hardware is limited to `hardware.py` (= HARDWARE.md).
- Physical controls: BTN1 short press selects the next forklift on every screen; BTN0 short press
  runs the selected forklift's next task-list step (refilled by the planner when empty).
  LED0 follows "truck docked at Bay 1"; LED1 is commanded from clients and is only shown on
  after the board confirms.
- Site twin: `devices.py` (device registry, staleness, GW-01 derived from the board only),
  `production.py` (vibration baselines and z-score, OEE, finished pallets), `safety.py` (badge
  proximity to moving forklifts, restricted zones), `rules.py` (alerts from `backend/rules/*.yaml`:
  raised → acknowledged → resolved). Set `TWINDOCK_MQTT_CLIENT_ID` to run a second backend
  against the same broker.
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
npm test                                     # node --test: fleet logic + the LIVE/SIM audit
```

- Message types are generated from `/shared/schemas` and every WebSocket message is validated
  at runtime with ajv against the same files the backend uses (`src/contract/`).
- The store (`src/store/`) only changes on server messages; clicks send intents. Units glide
  towards each 20 Hz server position (critically damped, never extrapolated).
- The scene (`src/scene/`) is procedural low-poly: cutaway warehouse (walls facing the camera
  drop to a kerb so the floor stays visible from all four 90° views), roll-up doors D1–D3 that
  open while a truck is docked, racks, instanced pallets, forklifts, box trucks, office, fence
  and gate, trees, containers, and the gateway pole with its violet BLE ring (bright only
  while the board is online). Static scenery is merged per material (272 draw calls with both sites, device pucks and workers on; RUN_REPORT.md).
- Controls: drag to pan, wheel or +/− to zoom (0.6x–2x), rotate in 90° steps, home/center.
  Click a unit to select it on every screen; `?stats` shows FPS and exposes renderer stats.
