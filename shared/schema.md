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
- IDs: units `FL-01`, `TR-01`, `PL-01`, `GW-01`, `M-01` (machine), `WK-01` (worker); devices `GW-01`, `MM-01`, `EN-01`, `BG-01`; sites `WH-01`, `FAC-01`; graph nodes `DOCK_1`, `RACK_A3`, `CHARGER_C1`, `GATE_IN`.
- Every unit has `source`: `device` | `manual` | `auto` | `sim` (machines and workers of the simulated site).
- Devices (`ws/defs.json#/$defs/device`) have `source`: `device` (GW-01, the real board) | `sim`.
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

### Hardware wiring

`schemas/hardware/wiring.json` validates every device kit, `hardware/kits/<kit_id>.json`: the single
source of truth for one asset's sensor pack (parts, buses, I2C addresses, pins, wires, evidence,
status and bill of materials). It is not a message. `GET /api/kits` lists the kits (summary with the
devices built from each), `GET /api/kits/<id>` serves one validated file to `/wiring/<id>`, and
`GET /api/wiring` is the FL-01 kit (`fl01_sensor_pack`). See HARDWARE.md.

- `kit {id, name, asset_type, status, radio, power_source, mounting, purpose, ...}`: `status` is
  `built` (real hardware: only the FL-01 pack) or `reference` (real parts and a correct wiring plan,
  simulated data). Every wiring page shows "Built and verified" or "Reference design · simulated".
- `bom[]`: part number, manufacturer, quantity, approximate unit cost, link and `source`
  (`datasheet`, `silabs.com`, `unverified`); `covers` lists the `parts` ids each line supplies.
- A device in `backend/world/sites.json` names its kit with `kit` (one design, many devices); it
  also appears on the `device` object in snapshots.
- `backend/twindock/wiring.py::validate_kit` checks every kit: no pin driven twice, no I2C address
  clash per bus (runtime address when firmware moves a part), supply voltage inside each part's
  range, and every BOM line used in the wiring and every part in the BOM.

- Parts and connections each carry `status`: `planned`, `wired` (on-board parts and PCB traces are
  wired by the board itself), `verified` (firmware has read a plausible value; never set by hand
  before that).
- Each part has a plain-language `caption` for non-engineers.
- `board_drawing` (optional; kits without a photographed dev board omit it) is the board outline from UG581 Figure 1.1 (30.4 × 55.0 mm, feature boxes and the
  26 breakout pads as % of the board). The page draws it until `frontend/public/board/top.jpg`
  exists, then overlays the photo; a part's `outline_pct` (measured on the photo) wins over it.
- Live readings are not in this file: the page takes them from `gateway.sensors` (gateway_update).

### Simulated site devices (`twin/<site>/<device>/<channel>`)

Published by `tools/site_sim.py` only. Site ids match `^[A-Z]{2,4}-[0-9]{2}$` (WH-01, FAC-01), so
they can never collide with `twin/gateway/…`. Every payload has `source: "sim"` (a schema
constant); `fw_version` is `sim-x.y`.

| Topic | Schema | Notes |
|---|---|---|
| `twin/<site>/<device>/hello` | `mqtt/site_hello.json` | Retained. Type, protocol and capabilities must match the device's entry in `backend/world/sites.json`. |
| `twin/<site>/<device>/status` | `mqtt/site_status.json` | Every 10 s: battery, signal, fault. |
| `twin/<site>/<device>/<channel>` | `mqtt/site_reading.json` | One reading on a channel listed in the hello's `capabilities`. A badge's `position` value is `[x, z]`. |
| `twin/<site>/<device>/cmd/<action>` | `mqtt/site_cmd.json` | Backend → simulator only (never GW-01): `degrade`, `restore`, `maintenance` (machine monitors), `door_open`, `door_close`, `route` (badges), `silence`. |

