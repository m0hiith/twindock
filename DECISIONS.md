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

## Factory extension: K3 worker safety
- All rules live in `backend/twindock/safety.py` and run on the same inputs for simulated and real badges (`set_position`, `on_badge`, `set_helmet`); alerts still come only from `backend/rules/safety.yaml` (8 new rules) and `devices.yaml` (gas, fire panel, heat, leak, conveyor jam, air pressure).
- Direction: a forklift's direction of travel comes from its recent movement; a worker within 60° of it gets a radius ×1.3, ×2 when the forklift reverses (heading opposite to movement). The forklift flashes an amber beacon (3D model) and the badge is told to buzz.
- Fall: pre-alert, 30 s to cancel on the badge, then critical man-down with location and the nearest first-aider (a worker marked `first_aider` with a fresh badge). No movement for 90 s is the same path; walking again clears a no-movement man-down. SOS and man-down stay open until closed on the monitoring page, even if the badge goes quiet.
- Gas: a gas detector in alarm (fresh reading) evacuates its zone and any zone whose bounding box is within 6 m. A real gas detection system must come first; the node only adds information (the kit says so).
- Heat: NOAA heat index per zone from env nodes; zones at or above 32 °C buzz rest reminders every 20 min, naming nobody.
- PPE: only the helmet can be sensed (helmet clip). Missing: a buzz at most every 10 min, a count on the wire, nothing stored, no worker id.
- Evacuation: workers on shift at the start are the headcount; arrival is a position within 6 m of a muster point; simulated badges walk to the nearest one (`goto`). Muster points MP-1/MP-2 are placeholders until F1 places real ones.
- Privacy: location is shown only for an active condition or evacuation (`privacy.location: alerts_only`, `always` possible); otherwise workers are drawn at their zone centre and the badge position reading is withheld from device updates. Off-site positions are dropped. Shift/breaks are served per worker (`/api/safety/me/<id>`) and to the supervisor; the broadcast has only counts. Retention 30 days, configurable in `sites.json`. The demo has no sign-in, so `/me/<id>` is the worker's link, not a protected page.
- Zones got `hazard`, `ppe`, `time_limit_min`, `lone_worker` for the existing press, cold room, production and dock zones; F1 sets them for the campus.

## Factory extension: K4 monitoring centre
- `/monitor` is one page for a 1920 × 1080 wall display with no page scrolling: the 3D campus (overview camera: `site = "ALL"`, every site in view) with pulsing rings at open alerts (acknowledged ones stop pulsing and stay as a steady ring), open alerts and the incident timeline (tabs), worker safety with the evacuation controls and live headcount, and a bottom strip (production, logistics, energy, air quality, device health, GW-01).
- GW-01, the real board, is always the last tile with the violet LIVE badge ("Waiting for device" until a message arrives). Every other tile is SIM-badged or plainly computed from units.
- Energy: kW now from the simulated power meters; "today" counts from the meter's kWh register at the start of the day; "yesterday" appears only after a midnight has passed while the backend runs (in memory, so a restart means "no data yet"). Nothing is back-filled or invented.
- Incident timeline: `GET /api/monitor` returns the last 24 h of alerts (up to 2000) with who acknowledged, response time and resolution time. The daily safety report is a one-page PDF drawn from that (counts, median response and resolution, near-misses under 1.5 m, falls and cancelled falls, SOS, restricted entries, last evacuation drill, the last 22 incidents); roles and zones only, no names.
- Camera fly-to: clicking an alert, a worker row or anything in the scene flies the camera there and opens the inspect card on the map; alerts on `/monitor` keep the page (`stay`), on other pages they still go to /twin.
- Worst air quality = the zone whose CO₂ or PM2.5 is closest to its limit (1000 ppm, 25 µg/m³) among online simulated sensors.
- Checked in the browser at 1920 × 1080 with the simulator running: SOS, a gas alarm and the resulting evacuate alerts showed in all panels and on the map.

