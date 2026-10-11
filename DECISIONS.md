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

## Stage 6: S10 items 2–4, DEMO.md, README
- Demo runner: one `scenario_command` per beat, run by the backend so every screen sees the same thing. Beats only send simulator commands and engine moves. The real-board beats are a manual checklist in the Demo tab, because nothing should trigger or fake them.
- The near-miss beat drives the nearest free forklift (not BLE-tracked, not carrying) to the factory outbound and sends WK-02 walking that lane. It refuses with a reason if no forklift is free.
- Reset demo = world reset + the simulator back to normal (restore machines, default routes, door closed, AQ-01 reporting) + today's safety counters cleared. Alert history is kept.
- The Demo tab has no "show on twin" button: camera and site are per-screen, so the phone can't move the projector.
- Value audit: a reviewed allowlist test (`frontend/src/audit.test.ts`) plus a backend test, instead of a one-off manual check, so the guarantee keeps holding after this run.
- Performance: the run is unattended and the Chrome window is hidden, so requestAnimationFrame is throttled and real-time fps can't be observed. Frame cost was measured instead, by stepping whole frames (every `useFrame` callback + render) with `advance()` and forcing a GPU sync with `readPixels` (a `?stats`-only hook). Under 16.7 ms per frame means 60 fps is achievable. The user should still confirm real fps by eye (RUN_REPORT.md).
- To pay for the factory, static conveyor and QC parts are merged (`Baked`) and device pucks don't cast shadows. The conveyor belt keeps its material, so its texture still scrolls.
- `shared/schema.md` and the CLAUDE.md contract summary now list every message added in S2–S10 (they had fallen behind `/shared/schemas` during stages 3–5).

## Traffic (user request after Stage 6: no collisions between forklifts, trucks or people)
- Collision prevention is reservation-based (`traffic.py`): a vehicle drives only onto waypoint nodes and lanes it holds, and a conflict map built from the real footprints (forklift 3.0 × 1.7 m, truck 10.8 × 3.1 m, 0.2 m margin) says which nodes and lanes can't be held at the same time. That rules out overlaps by construction, which the earlier speed-only "keep a gap" approach did not (gridlocks in 40% of random runs).
- Reservations are granted in priority order (loaded forklifts first, then trucks, then the lower id) and two steps ahead at most, so nobody locks a whole aisle.
- Entering a dead end (rack slot, dock, charger) is atomic: the vehicle only goes in if it can also reserve the way out, so it can't trap itself.
- Getting unstuck: a parked blocker moves aside after 1.5 s; after 2 s of a wait-for cycle one member makes way into the nearest free pocket and picks its task up again once the others have passed (or after 20 s); after 10 s a vehicle re-routes. Auto mode doesn't give new tasks to a vehicle that is making way.
- Pedestrians: a forklift stops when a worker stands on its lane ahead ("Stopped for a pedestrian"). Simulated workers walk 1.7 m beside forklift aisles (a walkway), still inside the 3 m warning radius, so S3's proximity alerts keep working.
- Layout changes for traffic: ROAD_IN (90, 41.5) so returning and waiting trucks stand on the inbound side, not on the exit lane; CHG_J moved east so a charging forklift doesn't block the charger lane; rack slots moved deeper into the racks so a forklift picking there leaves the aisle free; idle forklifts park only in zones, never on aisle junctions; one forklift per docked truck at a time.
- Verified: 60 random 10-minute auto-mode runs with no overlap > 0.15 m and no unit blocked for a minute (5 seeds are in the test suite). Some tests got longer timeouts because vehicles now wait for each other.
- README.md was found reverted to an old copy (no WareTrack credit, firmware "Not started"), changed outside this run on 2026-10-10 22:23. It was restored from git and the Stage 6 edits re-applied; the overwritten copy was not kept.

