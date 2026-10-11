# TwinDock Factory: device kits, worker safety and a full factory campus

Three extensions, run after the site twin (S0–S3, S6) is in place:

1. **Device kits:** every asset type (truck, machine, worker, dock, cold room, utilities...)
   gets its own sensor kit with a wiring page like FL-01's, drawn with realistic top-view parts.
2. **Worker safety and monitoring:** safety features for people plus a central monitoring room.
3. **Full factory campus:** from one manufacturing block + warehouse to a complete factory
   with gate, offices, utilities, labs, workshop, canteen, fire safety and more.

## Ground rules (put in every session)

- **Real vs designed.** Only the FL-01 kit (SiWx917 BRD2605A) is real hardware. Every other kit
  is a **reference design**: real, buyable parts with a correct wiring plan, but simulated data.
  Every wiring page shows a status banner: "Built and verified" or "Reference design · simulated".
- **Silicon Labs radios first.** Pick the radio by the job, and say why in the kit:
  - Wi-Fi 6 + BLE (SiWx917): mains-powered or vehicle-powered kits that need bandwidth
  - BLE (EFR32BG22 / BG27 class): coin-cell badges and tags
  - Thread / Matter / Zigbee (EFR32MG24 class): battery building sensors, mesh networks
  Check exact part numbers and capabilities on silabs.com before writing them; mark anything
  unconfirmed as "unverified" exactly like wiring.json does today.
- **No made-up values.** Simulated kits publish through the same broker and schemas with
  `source: "sim"`. Nothing simulated is ever shown as LIVE.
- **Realistic parts, not copied artwork.** Draw parts procedurally (see K1) or use part
  graphics with a license that allows it (e.g. Fritzing part SVGs from SparkFun/Adafruit,
  CC BY-SA, with attribution in CREDITS.md). Never copy vendor marketing images.
- One AI tool editing the repo at a time. All tests, typecheck and build pass before each commit.

---

## K0: Kit framework (generalise wiring.json)

```
Read CLAUDE.md, HARDWARE.md, hardware/wiring.json, shared/schemas/hardware and the /wiring page.
Generalise from one wiring file to many device kits. Plan in docs/kits_plan.md, then build.

1. hardware/kits/<kit_id>.json, one per kit, using the existing wiring schema extended with:
   kit {id, name, asset_type, status: built|reference, radio, power_source, mounting,
   purpose, est_battery_life?}, and a bom[] with part number, manufacturer, quantity,
   approx unit cost, link, and source (datasheet|silabs.com|unverified).
2. Move the current FL-01 file to hardware/kits/fl01_sensor_pack.json with status "built".
   Nothing about it changes; its tests keep passing; gen_pins.py still reads it.
3. A kit is attached to device ids in the site model (one kit design, many devices).
4. /wiring becomes /wiring/:kit_id with a kit picker (grouped by asset type) and the
   status banner. The existing three views work for every kit unchanged.
5. A /kits index: cards per kit with asset type, radio, power, part count, BOM cost,
   status. Click opens its wiring page.
6. Validation (extend W5 checks to every kit): schema, no pin driven twice, no I2C address
   clash per bus, voltage compatibility, every BOM part used in the wiring and vice versa.
Commit when all checks pass.
```

---

## K1: Realistic top-view part library

```
Read CLAUDE.md and the /wiring code. Make every part on the breadboard view look like the
real thing seen from above, the way the SiWx917 board already does.

1. frontend/src/wiring/parts/: one component per part *family*, drawn procedurally in SVG
   from real dimensions (mm) taken from each part's datasheet or breakout page:
   PCB (correct colour: green, blue, black or red; rounded corners; mounting holes),
   chips (black QFN/LGA/SOIC packages with pin-1 dot and readable marking),
   connectors (Qwiic/JST-SH, JST-PH, screw terminals, pin headers, USB-C, M12),
   passives (0603/0805 resistors and caps), crystals, antennas (chip, PCB trace, u.FL),
   LEDs, buttons, coin-cell holders, LiPo pouch cells, sensor windows (ToF optical
   window, gas sensor mesh cap, microphone port), relays, terminal blocks, current clamps,
   load cells, magnetic reed switches, PIR domes, buzzers.
2. Each part entry in the kit JSON has drawing {family, w_mm, h_mm, pcb_color, features[]}
   and pin positions in mm, so wires land on the real pads.
3. Optional photo mode: if frontend/public/parts/<part_id>.jpg exists (my own photo or a
   licensed image listed in CREDITS.md), use it instead of the drawing, like the board photo.
4. Scale: everything on the breadboard view is drawn at true relative size, with a scale bar.
5. Wires: realistic thickness, colour by signal, slight curve, insulation highlight, and
   ferrules/connectors at the ends. Cables (Qwiic, M12) drawn as cables, not single lines.
6. Render a "part gallery" test page showing every family side by side, and check it in
   the browser at 100% and 300% zoom. Fix anything that looks toy-like or out of scale.
```

---

## K2: Kits for every asset

