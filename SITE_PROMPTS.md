# TwinDock Site: Claude Code prompts for the factory extension

Extends TwinDock from a warehouse twin to a **site twin**: a factory with a warehouse attached,
where every kind of IoT device appears in one live, game-style view, and a new site can be
planned, commissioned and managed from the same tool.

## Before you start

- **Gate:** start S0 only after firmware Prompt 2 Steps A–D work on the real board.
  The extension is only convincing if the one real device in it is real.
- **Order matters.** Prompts are sorted by value. S0–S3 are the core; stop wherever time runs out.
  Every prompt ends with a working, committed state.
- **One AI tool at a time.** Close Codex or any other agent before running these.
- Run each prompt in a fresh Claude Code session from the repo root.

## What gets built

| Prompt | Adds | Real or simulated |
|---|---|---|
| S0 | Site → zone → device model, CLAUDE.md addendum | Foundation |
| S1 | Fleet page: every device, health, protocol | Real board + simulated |
| S2 | Production line: machines, vibration baselines, OEE | Simulated |
| S3 | Worker safety: BLE badges, forklift proximity warning | Simulated (real later) |
| S4 | Cold room and docks: temperature, doors, occupancy | Simulated |
| S5 | Energy and building: power per zone, lights, air quality | Simulated |
| S6 | Rules and alerts engine | Applies to all |
| S7 | Commissioning: add a device by QR scan and map tap | Real flow, works with the real board |
| S8 | New factory planner: layout editor, capacity simulation, site template | Planning tool |
| S9 | Firmware lifecycle view: versions, update campaigns | Real board reports version; updates simulated and labelled |
| S10 | Demo and story hardening | All |

---

## S0: Foundation and rules

```
Read CLAUDE.md, HARDWARE.md, /shared and the backend and frontend structure.
We are extending TwinDock into a site twin. Plan first: show me the plan and the
/shared changes before writing code.

1. Data model in /shared and the backend:
   - Site {id, name, kind: warehouse|factory|mixed, layout_ref}
   - Zone {id, site_id, name, kind: storage|docks|production|cold_room|office|yard, polygon}
   - Device {id, site_id, zone_id, type, protocol: wifi|ble|thread|matter,
     capabilities[], position, battery_pct?, fw_version?, rssi_dbm?, last_seen_ms,
     source: device|sim, status: online|stale|offline|fault}
   - Device types to support now: gateway (the SiWx917), machine_monitor, env_sensor,
     door_sensor, occupancy_sensor, badge, asset_tag, power_meter, light, air_quality.
2. The real SiWx917 becomes device "GW-01" of type gateway in site WH-01. Its existing
   topics, behaviour, tests and the "board is never faked" rules must not change.
3. MQTT topics for new devices: twin/<site>/<device_id>/<channel>. A retained
   twin/<site>/<device_id>/hello announces type, protocol and capabilities, exactly
   like the board's hello. Same staleness rules as the board.
4. A single simulator process (tools/site_sim.py) publishes all simulated devices through
   the same broker and schemas, with source "sim" and fw_version "sim-x.y". It can be
   started per zone and stopped without touching the real board.
5. Add a CLAUDE.md section "Site twin" with these rules:
   - Every device shows LIVE (violet) or SIM (grey) everywhere it appears.
   - Simulated devices never write into real device state and never trigger real LED or
     board commands.
   - No value is shown without a source and an age.
   - Device protocols are labelled honestly: a simulated Thread device is "SIM · Thread".
6. Site selector in the top bar switches between sites. Create site FAC-01
   "Riverside Assembly" next to WH-01 with zones: production, cold_room, docks, office.
Tests: model validation, topic parsing, staleness for a sim device, and a test proving a
sim device cannot change GW-01's state. Commit when green.
```

---

## S1: Fleet page

```
Read CLAUDE.md (Site twin section) and /shared. Build /fleet.

1. A table of every device across sites: id, type, protocol, site, zone, status,
   battery, signal, firmware, last seen (live age), LIVE/SIM badge.
2. Real devices always sort first. Default filter: "Needs attention" (stale, offline,
   fault, battery below 20%). Filters for site, zone, type, protocol, source.
3. Summary strip: devices online / total, by protocol, needing attention.
4. Clicking a device opens a side panel: its latest readings with ages, a small history
   chart of its main reading, its location on a mini-map, and "Show in twin", which
   switches site, centres the 3D camera on it and selects it.
5. Device markers in the 3D scene: small low-poly sensor pucks at their positions, with a
   colour ring for status. Hidden by default; a "Devices" toggle in the map controls
   shows them.
Tests for sorting and the needs-attention filter. Check the page in the browser.
```