## Factory extension: K0 kit framework
- One schema (`shared/schemas/hardware/wiring.json`) extended with `kit` and `bom` instead of a second file; `board_drawing` became optional so kits on other boards need no photographed dev board.
- FL-01 moved to `hardware/kits/fl01_sensor_pack.json`; the content is unchanged apart from `kit` and `bom`. `/api/wiring` still serves it. `tools/gen_pins.py` does not exist in the repo, so nothing needed repointing.
- BOM lines `covers` the part ids they supply (a dev kit covers its on-board parts); validation requires every part covered exactly once and every covered id to exist.
- "Pin driven twice": a pin may fan out only for bus/ground/power/INT signals and only with one signal; one SoC GPIO may not carry two functions. The dev kit's shared interrupt line (INT on UULP_VBAT_GPIO_3) passes.
- BOM costs are `null` where not confirmed (FL-01 breakouts and load cell are still "model TBD"); the dev kit is $40 MSRP from the Silicon Labs page.
- The kit status badge is green BUILT / grey REFERENCE, not violet: violet is for real device data, and a kit's status is not a reading.
- `.venv` did not exist on this machine; created with Python 3.13 (3.14 failed in ensurepip).

## Factory extension: K1 part library
- Parts are drawn procedurally in SVG (`frontend/src/wiring/parts/`), one function per family; no third-party artwork, so CREDITS.md only matters once a photo is added under `frontend/public/parts/<part_id>.jpg` (the breadboard view uses it instead of the drawing when it exists).
- The breadboard view is now at one scale, 10 px per mm, for the board and every external part; the canvas grows to fit (a 90 mm load cell next to a 30 mm board). A 20 mm scale bar sits bottom-left.
- `drawing.dims_evidence` says whether sizes come from a datasheet or are typical for that kind of part. FL-01's two breakouts and the load cell are still "model TBD" (open questions), so they are drawn at typical Qwiic-breakout (25.4 mm square) and 50 kg bar load cell sizes, and the tooltip says so.
- Pads: `pins[].x_mm/y_mm` on a part's drawing put wires on the real pad; an optional `side` says which way the wire leaves.
- Pre-made cables (`qwiic_cable`, `m12_cable`, `jst_cable`, `usb_cable`) are drawn once per connector pair as a jacketed cable with moulded plugs at both ends and the conductors side by side; loose `wire` connections get insulation, a highlight and tinned ends. Planned wires are faded, not dashed.
- /parts is the gallery (100% / 300%); a test requires every schema family to have a drawing function and a gallery specimen.
- Checked in the browser at fit and at about 5× zoom on /wiring/fl01_sensor_pack and /parts. Fixed: conductors crossing inside the Qwiic cable, load-cell leads crossing, dashed wires reading as chains.

## Factory extension: K2 reference kits
- 15 reference kits, generated by `tools/kits/gen_reference_kits.py` (kept in the repo so the kits can be regenerated after a fix; the JSON files remain what the backend serves).
- Every reference kit is prototyped on a buyable Silicon Labs board: SIWX917-DK2605A (Wi-Fi kits; pads from UG581, the same board as FL-01), xG24-DK2601B (Thread kits), xG27-DK2602A (badge), SLTB010A BG22 Thunderboard (tag, helmet clip). Part numbers and links checked on silabs.com / distributor pages on 2026-10-11; only the DK2605A has a confirmed price ($40 MSRP), the others are left without a price.
- The EFR32 dev kits' pad mapping was not confirmed, so those kits reuse the BRD2605A pad numbering as a placeholder, mark every pin "unverified", and say so in an open question.
- Third-party parts (sensors, regulators, modules): part numbers, I2C addresses, supply ranges, sizes and costs are from memory, marked unverified, and each kit has an open question saying to check the datasheets. Costs are rough budget figures; the UI says so.
- Battery life and power budgets are estimates with their assumptions written next to them. The env node is USB-powered with a LiPo back-up because the PM2.5 sensor's fan makes pure battery power impractical; that is said in the kit.
- New simulated device types: truck_telematics, dock_bay, conveyor_monitor, compressor_monitor, helmet_clip, gas_detector, leak_sensor, tank_level, fire_panel (plus models for the existing power_meter and asset_tag types). New devices TT-01/02, DB-01/02, AT-01, CV-01, CP-01, HC-01, EN-04, GD-01, LK-01, TL-01, FP-01, PM-01 sit in today's zones; F1 moves them into the campus buildings.
- Truck telematics doesn't publish a position: a real unit would report GNSS, but in the twin the truck's position comes from the movement engine, and a second, simulated position would contradict it.
- Machine monitors now also report `temperature_c` (bearing thermocouple in the kit), modelled from motor current.
- Validation: analog nodes (`AIN_*`) and 1-Wire lines may connect several parts to one pin; any other signal on one pin twice is still an error.
- Tree layout: each part is placed under the pins it connects to on the rows above, which removed most wire crossings on the bigger kits.