## Factory extension: F1 campus layout
- The campus is data, generated by `tools/campus/gen_campus.py` (idempotent) into `layout.json` and `sites.json`; F2's 3D buildings read `layout.campus`. A test regenerates it and checks the files don't change.
- Two sites kept (WH-01 west of x = 83, FAC-01 east of it) rather than adding sites per area: the site picker, device registry and privacy bounds stay simple, and the monitor's "ALL" camera shows everything. Both now span z −12…104.
- Pedestrian graph = nodes with `kinds: []` (the existing WALK_* stands are in it, joined by lanes inside the hall). Vehicle lanes and walkways only meet on lanes marked `crossing`; five crossings with hotspots. Inside the factory hall people and forklifts still share aisles, as before (the proximity rules exist for that); those lanes are exempt in the test.
- Weighbridge: a node between ROAD_E and GATE_IN (the old direct lane is replaced); trucks pass through it, no dwell yet.
- Raw material store docks are nodes only (not in `docks`) so the movement engine's truck assignment and the existing tests are unchanged; the raw → factory → warehouse forklift route is tested for connectivity.
- Line 2 (Press 2, Packer 2, a second conveyor) is data plus two machine monitors; OEE and "units today" stay line 1 (`Machine.line`) so the existing KPIs keep their meaning.
- Moved devices: CP-01 into the compressor room, TL-01 into the water tanks, TT-01 into the docks zone (it was outside its zone).
- Muster points replaced by MP-1/2/3 on open ground (tested: clear of buildings and roads); hazmat is 12 m or more from every occupied building and at the far south-east.
- New workers' badges check in for the lone-worker rule every 7 min (`sim.checkin_s`); the demo can make a worker forget (`skip_checkin`).

## Factory extension: F2 buildings in 3D
- Every campus building is drawn from `layout.campus` by `frontend/src/scene/campus/` (shared helpers, batch A gate/parking/admin/canteen/medical, batch B raw store/QC lab/workshop, batch C utilities/ETP/hazmat/fire pump/solar). Batches B and C were committed together; batch A on its own.
- Cutaway: the "Interiors" map control (and the building card) takes the roofs off and lowers the walls facing the camera, like the warehouse and factory. Closed is the default for the new buildings. The warehouse and factory hall stay cut away as before, so `/twin` keeps showing the production line.
- Rooftop solar: panels are drawn on the raw store roof (closed) and on the warehouse and factory roofs in the monitoring centre's overview camera (where those roofs are drawn flat); on `/twin` the two halls stay open. Output is computed from the time of day (6:00-18:00 sine) times the design kWp × 0.8 and labelled as simulated, never as a measurement.
- Animations come from device state: generator shakes and puffs while PM-05 reads over 1 kW, compressor roof fan spins fast while CP-01's motor current is over 30 A, tank levels follow the tank-level devices, the boom barrier lifts when a truck is within 9 m, dock doors follow DB-03/04.
- Device markers stand at their real mounting height (`MOUNT_HEIGHT` per device type) on a thin stem over their floor ring.
- The inspect card for a building (`BuildingCard`) shows purpose, hazard, PPE, restricted roles, people count (a count only), KPIs computed from the building's own devices, and its devices with readings and ages.
- Checked in the browser (overview, FAC-01 view, building card); no per-building screenshots were saved.