The backend drops (with a warn event, once per device and reason) messages for devices that are
not commissioned, that name a real device (GW-01), whose hello disagrees with commissioning, or
whose channel is not a capability. Same staleness as the board: online ≤ 15 s, stale ≤ 60 s,
then offline.

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
| `event` | `ws/event.json` | Event-log notices: BTN0/BTN1 actions, auto mode, LED confirmation timeouts, dropped device messages, BLE tag acquired/lost. |
| `ble_tracks` | `ws/ble_tracks.json` | After each `twin/gateway/ble` message and when a tag is lost. Per tag: last and smoothed RSSI, raw and committed zone, pending zone. Feeds the /device calibration helper. |
| `device_update` | `ws/device_update.json` | At most 2 Hz: devices whose status, readings, battery or signal changed. `world_snapshot` carries all `sites` (with zones) and `devices`. |
| `production_update` | `ws/production_update.json` | On connect and ≤ 1 Hz: FAC-01 machines (state, cycle, current, vibration, learned baseline, z, abnormal, OEE parts) and the line (units, pallets, zone OEE). |
| `safety_update` | `ws/safety_update.json` | On connect and ≤ 2 Hz: workers (role, badge, zone, nearest moving forklift, restricted zone; **no names**), workers per zone, today's counters. |
| `alerts_update` | `ws/alerts_update.json` | On connect and on every raise/acknowledge/resolve: open alerts (critical first) + recently resolved, and every rule from `backend/rules/*.yaml`. |
| `control_update` | `ws/control_update.json` | On connect and on change: work orders (bearing change, leak fix, compressor service) with state, cause, technician and result; recommendations waiting for a person (stop a machine, call emergency services); the last automatic actions as cause → action → result; whether loads are shed; the leak flow measured at the last break. |
| `logistics_update` | `ws/logistics_update.json` | On connect and ≤ every 2 s: logistics KPIs from the event log (dock-to-stock, turnaround, on-time dispatch, arrivals on schedule, forklift utilisation), each truck's stage (off site, gate, weighbridge, queue, dock, paperwork, leaving) with weighbridge weights, finished-goods orders, recent weighbridge tickets, inventory by SKU group and place, the raw material reorder position, forklift batteries in Ah. Simulated (auto mode). |
| `sim_clock` | `ws/sim_clock.json` | On connect, on a speed change and every 5 simulated s × speed: simulated time (`sim_ms`, the same clock as every `server_ts_ms`), speed (1, 5, 20), the warm start (simulated and wall seconds, seed) and `speed_locked` (why only ×1 is allowed now: the real board is online). |

### Client → server

| type | Schema | Validation |
|---|---|---|
| `move_unit` | `ws/move_unit.json` | Optional `pallet_id` for `pick`. Unit exists, is not `device`-sourced, target allowed for its kind (truck: docks/gate only), path exists, dock holds one truck, pallet not already carried. `dry_run` returns the path only. |
| `select_unit` | `ws/select_unit.json` | Unit exists (or null to clear). |
| `led_command` | `ws/led_command.json` | LED is in `hello.leds`; LED0 is rule-driven (Bay 1) and rejected. Forwarded to `twin/gateway/cmd/led`. |
| `set_auto_mode` | `ws/set_auto_mode.json` | — |
| `control_decision` | `ws/control_decision.json` | A person approves or dismisses an open recommendation (`rec_id`, `decision`, `by`). Approving a machine stop dispatches the technician; nothing that stops production happens without it. |
| `set_sim_speed` | `ws/set_sim_speed.json` | Speed 1, 5 or 20. Anything but 1 is refused while the real board is online, and a board coming online resets the speed to 1: board data always runs on real time. |
| `machine_command` | `ws/machine_command.json` | Machine exists. Forwarded to the simulator (`degrade`, `restore`, `maintenance`); never to the board. |
| `ack_alert` | `ws/ack_alert.json` | Alert is open and not yet acknowledged. `by` is the screen's name (no sign-in). |
| `scenario_command` | `ws/scenario_command.json` | Demo runner beats (`degrade`, `near_miss`, `visitor`, `cold_door`, `stale`, `reset`); simulator and engine only. |

### BLE tags as live forklifts

A tag named `TD-FL01` is forklift `FL-01`. The backend averages each tag's last `window` RSSI
readings and maps the average to a zone using `backend/world/ble_zones.json` (nodes nearest
first, each with a `min_rssi_dbm`). A zone is committed only after it has been the answer for
`stable_s` seconds. On the first committed zone the forklift becomes `source: "device"` and drives
to that node; manual commands, BTN0 and auto mode then leave it alone. A tag unseen for
`lost_after_s` hands the forklift back to `manual`. Empty `zones` = tracking off.