---

## S2: Production line

```
Read CLAUDE.md and /shared. Add the production zone of FAC-01.

1. 3D: an assembly line in the existing low-poly style: a conveyor (animated belt when
   running), two machines (M-01 press, M-02 packer), a QC station, and an outbound pallet
   spot that feeds the warehouse. Each machine has a machine_monitor device mounted on it.
2. Simulation: each machine has states running | idle | fault | maintenance, a cycle time,
   motor current and vibration RMS. Vibration has a per-machine baseline learned over the
   first minutes; flag "abnormal vibration" when the rolling z-score exceeds a configurable
   threshold. Call it abnormal compared with baseline, never a failure prediction.
3. A "degrade" control on /control injects a slowly rising vibration on one machine so the
   anomaly can be demonstrated on cue.
4. Output connects to logistics: finished units become pallets at the outbound spot, and
   forklifts in auto mode carry them to the warehouse racks.
5. KPIs for the production zone: units today, machine availability, simple OEE
   (availability × performance × quality) with the formula shown on hover.
6. Inspect card for a machine: state pill, cycle time, current, vibration with baseline
   band chart, units today, last fault.
Tests for the state machine, the baseline/z-score logic and the OEE formula.
```

---

## S3: Worker safety

```
Read CLAUDE.md and /shared. Add worker safety with BLE badges.

1. Device type badge (protocol ble). 4 simulated workers with names and roles walking
   realistic routes between office, production and docks on the waypoint graph.
2. Proximity rule: when a badge is within a configurable distance (default 3 m) of a
   moving forklift, raise a "pedestrian near forklift" warning; critical below 1.5 m.
   Show a pulsing ring around both in the 3D scene, a notification and an event.
3. Restricted zones: mark the cold room and the press area as restricted. A badge
   entering without the right role raises an alert.
4. Real path: badges named TD-BADGE-* seen by the real SiWx917's BLE scan (once firmware
   Step E exists) become real badges, using the same RSSI smoothing as live forklifts.
   Until then a phone advertising TD-BADGE-01 can act as one.
5. Safety panel on /twin: live count of workers per zone, warnings today, closest
   approach today.
6. Privacy note in the UI and README: badges show role and zone, names only to authorised
   users; nothing is recorded beyond the event log.
Tests for the proximity rule (moving vs parked forklift), thresholds and restricted zones.
```

---

## S4: Cold room and docks

```
Read CLAUDE.md and /shared.

Cold room (FAC-01):
1. 3D cold room with an insulated door. Two env_sensor devices (temperature, humidity)
   and one door_sensor.
2. Temperature reacts to the door: rises while open, recovers when closed. Alert when the
   door stays open over 60 s and when temperature leaves the configured range; show the
   time out of range.
3. Inspect card: temperature chart with the allowed band, door open count today.

Docks (WH-01 and FAC-01):
4. door_sensor and occupancy_sensor per bay. Bay occupancy in the existing dock logic now
   comes from these devices when present (simulated), falling back to the engine.
5. Alert: dock door open with no truck for over 2 minutes (energy loss, security).
Tests for the door/temperature model and both alerts.
```

---

## S5: Energy and building

```
Read CLAUDE.md and /shared.

1. power_meter devices per zone and per machine (simulated, protocol wifi). Power follows
   machine state and lighting.
2. light devices (protocol matter, simulated) per zone: on when a badge or a moving
   forklift is in the zone, dimmed after 2 minutes empty. Show lights in the 3D scene.
3. air_quality devices (CO2, PM2.5) in production and office, with thresholds.
4. Energy page section or panel: kW now per zone, kWh today, energy per pallet shipped,
   and how much the occupancy-based lighting saved versus always-on (computed, with the
   formula shown).
5. Heat-map overlay toggle in the 3D view: colour zones by power, temperature or CO2.
Tests for lighting control logic and energy-per-pallet calculation.
```

---

## S6: Rules and alerts engine

```
Read CLAUDE.md and /shared. Replace scattered alert code with one rules engine.

1. Rules defined in backend/rules/*.yaml: condition on device readings or world state,
   duration, severity (info | warning | critical), message template, and the zone or
   unit it points at. Migrate every existing alert (impact, abnormal vibration,
   proximity, cold room, dock door, air quality) to this format.
2. Alert lifecycle: raised → acknowledged → resolved, with who acknowledged and when.
   Alerts are shared across all screens.
3. Alerts panel on /twin and /control: open alerts sorted by severity; click to fly the
   camera to the source. Acknowledge from the phone.
4. Real board rule: if GW-01 goes offline, raise a critical "gateway offline" alert;
   resolve it automatically when it returns.
5. A rules page listing every rule in plain language ("Warn when a worker is within 3 m of
   a moving forklift for 1 s").
Tests: each migrated rule fires and resolves, and acknowledge/resolve works.
```