## Factory extension: F3 utilities, energy and emergencies
- Campus physics lives in the simulator (`tools/sim_models.py` `Physics`, config in `sites.json` `utilities`): feeder meters follow what runs (machines, compressor, EV chargers, the fire pump during a fire alarm), the substation incomer meter reads the whole campus minus solar and drops to 0 V on a grid failure, the generator starts after 8 s and picks up the critical zones only (fire pump house, hazardous store, substation, generator, admin), and mains devices elsewhere stop reporting until the grid is back. Critical devices have battery back-up in the design, so they do not blink out during the 8 s start.
- Grid state is read from the incomer's voltage reading, not from a hidden flag: the rules, the energy page and the monitor all see what the meter says.
- Solar is computed (design 360 kWp × 0.8 × time-of-day sine), labelled "computed" everywhere; it is zero in a grid failure (no islanding). No solar value is ever shown as measured.
- Compressed air: a tripped compressor (`tripped` channel, command `fault`) makes no air; pressure falls about 1 bar per 20 s; machines' cycle times stretch (×1 below 6 bar up to ×2.2). `leak` adds demand as before.
- Water: tank levels as before; ETP inflow/outflow quality (WQ-01/02, new kit `water_quality_node`: pH and turbidity). Bands (pH 6.5-8.5, turbidity 25 NTU) are example limits for the demo and say so in the rule text.
- Fire: a fire panel bridge alarm starts the K3 evacuation (advice to badges and screens) with reason "fire alarm: <zone>"; it closes, locks and silences nothing, and ending the evacuation stays a person's decision. Workers walk the pedestrian graph to the muster point (`goto` carries the walkway waypoints); a muster point within 40 m of the hazard is skipped. `safety_update.routes` gives one route per zone with people (zone-level, so nobody is singled out) and the 3D scene draws them.
- Energy: `/api/monitor.power` (kW by building, other loads, solar share, grid import, generator, diesel, kWh per unit = production feeder energy since the backend started ÷ units made, peak warning at 160 kW grid import for 30 s) and the `/energy` page. "Other loads" is what the incomer sees beyond the metered feeders, so it is a difference, not a measurement.
- Scenario buttons on `/control` (Demo tab, section 3): grid failure, gas leak in the hazardous store, fire alarm in the warehouse, compressor fault; "Reset demo" restores all four. Each has an end-to-end test (`tests/test_scenarios_f3.py`) that runs the simulator and the backend together.
- New rule subject `site` (backend/rules/site.yaml): grid failure, devices without power, low diesel, peak demand.
- `utilities` and the WQ devices are generated by `tools/campus/gen_campus.py` like the rest of the campus.
- The compressor's fault channel is called `tripped`: a channel named `fault` collided with the device-status fault in the rule facts.

## Factory extension: F4 navigation and performance
- Level of detail is one value (`far | mid | near`) in the view store, set by the camera rig from pixels per metre with hysteresis (tested). Far = campus overview, mid = a site, near = a building. Buildings' windows, signs and ground labels appear from mid; device markers from mid (and only when the Devices control is on); interiors only with the roof off.
- Instancing: solar panels (3 draw calls for ~660 panels) and fixed device markers (4 instanced meshes). Badges stay individual groups because they move.
- Mini-map shows buildings, roads, muster points and the camera's visible ground area; click or drag to move the camera. Presets: a camera menu (campus overview, each site, each building, follow the selected vehicle or worker). Search covers sites, buildings, vehicles, workers (by id or role), devices and open alerts.
- Measured before and after in `docs/perf_report.md`: draw calls 1729 to 564 in the overview, frame cost 14.8 to 10.5 ms, JS heap 210 to 132 MB.
- Chrome pauses React effects and timers in background tabs: the stats and bench hooks only appear once the tab has been in front (a screenshot is enough). The hooks now also write to `document.body.dataset` so they can be read from outside the page.
- Bug found while checking the overview: a badge that was silent for a while and then reported from the same spot counted as "standing still since before", raising no-movement alerts for everyone after a simulator restart. A gap of more than 10 s now restarts the still timer (tested).

## Auto mode runs the factory side too
- Added a raw-material flow: TR-03 (area raw) docks at DK-04/05 (raw store), FL-05 unloads to RAW_STOCK and feeds FAC_IN; the line uses up a pallet every 25 s while a machine is running; TR-03 leaves when empty and returns from RD_110 with a new load. Raw bays sit 9 m from their docks (as in the warehouse) so a forklift at the dock never overlaps the truck.
- Everything is simulated (`source: "auto"`); no board topics or GW-01 behaviour touched. BTN1 now cycles FL-01..FL-05.

