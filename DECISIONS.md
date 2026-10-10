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

## Stage 4: S3 worker safety
- Workers walk named routes of layout nodes (forklift lanes and walker-only `WALK_*` nodes with no mover kinds), looping, pausing 5–18 s at work stands. Routes live in `sites.json`.
- Proximity counts only forklifts moving faster than 0.2 m/s. Warning < 3 m, critical < 1.5 m, cleared above 3.5 m (0.5 m hysteresis) or when the forklift stops. Evaluated 4×/s.
- A badge that isn't fresh (> 15 s) claims nothing: no proximity, no restricted alert, and the worker isn't drawn.
- The press area is a sub-zone of Production (listed after it; the last matching zone wins). Restricted: press area (press operators, maintenance, supervisors), cold room (logistics, supervisors).
- Privacy: no worker names on the wire at all; the demo has no sign-in, so nobody is an "authorised user". Names stay only in `sites.json`.
- Real path: a tag named `TD-BADGE-01` seen by the real board's BLE scan is the commissioned real device `RB-01` (LIVE). Its RSSI, last seen and calibrated zone come from the existing BLE tracker. It is not in the proximity rule until zones are calibrated, because without a position it can't honestly be near anything.
- The simulator advances simulated time by `dt` (not wall clock), so tests are fast and deterministic.

## Stage 5: S6 rules and alerts
- Alerts come only from `backend/rules/*.yaml`: production, safety, devices and gateway files. Each rule has a plain-language sentence for `/rules`.
- Migrated: machine fault, abnormal vibration, outbound full, proximity warning and critical, restricted zone. The production and safety modules now only compute state and counters; they no longer emit alert-like events.
- Not alerts, still plain events: LED confirmation timeouts, dropped device messages, BLE tag changes. They are command or diagnostic outcomes, not conditions that stay true.
- Impact (sensor pack) has no rule: that sensor is gated and not built. Dock-door rules wait for S4. Cold-room door and temperature and CO₂ rules were added because those devices already exist (S0).
- A missing or stale value never satisfies a clause, so no alert is ever raised on data that didn't arrive; device readings count only while the device is online.
- Gateway offline fires only after the board has been online since the backend started: a board that was never seen is "Waiting for device", not a critical alert.
- The alert message is rendered when the alert is raised (e.g. "6.6 °C"); the panels show the live value elsewhere.
- Acknowledged by: there is no sign-in, so the screen names itself ("Control Room", "Twin", "(phone)" under 640 px wide), and that name is shown to everyone.
- Rules are evaluated at 2 Hz; open alerts are sorted critical first, then newest; the last 30 resolved are kept for the panels.
