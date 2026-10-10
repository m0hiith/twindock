# Site twin: plan for SITE_PROMPTS.md S0 (foundation)

Written before the code, as the plan S0 asks for. It covers the `/shared` contract changes, the
backend, the simulator and the frontend. Decisions taken without review are also listed one per
line in `DECISIONS.md`.

## Shape of the world

- **One world, two sites.** FAC-01 "Riverside Assembly" sits physically next to WH-01, east of
  it (x ≈ 86–142 m), in the same metre grid and the same waypoint graph. A forklift lane runs
  from an opening in the warehouse's east wall (by Zone B) to the factory's outbound pallet spot.
  So "finished units become pallets that forklifts carry to the racks" (S2) uses the existing
  movement engine and planner, not a second world.
- The **site selector** (top bar) is local view state, like the camera: it moves the camera to
  the site and scopes site-specific panels. It does not change server state, so two screens can
  look at different sites.
- `backend/world/layout.json` stays the single geometry file (version `riverside-2`). It gains
  the factory building, cold room, factory office, production line spots, the link lane and
  walkway nodes. `backend/world/sites.json` describes the **sites, zones and commissioned
  devices** (ids, type, zone, position, what each is mounted on).

## Contract changes (`/shared`)

`shared/schemas` stays authoritative; `shared/schema.md` and CLAUDE.md are updated in the same
commit.

| File | Change |
|---|---|
| `ws/defs.json` | `unit_id` pattern relaxed to 1–3 letters (`M-01` machines). `source` gains `sim`. `kind` gains `machine`, `worker`. New `site_id`, `device_id`, `zone_id`, `site`, `zone`, `device`, `device_type`, `protocol`, `device_status`, `reading`. |
| `ws/world_snapshot.json` | New required `sites` (with zones) and `devices`. |
| `ws/device_update.json` | **New** server → client: changed devices (status, readings, battery, last seen), at most 2 Hz. |
| `ws/select_unit.json` | Unchanged shape; the id may now also be a device id (same pattern). |
| `mqtt/site_hello.json` | **New** retained `twin/<site>/<device>/hello`: `{type, protocol, capabilities[], fw_version, source}`. Like the board's hello. |
| `mqtt/site_status.json` | **New** `twin/<site>/<device>/status`: `{ts_ms, battery_pct?, rssi_dbm?, fault?, source}`. |
| `mqtt/site_reading.json` | **New** `twin/<site>/<device>/<channel>`: `{ts_ms, value, unit?, source}`. |

`source` on every `twin/<site>/…` payload is the constant `"sim"`: nothing on these topics can
claim to be device data. Real devices other than GW-01 do not exist yet; when one does, it
gets its own schema change.

### Device model

`Device {id, site_id, zone_id, type, protocol, capabilities[], x, z, battery_pct?, fw_version?,
rssi_dbm?, last_seen_ms, source: device|sim, status: online|stale|offline|fault, readings{},
label?, attached_to?}`

Types now: `gateway`, `machine_monitor`, `env_sensor`, `door_sensor`, `occupancy_sensor`,
`badge`, `asset_tag`, `power_meter`, `light`, `air_quality`. Protocols: `wifi`, `ble`,
`thread`, `matter`.

**Staleness** (same 15 s rule as the board): online while the last message is at most 15 s
old, stale up to 60 s, offline after that or if never seen, fault while the device reports a
fault. GW-01 uses the age of the board's last status, exactly as `gateway.online` does.

## The real board stays untouched

- GW-01 is not stored in the device registry. Its device entry is **derived** on every
  snapshot from `GatewayStore` (the board's own messages). Its topics (`twin/gateway/*`),
  handlers and tests do not change.
- The bridge subscribes `twin/#` once, and the engine dispatches on the prefix: `twin/gateway/`
  goes to the existing board code, `twin/<SITE>/<DEV>/<channel>` goes to the device registry.
  The site id pattern (`^[A-Z]{2,4}-[0-9]{2}$`) can never be `gateway`.
- The registry **rejects** any site-topic message for a device whose registered source is
  `device` (GW-01): logged as a warn event and dropped.
- Registry code has no reference to `GatewayStore`, LEDs or `MqttOut`. A test feeds every kind
  of sim message, including ones that name GW-01, and asserts the gateway state, LED state and
  outgoing MQTT are byte-identical before and after.

## Simulator: `tools/site_sim.py`

One process, `paho-mqtt`, the same broker. It reads `backend/world/sites.json` and
`backend/world/layout.json`, so device ids and positions come from the commissioned list.

- `--zones production,cold_room` (default: every zone with sim devices), `--site FAC-01`.
- It publishes retained hello, status every 10 s and readings at each type's rate. Device
  models live in `tools/sim_models.py` so tests can import them.
- It refuses to publish for any device whose `source` is `device`, and never touches
  `twin/gateway/…`.
- Stopping it (Ctrl-C) just stops publishing. The retained hellos stay, so the devices go
  **stale, then offline**, which is the honest outcome.
- `fw_version` is `sim-x.y`.

## Frontend

- Contract types regenerated, then `sites` and `devices` in the world store, plus a local
  `site` view state.
- Top-bar site selector lists WH-01 and FAC-01. Picking one flies the camera to that site.
- 3D: factory building (same red ribbed cutaway walls), cold room block, factory office,
  floor zones, link lane, and the warehouse east-wall opening.
- `SimBadge` (grey "SIM") next to `LiveBadge` (violet "LIVE"). Protocol labels read
  "SIM · Thread", "LIVE · Wi-Fi".

## CLAUDE.md

New section "Site twin" with the four rules from S0, plus the topic layout and the GW-01
protection above.

## Tests (S0)

- Model validation: `sites.json` and every device validate; snapshot with sites/devices
  passes `ws/world_snapshot.json`.
- Topic parsing: valid, wrong site id, `twin/gateway/...` not parsed as a site topic, bad
  channel.
- Staleness: a sim device goes online → stale (15 s) → offline (60 s); a fault flag wins.
- Isolation: sim messages (including ones naming GW-01) never change gateway state, LED
  state, or produce MQTT output; GW-01's device entry follows only the board's status.