## Simulator inside the backend when there is no broker
- The Vercel deploy has no Mosquitto, so every SIM device showed "never seen" and demo beats failed with "Not connected to the MQTT broker". `TWINDOCK_SIM=auto` (default) runs `tools/site_sim.py` in the backend's event loop when the broker isn't reachable at startup: messages go to `Engine.on_mqtt` on the same site topics (schema-checked, device registry only) and site commands go straight back. LED commands to the board still need the broker. GW-01 and RB-01 stay offline until the real hardware speaks.
- Kits: the user asked not to show "reference". Non-built kits now say "Simulated kit" / SIM badge (still grey, never violet), and the part panel lists the SIM readings of devices built from the kit.

## Realism and deploy run (REALISM_DEPLOY_PROMPTS.md)

### D0/D1: one production container
- Vercel is gone (`vercel.json`, `.vercelignore` and the backend/simtools copy paths). Serverless functions freeze the 20 Hz tick and the embedded simulator between requests, start fresh worlds on cold starts, run several copies and can't hold the `/ws` hub (docs/deploy_diagnosis.md, reproduced by `scripts/repro_serverless.py`). The factory logic was fine; the hosting model wasn't.
- One `Dockerfile`: a Node stage builds the frontend, and a slim Python stage serves `frontend/dist`, `/api` and `/ws` from one FastAPI process on `$PORT` (default 7860, the Hugging Face Spaces port) with **exactly one worker**, because two workers would be two separate worlds. The container keeps the repo layout under `/app`, so no path in the code changes.
- Broker: `MQTT_URL` (`mqtt://` or `mqtts://user:pass@host:8883`) wins. Without it the container sets `TWINDOCK_MQTT=0` and runs the simulator embedded. With a remote `MQTT_URL` the simulator also stays embedded (nobody runs `tools/site_sim.py` next to a hosted backend); `TWINDOCK_SIM=external` overrides that. Passwords are never logged (`BrokerConfig.__str__`).
- `/api/health` reports uptime, achieved tick rate (5 s window), sim clock, SIM devices online/total and the broker. A tick rate below 15 Hz is logged as a warning.
- The frontend already took its WebSocket URL from `window.location` and got a fresh `world_snapshot` on every connect; reconnects now add jitter and back off to 10 s, so many screens don't hammer a host that is waking up.
- Docker on the dev Mac is Colima + the Homebrew docker CLI (Docker Desktop had been removed). `scripts/verify_live.py` watches a running instance over `/ws` for N minutes (auto mode, compressor cycling, generator on a grid failure, line output, vibration, tick rate).

