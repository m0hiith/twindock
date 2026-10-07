# TwinDock message contract

This is the single definition of every message in the system. The JSON Schemas in
`schemas/mqtt/` and `schemas/ws/` are authoritative; this page explains them.
The backend (pydantic) and frontend (TypeScript) both validate against these files.

## Conventions

- Times: `ts_ms` is **board** time (ms since boot, or epoch ms once SNTP is available).
  `received_ms`, `server_ts_ms` and `sent_ms` are **backend** epoch ms. The UI computes ages
  ("12s ago") from `received_ms`, never from `ts_ms`.
- Coordinates: meters, origin at the warehouse NW corner, `x` east, `z` south.
  `heading_rad` 0 = facing east, increasing towards south.
- IDs: units `FL-01`, `TR-01`, `PL-01`, `GW-01`; graph nodes `DOCK_1`, `RACK_A3`, `CHARGER_C1`, `GATE_IN`.
- Every unit has `source`: `device` | `manual` | `auto`.
- **No board value is ever defaulted.** A device field that has never arrived is `null` (or absent),
  and the UI shows "Waiting for device".

## MQTT (board <-> broker)

| Topic | Dir | Schema | Notes |
|---|---|---|---|
| `twin/gateway/hello` | board → | `mqtt/gateway_hello.json` | Retained. LED/button/sensor lists must match HARDWARE.md. |
| `twin/gateway/status` | board → | `mqtt/gateway_status.json` | Every 5 s. Fields the SDK can't give are omitted. Buffered replays keep their original `ts_ms` and set `replay: true`.\*\* |
| `twin/gateway/button` | board → | `mqtt/gateway_button.json` | On each debounced change. |
| `twin/gateway/led` | board → | `mqtt/gateway_led.json` | Confirmation of real LED state. Optional `cmd_id` echoes the command that caused it.* |
| `twin/gateway/ble` | board → | `mqtt/gateway_ble.json` | Every 2 s, names starting `TD-` only. |
| `twin/gateway/sensor/<name>` | board → | `mqtt/gateway_sensor.json` | Only verified sensors. |
| `twin/gateway/cmd/led` | → board | `mqtt/gateway_cmd_led.json` | From the backend only. |

\* `cmd_id` on the LED confirmation is an addition to the table in CLAUDE.md. It lets the UI
clear exactly the pending command it belongs to. It is optional, so a confirmation caused by a
local rule (no command) is still valid.

\*\* `replay` is also an addition. Without it the backend cannot tell a flushed old sample from
a fresh one after a board reboot (both can have a small `ts_ms`). Replays count as "board reachable"
but never replace the current status.

### Fake board

`tools/fake_board.py` publishes the same topics with `hello.board = "FAKE"` and
`fw_version = "fake"`. The backend sets `gateway.fake = true` and the UI must show a FAKE BOARD
banner. Development only, never in the demo.

## WebSocket (`/ws`, backend <-> browsers)

Every message is a JSON object with a `type` field.

### Server → client

| type | Schema | When |
|---|---|---|
| `world_snapshot` | `ws/world_snapshot.json` | On connect (and after a reset). Full units + gateway + selection + auto mode. |
| `unit_update` | `ws/unit_update.json` | At most 20 Hz, only changed units. |
| `gateway_update` | `ws/gateway_update.json` | After each device message or online/stale change. Includes `raw` MQTT message for the log. |
| `selection_changed` | `ws/selection_changed.json` | When any client or BTN1 changes the shared selection. |
| `command_ack` | `ws/command_ack.json` | Reply to each client command (`ok`, `reason`, planned `path`). |
| `event` | `ws/event.json` | Event-log notices: BTN0/BTN1 actions, auto mode, LED confirmation timeouts, dropped device messages. |

### Client → server

| type | Schema | Validation |
|---|---|---|
| `move_unit` | `ws/move_unit.json` | Optional `pallet_id` for `pick`. Unit exists, is not `device`-sourced, target allowed for its kind (truck: docks/gate only), path exists, dock holds one truck, pallet not already carried. `dry_run` returns the path only. |
| `select_unit` | `ws/select_unit.json` | Unit exists (or null to clear). |
| `led_command` | `ws/led_command.json` | LED is in `hello.leds`; LED0 is rule-driven (Bay 1) and rejected. Forwarded to `twin/gateway/cmd/led`. |
| `set_auto_mode` | `ws/set_auto_mode.json` | — |

### Gateway state (inside snapshot and updates)

`ws/defs.json#/$defs/gateway`: each value is wrapped as `{data, received_ms}` or is `null` if never
received. `online` is false when the last status is older than 15 s. LEDs carry the last
**confirmed** `on` plus a `pending` command, so the UI can show "pending" between the click and
the board's confirmation.