```
Read CLAUDE.md, docs/kits_plan.md and the kit framework. Create reference-design kits,
each with a complete kit JSON (parts, pins, connections, BOM, captions in plain language),
attached to the matching simulated devices, publishing simulated data through the broker.

Logistics
- truck_telematics: SiWx917 + GNSS module (UART), 4G modem or vehicle hotspot, IMU
  (harsh braking), door reed switch, cargo temperature probe, vehicle 12/24 V to 3.3 V
  supply with protection. Data: position, speed, door open, cargo temp, harsh events.
- dock_bay: occupancy (ToF or radar), dock door position (reed switches), dock light,
  leveler state input. Mains-powered.
- pallet_asset_tag: BLE tag on a coin cell; button + LED for "find me".

Production
- machine_monitor: current clamp(s) via ADC, 3-axis vibration (accelerometer), surface
  temperature (thermocouple or IR), stack-light input (run / fault), cycle counter input.
  Data: state, current, vibration RMS, temperature, cycle count.
- conveyor_monitor: motor current, belt speed (encoder or hall), jam detection (ToF).
- compressor_monitor (utilities): pressure transducer, current, run hours, dew point.

People (see K3 for behaviour)
- worker_badge: BLE SoC, IMU (fall/man-down), SOS button, vibration motor + buzzer + LED
  for alerts, coin cell or small LiPo, optional skin-contact-free ambient temp/humidity.
- smart_helmet_clip (optional): IMU impact detection, BLE.

Building and environment
- env_node: temperature, humidity, CO2, PM2.5, Thread/Matter radio, battery.
- gas_detector_node: zone gas sensor (e.g. CO/O2 class), alarm relay output, mains.
- door_access: reed switch + badge reader input, Thread.
- energy_meter: DIN-rail meter via Modbus to a SiWx917 bridge.
- water_leak / tank_level: leak probe, ultrasonic level for tanks.
- fire_panel_bridge: dry-contact inputs from an existing fire panel (we only read it;
  we never replace a certified fire system, and the UI says so).

For every kit: radio choice with one-line reason, power budget and estimated battery life
(shown as an estimate with the assumptions), mounting description, and 2–3 plain-language
captions for non-engineers. Run the K0 validation on all kits.
```

---

## K3: Worker safety features

```
Read CLAUDE.md, the site model, the badge kit and the existing proximity rule (S3).
Add worker safety features. Everything simulated is labelled SIM; real badges (phone or
TD-BADGE-* seen by the real board) use the same code path.

1. Pedestrian–vehicle proximity (exists): add vehicle direction so a worker behind a
   reversing forklift is warned earlier; buzz the badge and flash the forklift.
2. Fall / man-down: IMU free-fall followed by impact, or no movement for N seconds →
   pre-alert on the badge (worker can cancel within 30 s) → critical alert with location.
3. SOS button: long press raises a critical alert with location and nearest first-aider.
4. Restricted and hazardous zones: role-based entry; alert on unauthorised entry; time
   limits in high-heat or gas-risk zones.
5. Gas and heat exposure: when a gas_detector_node alarms, every badge in that zone and
   adjacent zones gets an evacuate alert; heat index from env_nodes drives rest-break
   reminders.
6. Lone worker: workers in remote zones (utilities, ETP) must check in every N minutes;
   missed check-in escalates.
7. PPE zone rules: zones that require helmet/vest; the smart_helmet_clip proves the helmet
   is worn (presence + motion); otherwise a reminder, never a punishment record.
8. Emergency evacuation: one button on the monitoring page starts an evacuation; badges
   alert; muster-point gateways count arrivals; a live headcount shows who is unaccounted
   for and their last known zone.
9. Shift and fatigue: hours on shift and break reminders (from badge check-in), shown only
   to the worker and supervisor.
10. Privacy by design (in UI and README): no location tracking off-site or off-shift,
    named location visible only during an active alert or evacuation, otherwise zone
    counts only; data retention period configurable; workers can see their own data.
Tests for every rule, including false-alarm cancel and evacuation headcount.
```

---

## K4: Monitoring centre

```
Read CLAUDE.md and the rules engine (S6). Build /monitor: the control-room view for a
large screen.

1. Left: live campus map (3D, overview camera) with alerts pulsing at their location.
2. Right column: open alerts by severity with acknowledge/assign/resolve, safety status
   (workers on site, in hazardous zones, last fall/SOS), evacuation control and headcount.
3. Bottom strip: production (units, OEE), logistics (trucks on site, docks busy),
   energy (kW now, today vs yesterday), environment (worst air quality zone),
   device health (online %, low batteries, stale), the real gateway GW-01 always shown.
4. Incident timeline: every alert with who acknowledged, response time, resolution.
   A daily safety report (PDF export) with counts, response times and near-misses.
5. Camera fly-to: clicking anything focuses the 3D view on it and opens its inspect card.
6. Works at 1920×1080 and on a wall display with no scrolling.
```

---

## F1: Full factory campus layout