---

## S7: Commissioning (add a device to the site)

```
Read CLAUDE.md and /shared. Build device commissioning on /control (phone).

1. "Add device": scan a QR code with the phone camera (fallback: type the ID). The QR
   encodes {device_id, type, protocol}. Generate printable QR labels for simulated
   devices in tools/labels.py.
2. Then tap its position on the site map and pick the zone. The backend registers the
   device; it appears in the twin as "Awaiting first message" until its hello arrives.
3. The real board can be commissioned the same way: print GW-01's QR, scan it, place it.
   Its "awaiting" state must clear only on a real hello.
4. Decommission: remove a device, with confirmation; its history is kept.
5. Commissioning log: who added what, where and when.
Tests for registration, the awaiting state and that only a real hello clears it.
```

---

## S8: New factory planner

```
Read CLAUDE.md and /shared. Build /plan: a tool for planning a new site before building it.

1. Layout editor (top-down 2D, snapping grid): place zones, racks, docks, chargers,
   machines and lanes; the waypoint graph is generated from lanes. Save as a site layout
   in the same format as layout.json.
2. Capacity simulation: inputs are trucks per hour, pallets per truck, forklifts, docks
   and machine cycle times. Run the existing movement engine faster than real time on the
   draft layout and report dock waiting time, forklift utilisation, queue hotspots
   (shown as a heat map) and throughput. Compare two layouts side by side.
3. Device plan: from the layout, propose a device list (badges per worker, machine
   monitors per machine, door and occupancy sensors per dock, env sensors per cold room,
   gateways sized by coverage radius) with counts, protocols and a bill of materials.
   Gateway coverage circles drawn on the plan.
4. "Create site from plan": the plan becomes a new site in the twin with all devices in
   "planned" state, ready for commissioning (S7).
5. Template: duplicate an existing site as the starting point for a new one.
Tests: graph generation from lanes, simulation determinism with a fixed seed, device plan counts.
```

---

## S9: Firmware lifecycle view

```
Read CLAUDE.md and /shared. Add firmware lifecycle to /fleet.

1. Firmware column and a "Firmware" tab: versions in use per device type, devices on old
   versions, the real GW-01's version from its hello (real data).
2. Update campaigns for simulated devices: choose a type and target version, roll out in
   waves (10% → 50% → 100%), with simulated success/failure and automatic pause if the
   failure rate exceeds a threshold. Everything here is labelled SIM.
3. For GW-01, show the real version only, plus a note describing how a real over-the-air
   update would be done on the SiWx917 (to be researched and confirmed in the SDK docs;
   do not claim it is implemented).
4. Security panel: which devices use TLS to the broker and broker credentials, and which
   still connect anonymously, as an honest checklist.
Tests for wave progression and the automatic pause.
```

---

## S10: Demo and story hardening

```
Read CLAUDE.md and DEMO.md. Prepare the site demo.

1. Update DEMO.md with a 5-minute run:
   - Real board first: GW-01 online, button press moves FL-01, LED confirmation,
     Wi-Fi drop and recovery.
   - Switch to FAC-01: production running, trigger "degrade" on M-01, abnormal vibration
     alert appears, acknowledge it from the phone.
   - Worker badge walks near a moving forklift: proximity warning.
   - Cold room door left open: alert, temperature rises.
   - /fleet: real vs simulated devices, needs attention.
   - /plan: show the new factory layout, run the capacity simulation, create the site.
2. A "demo scenario" runner that triggers each beat on cue from /control, plus reset.
3. Audit: list every value on every page with its source (device, sim, computed) and
   confirm no simulated value is ever shown as LIVE.
4. Performance: 60 fps with all zones, devices and overlays on; no memory growth over
   15 minutes. Report the numbers.
5. Update README: architecture diagram, what is real vs simulated, and the WareTrack credit.
```

---

## Suggested 3-day split

| When | Do |
|---|---|
| Day 1 | Firmware Steps A–B. Backup demo video with the fake board. |
| Day 2 | Firmware Steps C–D, then S0 and S1. |
| Day 3 morning | S2 and S3 (the strongest stories). |
| Day 3 afternoon | S10 demo prep, real demo video, wiring PDF export, rehearse. |

S4–S9 are the roadmap. Present them as one slide ("where this goes next") unless you
finish early. A working real board plus S0–S3 is a stronger submission than everything
half-built.
