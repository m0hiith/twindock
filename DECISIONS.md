# Decisions

One line each, newest at the bottom, made during unattended runs. Each says what was decided and why.

## Stage 0: housekeeping
- HARDWARE.md SDK row now says WiSeConnect 4.1.1 on Simplicity SDK 2026.6.1; the 3.5.3 copy stays in the repo (gitignored) for reference only.
- The NWP firmware update is recorded as an **open** row and open item, not "confirmed", because nobody has done it on the board yet.

## Stage 1: S0 foundation
- FAC-01 sits east of WH-01 in the same metre grid and waypoint graph (one engine), so production pallets can reach the warehouse racks on real lanes.
- The site selector is local view state (like the camera), not shared server state: two screens may watch different sites.
- `layout.json` stays the single geometry file (now `riverside-2`); `sites.json` holds sites, zones and commissioned devices.
- GW-01 is never stored in the device registry; its device entry is derived from GatewayStore on every read.
- Every `twin/<site>/…` payload has `source: "sim"` as a schema constant: nothing on site topics can claim to be real.
- The bridge subscribes `twin/#` once (not two overlapping subscriptions) and the engine routes by prefix.
- Device status: online ≤ 15 s (board rule), stale ≤ 60 s, then offline; fault wins.
- `unit_id` relaxed to 1–3 letters so machines can be `M-01` as SITE_PROMPTS.md names them; `source` gains `sim`, `kind` gains `machine` and `worker`.
- Badge positions are a reading whose value is `[x, z]` rather than two separate channels, so x and z never tear.
- Unknown or rejected sim messages produce one warn event per device and reason, so the event log is not flooded.
- Backend MQTT client id is configurable (`TWINDOCK_MQTT_CLIENT_ID`) so a second backend can run beside the user's without kicking it off the broker.
- The warehouse got an east-wall opening and the link lane runs between Zones B and C (z = 18.8), so forklifts never drive through Zone B pallets.

## Stage 2: S1 Fleet page
- Frontend tests run with `node --test` and Node 26's built-in TypeScript type stripping (`npm test`); no test framework dependency added.
- Fleet sort: real devices first, then by worst problem (fault, offline, stale, low battery), then id.
- Device history for the side panel comes from `GET /api/devices/{id}/history` (backend keeps the last 240 values per channel); GW-01's history is only the RSSI values from the board's own status messages.
- GW-01 battery shows "—", not "Mains": nothing in the board's messages says how it is powered. Simulated Wi-Fi devices show "Mains".
- On the twin page, the warehouse KPI, shipment and fleet panels show only while WH-01 is the site on screen; FAC-01 shows a device-health card instead of misleading warehouse numbers.
- Device pucks are hidden by default (map control "Devices", or `?devices` in the URL); GW-01 has no puck because its pole already marks it.
- A device can be the shared selection (`select_unit` accepts a device id); the inspect card then shows the device with every reading's age.

## Stage 3: S2 production line
- Machine physics (states, cycles, current, vibration, degrade) lives in the simulator; baseline learning, z-score, OEE and pallets live in the backend, the way a real twin would analyse real monitors.
- Machines are units (`M-01`, `M-02`, kind `machine`, source `sim`). With no fresh monitor data their state is `no_data`, never a guessed "running".
- Baseline: learned from running-state readings only, over 90 s and at least 40 readings. z = (mean of last 10 readings − baseline mean) / baseline std; raise above 3.0, clear below 2.0 (hysteresis). Configurable in `sites.json` → `production`.
- "Degrade" adds +0.015 mm/s per second (a worn bearing): it is flagged about 30–60 s after the click, visible on cue but not instant.
- OEE per machine: A = running/planned (planned = time with data, excluding maintenance), P = ideal cycle × units/running time (capped at 1), Q = good/all. Zone OEE = mean A × mean P × product of Q.
- A machine's units counter is counted from the first reading the backend sees (the simulator may already be running), so a backend restart starts "units today" at 0.
- Every 6 packer units become one finished pallet (`FG-xx`, source `sim`) at the factory outbound spot. If the spot is full, pallets wait (counted) and one warn event is raised.
- Finished pallets leave the world when their truck departs (delivered); other cargo still comes back with the truck as before. This keeps pallet counts and ids bounded.
- Auto mode gains a "collect production" job (outbound spot → rack slot, else staging), after unload/load in priority.
- Simulator commands go on `twin/<site>/<device>/cmd/<action>` (schema `mqtt/site_cmd.json`), only for sim devices (asserted in the engine).
- The Control Room map still shows WH-01 only; FAC-01 controls are in a new "Factory" tab.