```
Read CLAUDE.md, layout.json and the site model. Expand FAC-01 + WH-01 into one complete
campus "Riverside Campus". Plan in docs/campus_plan.md (with an ASCII map) first, then build.

Campus zones and buildings:
- Main gate and security cabin (boom barrier, truck weighbridge, visitor check-in)
- Car and two-wheeler parking with EV chargers
- Admin office block and reception
- Canteen and first-aid / medical room
- Raw material store (inbound)
- Main manufacturing hall (existing production line, extended to 2 lines)
- Quality control lab
- Maintenance workshop and spare-parts store
- Finished goods warehouse (existing WH-01)
- Logistics yard with truck lanes, waiting area and docks
- Utilities block: electrical substation and transformer, diesel generator, air
  compressor room, water tanks and pumps
- Effluent treatment plant (ETP)
- Hazardous materials store (bunded, separated)
- Fire pump house, fire hydrant ring, assembly / muster points
- Rooftop solar on the big halls
- Internal roads, pedestrian walkways (marked separately from vehicle lanes), green belt

Rules:
1. Realistic flows: trucks enter via gate → weighbridge → yard → docks → exit; raw material
   → manufacturing → QC → warehouse → dispatch; people walk only on walkways and crossings.
2. Waypoint graphs for vehicles and pedestrians are separate, crossing only at marked
   crossings (which become proximity hot spots).
3. Zones carry hazard level and required PPE for K3.
4. Each building is a zone with its own devices from K2 (sensible counts, not hundreds).
Tests for graph connectivity and that no pedestrian path crosses a vehicle lane except
at crossings.
```

---

## F2: Buildings in 3D

```
Read CLAUDE.md, docs/campus_plan.md and the existing low-poly components. Build every campus
building in the same style as the warehouse, in batches, committing after each batch:

Batch A: gate + security + weighbridge, parking + EV chargers, admin block, canteen.
Batch B: raw material store, manufacturing hall with 2 lines, QC lab, maintenance workshop.
Batch C: substation + transformer, generator, compressor room, water tanks, ETP,
         hazardous store, fire pump house, hydrants, muster points, solar roofs.

Each building: cutaway roof or wall toggle so interiors are visible, identifying signage,
its devices placed at real mounting spots, and an inspect card (purpose, zone hazard
level, PPE, devices, live KPIs). Utilities animate with state (generator running,
compressor cycling, solar output by time of day).
After each batch, screenshot the overview and each building, and fix anything cluttered or
out of style.
```

---

## F3: Utilities, energy and emergencies

```
Read CLAUDE.md and the K2 kits. Simulate the campus utilities and connect them:

1. Power: substation feeds zones; solar offsets demand by time of day; generator starts on
   a simulated grid failure (scenario button) and critical loads stay on.
2. Compressed air: compressor pressure, leaks raise demand; machines slow if pressure drops.
3. Water: tank levels, pump runs, ETP inflow/outflow quality bands.
4. Fire: fire_panel_bridge alarm in a zone triggers K3 evacuation, closes nothing
   automatically (we only advise), and shows the route to the nearest muster point.
5. Energy dashboard: kW by building, solar share, kWh per unit produced, peak warnings.
6. Scenario buttons on /control: grid failure, gas leak in hazardous store, fire alarm in
   warehouse, compressor fault. Each runs end to end through devices → rules → alerts →
   monitoring centre.
Tests for each scenario's chain of events.
```

---

## F4: Navigation and performance for a big campus

```
Read CLAUDE.md. Keep the campus fast and easy to navigate.

1. Camera presets: campus overview, each building, "follow" a selected vehicle or worker.
2. Level of detail: far buildings render simplified; interiors and devices only load when
   zoomed in; instancing for repeated items; merge static geometry per building.
3. Mini-map with click-to-go and the visible-area rectangle.
4. Search box finds any building, device, vehicle, worker role or alert and flies to it.
5. Target: 60 fps on the Apple M1 with everything on; report draw calls, triangles and
   memory before and after.
```

---

## Final: audit and story

```
Read CLAUDE.md, DEMO.md and all kits. Then:
1. Run all validations (kits, graphs, schemas) and the full test suite.
2. Audit every page: each value labelled by source (device, sim, computed); nothing
   simulated shown as LIVE; every reference-design kit has its banner.
3. Update DEMO.md with a 6-minute run: real board first, then campus overview, a truck
   arriving through the gate to a dock, a machine anomaly, a worker fall with cancel and
   then a real alert, a gas-leak evacuation with headcount, the kits page and one wiring
   page, the monitoring centre.
4. Update README: campus map, list of kits with real/reference status, privacy section,
   CREDITS.md for any third-party part graphics, and the WareTrack design credit.
5. Push and write RUN_REPORT.md.
```

---

## Single-stretch version

```
Read CLAUDE.md, HARDWARE.md, /shared and FACTORY_PROMPTS.md. Run K0, K1, K2, K3, K4, F1,
F2, F3, F4 and Final in that order in one continuous run, following every rule in the
"Ground rules" section. Do not stop for approval; record decisions in DECISIONS.md.
One commit per prompt (one per batch for F2). Tests, typecheck and build must pass before
each commit. If a prompt still fails after three serious attempts, revert its uncommitted
changes, note it in DECISIONS.md and continue. Never touch firmware/, the real board's
topics or GW-01's behaviour. Push at the end and write RUN_REPORT.md.
```