### D3: warm start and the simulation clock
- One clock for everything (`backend/twindock/simclock.py`): the engine's `clock` is the simulation clock, so every `server_ts_ms`, `received_ms`, alert and safety timer is on simulated time. The UI already measured ages on the server clock; it now also advances that clock at the current speed between messages.
- The live loop is one 20 Hz loop (`App.advance`) that moves the clock, steps the simulator in fixed 0.25 s steps and ticks the engine in ≤ 0.05 s slices; at ×5/×20 a tick is cut into more slices, so movement and traffic never jump.
- Warm start (embedded simulator only; an external `tools/site_sim.py` can't be fast-forwarded): the clock starts 45 min in the past (`TWINDOCK_WARM_START_MIN`), auto mode runs, and exactly 45 simulated minutes are fast-forwarded with 0.5 s steps (movement is reservation-based, so coarser steps never skip a node) before the app serves. Afterwards the clock is a few seconds behind the wall clock, which is honest and harmless. Auto mode stays on after a warm start (the hosted demo is a working factory; `TWINDOCK_AUTO=0` turns it off); CLAUDE.md's "auto off by default" still holds for local runs against the board, where the warm start is off when the external simulator runs.
- Seed = fixed 917 × 100000 + CRC of the date (`TWINDOCK_SEED` overrides): every restart on the same day replays the same warm start from the same start time, other days differ. Auto mode's dice use seed + 1 unless `TWINDOCK_AUTO_SEED` is set.
- Speed ×1/×5/×20 in the top bar next to the clock; ×1 is the default. Anything above ×1 is refused while the real board is online, and a board coming online resets to ×1 with an event: the board's 15 s staleness and LED confirmation timeouts are real-time rules.
- Validation was the biggest cost of the message path (jsonschema ≈ 15 µs per reading). `fastcheck.py` compiles each schema in /shared into a yes/no check (≈ 3 µs); only "valid" is trusted from it, and any "invalid" goes through jsonschema for the error text. `test_fastcheck.py` checks the two agree on 2000+ real and mutated messages. During the warm start the simulator's own pre-send check is skipped (in-process, trusted); the engine still validates every message. Warm start: 45 simulated minutes in ≈ 6.5 s on the dev Mac.
- The container sets `TZ=Asia/Kolkata` (with tzdata) as the site's time zone, because solar, shifts and tariffs use the simulated *local* hour. A UTC container would have produced solar power at night for a viewer in India. Override it with `-e TZ=...`.

### R0: one simulation core
- The core lives in `backend/sim/` (params, seeded streams, core with fixed step + event queue + cause log, measurement layer, models, devices). `tools/site_sim.py` and the embedded simulator both use it through the unchanged `SiteSim` interface; `tools/sim_models.py` is gone. The container copies `backend/sim`.
- The core always models the whole campus; which devices *publish* is a separate choice (`--site/--zones`). Physics no longer depends on which meters happen to be simulated (the old `Physics` only existed if the incomer was selected).
- Models couple only through the bus (kW, Nm³/min, bar, zone power, flags). One-step lag on the pressure ↔ machine loop is accepted (0.25 s vs time constants of tens of seconds).
- Every number is in `backend/sim/params/*.yaml` with a unit and a source; an AST test fails on numbers in model code. 116 of 207 parameters are honest assumptions at this point; R1–R4 replace many with datasheet or standard values.
- Physics numbers left `sites.json` (machine cycle/current/vibration/scrap/alarms, meter base loads, generator timings, diesel use); `sites.json` keeps wiring and commissioning only (which meter is on which feeder, critical zones, battery at commissioning, badge check-in period). `gen_campus.py` was changed to match, and regenerating gives the same file. The backend's OEE ideal cycle times in `sites.json` must equal the simulator's (`test_backend_and_simulator_agree_on_ideal_cycle_times`).
- Sensor specs follow the kit parts. Two kit inconsistencies surfaced and were fixed. (1) The energy-meter kit specified a single-phase SDM230 (230 V, ≤ 100 A ≈ 23 kW) for 400 V feeders of 70–150 kW; it is now an SDM630MCT with 400/5 A CTs (full scale ≈ 277 kW) in `tools/kits/gen_reference_kits.py` and the regenerated `hardware/kits/energy_meter.json`. (2) The compressor monitor's 30 A clamp could not read the old simulated 46 A; the compressor is now a 15 kW screw (≈ 24 A loaded) with FAD 2.4 Nm³/min, and machine air use was sized to match (0.5 / 0.3 Nm³/min).
- Compressed air is already physical in R0 (receiver mass balance, load/unload band, leaks as a share of demand). With one compressor at ~77 % load, recovering from a trip takes minutes, which is realistic; the F3 test now waits 240 s, and R1 adds the standby compressor and the low-pressure trip that make recovery faster.
- Measurement noise now comes from the sensor spec (e.g. SHT45 σ 0.02 °C), not from the models. Badge positions are still exact in R0 (σ 0); R4 adds BLE zone error.
- `/model` (GET `/api/model`) lists every model, its equations in plain language, every parameter with its source kind, every simulated sensor and distribution, and the last 40 events with their causes.