### Gateway state (inside snapshot and updates)

`ws/defs.json#/$defs/gateway`: each value is wrapped as `{data, received_ms}` or is `null` if never
received. `online` is false when the last status is older than 15 s. LEDs carry the last
**confirmed** `on` plus a `pending` command, so the UI can show "pending" between the click and
the board's confirmation.

### Kit devices (FACTORY_PROMPTS.md K2)

Device types added for the reference kits: `truck_telematics` (speed_kmh, door_open, cargo_temp_c,
harsh_event), `dock_bay` (occupied, door_position, leveler, dock_light), `conveyor_monitor`
(motor_current_a, belt_speed_m_s, jam), `compressor_monitor` (pressure_bar, current_a, run_hours,
dew_point_c), `helmet_clip` (worn, impact_g), `gas_detector` (co_ppm, o2_pct, alarm), `leak_sensor`
(wet), `tank_level` (level_pct, pump_on), `fire_panel` (alarm, trouble); `power_meter` (power_kw,
energy_kwh, voltage_v) and `asset_tag` (find_me) now have simulator models. Simulator commands:
`jam`, `leak`/`clear`, `alarm`/`reset`, `find_me` (see `mqtt/site_cmd.json`). All `source: "sim"`.

R1 (utilities): `compressor_monitor` adds `loaded`, `power_kw` (computed from current), `flow_nm3_min` (estimated:
rated FAD while loaded) and `discharge_c`; CP-02 is the standby compressor. `power_meter` adds `power_factor`
(omitted while the meter sees no load); PM-08 meters the rooftop solar. New type `genset_controller` (GS-01, kit
`genset_bridge`, reads the generator's existing AMF controller): `engine_state` (off, start_delay, cranking,
accelerating, running, cooldown), `rpm`, `coolant_c`, `fuel_lph`, `load_kw`, `transfer` (mains, open, generator),
`mains_ok`. New simulator commands for the air system: `fix_leaks`, `service` (used by work orders, R5).

R2 (production): machine monitors report `state` as running, starved, blocked, setup, planned_stop, fault
(breakdown or minor stop; `alarm` says which) or maintenance. `production_update` machines carry `losses` (OEE losses
in seconds, folded from the machine's event log) and `iso_zone` (ISO 10816-1 class I zone of recent running
vibration); the line carries `blanks_used` (parts the presses made). Simulator commands `feed` (a raw pallet at the
press infeed, `units` blanks) and `repair` (a work order fits a new bearing, `seconds`).

### Worker safety (FACTORY_PROMPTS.md K3)

`safety_update` now also carries per worker: `prealert` (fall / no_motion, with the cancel deadline), `man_down`,
`sos_ms`, `evacuate`, `lone`, `zone_overtime_min`, `first_aider`, `nearest_first_aider`, `mustered`, `location_shown`,
and overall `evacuation` (headcount: on site, accounted, by muster point, unaccounted with last known zone), `on_site`,
`in_hazardous`, `gas_zones`, `heat_zones`, `ppe_reminders`, `breaks_due`, `privacy`.
`safety_command` (client → server): `start_evacuation`, `end_evacuation`, `clear_incident`, and demo actions
`sim_fall|sim_cancel|sim_sos|sim_checkin|sim_still` that drive a SIMULATED badge only.
Badge messages (sim badges, same path for a real one): channels `fall`, `sos`, `cancel`, `checkin`.
Zones may carry `hazard`, `ppe`, `time_limit_min`, `lone_worker`, `checkin_min`. `GET /api/safety/me/<worker>` is the
worker's own data; `GET /api/safety/shift` the supervisor's shift overview. Hours and break details are never broadcast.
Privacy: positions appear on screens only while that worker has an active safety condition or an evacuation runs
(otherwise the worker is drawn at their zone and the badge's `position` reading is withheld); nothing is tracked
off site (outside every site's bounds) or off shift (no data for 30 min ends the shift); PPE reminders are never
recorded or tied to an id; incident history is deleted after `privacy.retention_days`.
