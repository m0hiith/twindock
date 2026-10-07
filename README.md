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
| `frontend/` | Vite + React + TS + React Three Fiber: `/twin` and `/control` |
| `shared/` | `schema.md` and JSON Schemas for every MQTT and WebSocket message |
| `broker/` | Mosquitto config |
| `tools/fake_board.py` | **Development-only** board simulator |
| `HARDWARE.md` | Verified inventory of the physical board |

## Status

| Step | State |
|---|---|
| 0. HARDWARE.md | Draft, waiting for the SDK and developer checks |
| 1. Scaffold + contract | Done |
| 2. Firmware | Not started |
| 3–9. Backend, 3D, HUD, Control Room, board twin, BLE, demo | Not started |

## Running

### Prerequisites

- Mosquitto: `brew install mosquitto`
- Python 3.11+ (the Homebrew Python on the dev Mac is currently broken, so we use python.org 3.13):
  ```sh
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -m venv .venv
  .venv/bin/pip install -r tools/requirements.txt
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

### 3. Backend and frontend

Coming in steps 3–7.
