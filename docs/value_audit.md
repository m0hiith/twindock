# Value-source audit

SITE_PROMPTS.md S10, item 3: every value on every page and where it comes from. Last checked
2026-10-10 against the code at the commit that adds this file.

**Sources**

- **Device**: a real MQTT message from the SiWx917 board (`twin/gateway/*`), shown with its age.
  The only things that can be LIVE (violet) are this board (GW-01) and what it reports: its LEDs,
  buttons, sensors, BLE sightings, forklifts tracked by a calibrated BLE tag, and RB-01 (a phone
  advertising `TD-BADGE-01`, seen by the board's BLE scan).
- **Sim**: produced by `tools/site_sim.py` on `twin/<site>/<device>/<channel>`. The schemas force
  `source: "sim"`, and the UI shows a grey SIM badge.
- **Server**: world state owned by the backend: seed data in `layout.json`/`sites.json` plus the
  movement engine (manual, auto or device-driven units).
- **Computed**: derived by the backend or the browser from the above; the formula is stated.

**How it is enforced**

- `frontend/src/audit.test.ts` lists every place that can render violet LIVE styling, each with the
  reason it can only show real data. A new usage fails `npm test` until it is reviewed. It also
  checks that the site-twin views (production, workers, safety, factory) contain no LIVE styling,
  and that `deviceTone()` can never return the live tone for simulated data.
- `backend/tests/test_audit.py`: after feeding the board and every simulated device, the only
  device-sourced unit is GW-01 and the only device-sourced devices are GW-01 and RB-01; machines
  and workers are always `sim`; every `twin/<site>/…` schema has `source` constant `"sim"`.
- `backend/tests/test_sites.py::test_sim_messages_never_touch_the_real_board`: sim messages, even
  ones naming GW-01, never change gateway state, LED state, or produce board commands.

Result: **no simulated value is shown as LIVE** anywhere.

## /twin, WH-01 (warehouse)

| Value | Source |
|---|---|
| Units: positions, states, tasks, battery, cargo, speed | Server (battery drains 20× faster than a real shift) |
| Operator names, models, carriers, plates, SKUs | Server (seed in `layout.json`) |
| KPI cards (stock, trucks on site, docks in use) and deltas | Computed in the browser from server units; deltas compare with this screen's last snapshot |
| Shipment stepper | Computed from the truck's server state and cargo count |
| Gateway pole: violet ring brightness, status LED | Device (`gateway.online`: status within 15 s) |
| Gateway inspect card: RSSI, uptime, IP, counters, sensors, LED, buttons | Device, each with its age; missing values say so |
| LIVE badge on units | Device: `unit.source === "device"` (GW-01; forklifts with a calibrated BLE tag) |
| FAKE BOARD banner | Device hello says `board: "FAKE"` (tools/fake_board.py) |
| Event log (bell) | Server events (rules, board, BTN0/1, auto mode) |

## /twin, FAC-01 (factory)

| Value | Source |
|---|---|
| Machine states, stack lights, conveyor and press motion | Sim (machine monitors MM-01, MM-02); no fresh data → "No data", nothing moves |
| Units today, availability, OEE (A, P, Q) KPI cards | Computed by the backend from sim readings. OEE = A × P × Q; the formula shows on hover |
| Pallets out / on the next pallet | Computed: every 6 packer units = one pallet (`sites.json` → production) |
| FG-xx pallets at the outbound spot | Server, created from sim production (pallet `source: "sim"`) |
| Machine card: cycle time, current, vibration, z, baseline band, last fault | Sim readings with their age; baseline, z and band computed by the backend |
| "Abnormal compared with baseline" | Computed: rolling z-score of sim vibration vs the learned baseline. Not a failure prediction |
| Workers (people in hi-vis) and their positions | Sim badges BG-01…04 (not drawn without a fresh position) |
| Worker card: role, badge, zone, nearest forklift | Sim badge + computed zone; **name hidden** (no sign-in) |
| Safety panel: workers per zone, warnings today, closest approach | Computed from sim badge positions and server forklift positions |
| Amber/red safety rings | Computed: badge within 3 m / 1.5 m of a moving forklift, or in a restricted zone |
| Devices online card | Computed from device statuses (all SIM on FAC-01) |
| Device pucks and their status ring | Sim device status (online ≤ 15 s, stale ≤ 60 s, offline) |
| Device inspect card | Sim readings, battery, signal, firmware (`sim-x.y`), each with age |
| Alerts card | Rules engine over the above (see /rules) |

## /control

| Tab | Values | Source |
|---|---|---|
| Move | Units, planned path, distance | Server (dry run); metres summed in the browser from layout coordinates |
| Gateway | Board online, LEDs (confirmed + pending), buttons, counters | Device, with ages. An LED shows on only after the board confirms |
| Factory | Machine state, vibration, z, units, OEE | Sim + computed (as on /twin). Buttons only reach the simulator |
| Demo | GW-01 online state | Device. The real-board beats are done by hand; nothing here can fake them |
| Demo | Site beats | Commands to the simulator and the movement engine, never the board |
| Alerts | Open/resolved alerts, acknowledged by | Rules engine; "by" is the screen's name (no sign-in) |
| Event log | Server events | Server |

## /fleet

| Value | Source |
|---|---|
| GW-01 row: status, signal, firmware, last seen | Device (status age; firmware from the board's hello; RSSI from its status) |
| GW-01 battery | "—": the board reports no battery and the twin doesn't guess |
| RB-01 row | Device: the board's BLE scan of `TD-BADGE-01` (smoothed RSSI, last seen) |
| Every other row | Sim (SIM badge, `fw_version sim-x.y`), status computed from message age |
| Summary strip, Needs attention | Computed from device statuses and batteries (< 20 %) |
| Side panel history chart | Backend's last 240 values of that channel (for GW-01, only RSSI from its own status) |
| Mini-map | Server geometry (`layout.json`, `sites.json`) + the device's position |

## /rules

| Value | Source |
|---|---|
| Rule list and plain-language text | `backend/rules/*.yaml` |
| Alerts and history | Rules engine over device, sim and computed facts; a missing or stale value never fires a rule |

## /device

Unchanged by the site twin: BLE calibration (device: real `ble_tracks`), RSSI chart (device),
threshold suggestions (computed in the browser).

## /kits and /wiring/:kit_id (factory extension, audited 2026-10-11)

| Value | Source |
|---|---|
| Kit cards: asset type, radio, power, part count, BOM cost, devices using it | `hardware/kits/*.json` (design data). Costs are rough budget estimates, not quotes; "≥" means some parts have no price |
| Status badge and banner | Kit status: **BUILT** only for `fl01_sensor_pack` ("Built and verified"); every other kit shows "Reference design · simulated". Never violet |
| Readings on the FL-01 kit page | Device: `gateway.sensors` while the board is online, "Waiting for firmware" otherwise (unchanged) |
| Readings on a reference kit page | None: the part panel says the design is not built and its devices report simulated values (SIM) elsewhere |
| Part drawings and sizes | Procedural SVG at 10 px per mm; `dims_evidence` says datasheet or typical |
| Third-party part numbers, addresses, supply ranges, costs | From memory, marked unverified in each kit and its open questions; Silicon Labs boards checked on silabs.com |
| /parts | Visual test page, no data |

## /monitor, /energy and the building card (factory extension)

| Value | Source |
|---|---|
| Campus map, alert rings | Server geometry and open alerts (rules engine) |
| Open alerts, incident timeline, response and resolution times | Rules engine log (last 24 h); times computed from who acknowledged and when |
| Daily safety report (PDF) | Computed in the browser from `GET /api/monitor`; roles and zones only |
| Worker safety card | Computed from simulated badges (SIM). Positions only during an alert or evacuation; otherwise zone counts |
| Evacuation headcount and routes | Computed from badge positions and the pedestrian graph (SIM); advice only |
| Production, device health, air quality tiles | SIM devices, computed |
| Logistics tile | Server units |
| Energy tile, `/energy` | Simulated meters (SIM). Solar is **computed** from the time of day and the design size (never measured). "Other loads" is the incomer minus the metered feeders. Today vs yesterday starts counting when the backend starts: "no data yet" until a day has passed. kWh per unit = production feeder energy ÷ units since the backend started |
| GW-01 tile | **Device** (LIVE, violet): only from the board's own messages, "Waiting for device" until one arrives |
| Building card | Zone attributes (design data), people count (count only), KPIs computed from the building's SIM devices, device readings with age (SIM) |
| Rooftop solar and utility animations | Driven by simulated devices (generator running, compressor loaded, tank levels) and the time of day |

## /wiring (FL-01)

Wiring readings (device: `gateway.sensors`), unchanged.
