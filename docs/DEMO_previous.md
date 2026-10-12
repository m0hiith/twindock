# Previous site and campus demo scripts

Kept for reference; [DEMO.md](../DEMO.md) is the current script.

## Site demo (5 minutes): the board, then the factory

Run after the 3-minute board demo above, or as its continuation. Everything in part 2 is
**simulated** (grey SIM badges) and is triggered from the phone: `/control` → **Demo** tab. The
projector stays on `/twin`.

**Extra setup** (T-10 min): a fourth terminal runs the simulator, which publishes every simulated
device of the site through the same broker:

```sh
.venv/bin/python tools/site_sim.py
```

On the projector, pick **FAC-01 Assembly** in the site selector (top bar), then check: 11/11
devices online on FAC-01, both machines Running, four workers walking. Production needs about
90 s of running to learn each machine's vibration baseline, so start the simulator at least
2 minutes before beat 2a. Phone → Demo → **Reset demo** right before you start.

| Time | You do | Audience sees | Say |
|---|---|---|---|
| 0:00 | **Part 1, real board.** Projector on WH-01. Press BTN1, then BTN0. | FL-01 selected and moving; the violet LIVE gateway. | "One thing on this map is real: the SiWx917. Everything else that's violet comes from it." |
| 0:30 | Dock a truck at Bay 1 from the phone (Move tab). | The real LED turns green after the board confirms. | "The twin only shows green once the board says so." |
| 0:50 | Unplug the router (see beat 4 above). | GW-01 offline after 15 s, critical alert *Gateway offline*; resolves on its own when the board is back. | "And when it's gone, we say so." |
| 1:30 | **Part 2.** Projector: site selector → **FAC-01**. | The factory: conveyor running, press and packer, workers in hi-vis, KPIs: units today, availability, OEE (hover for the formula). All SIM. | "Same tool, a factory next door. These devices are simulated, and the twin labels every one of them SIM." |
| 1:45 | Phone → Demo → **a. Degrade M-01**. | Within ~1 min the press shows a pulsing amber ring and an alert: *abnormal vibration compared with baseline*. Open M-01: the vibration line leaves the green baseline band. | "Each machine learned its own normal. This is a comparison with that, not a prediction." |
| 2:45 | Phone → **Alerts** tab → **Acknowledge**. | The projector's alert shows *Acknowledged by Control Room (phone)*. | "Shared by every screen: who acknowledged and when." |
| 3:00 | Phone → Demo → **b. Worker near a moving forklift**. | A forklift drives to the factory outbound while WK-02 walks that lane: amber, then red rings on both; a proximity alert; the safety panel counts it and the closest approach. | "Pedestrian near a moving forklift. A parked forklift never triggers this." |
| 3:40 | Phone → Demo → **d. Cold room door left open**. | After 60 s the door alert; the cold room warms past 5 °C and a temperature alert follows. | "Door left open, and the temperature already reacts." |
| 4:30 | Switch the projector to **/fleet**. | GW-01 (LIVE) first, simulated devices after; *Needs attention* lists the low-battery sensor. Optional: Demo → **e** makes AQ-01 go stale. | "Fleet view: real first, honest status for everything." |
| 5:00 | Phone → Demo → **Reset demo**. | Seed world, simulator back to normal. | "Thanks." |

Optional beat **c. Visitor walks into the press area**: WK-04 (visitor) enters the restricted press
area, giving a critical alert that resolves when they leave.

**Not built yet** (SITE_PROMPTS.md): cold room door/temperature *physics in 3D* (S4; the alerts work),
energy (S5), commissioning (S7), the planner `/plan` (S8), firmware campaigns (S9). Don't promise them in
the demo; present them as the roadmap slide.

### Site fallbacks

- **Devices show stale/offline**: the simulator isn't running. Start `tools/site_sim.py`; they recover within 10 s.
- **Degrade shows nothing after 2 min**: the baseline wasn't learned yet (machine card says *Learning baseline*). Wait, or reset the demo earlier next time.
- **No forklift moves for beat b**: all forklifts are busy (the Demo tab says so). Turn auto mode off, wait for them to stop, retry.
- **Beat buttons say "Not connected to the MQTT broker"**: the backend lost the broker; check terminal 1.

## Campus demo (6 minutes): the board, the campus, safety, emergencies

The full story. Part 1 is the **real** board; everything after it is **simulated** (grey SIM badges) and driven from the phone
(`/control` → **Demo** tab) while the projector shows **`/monitor`** (the control-room wall display) and, for one beat, `/twin`.
Rehearsal: run it once with `tools/fake_board.py` standing in for the board, then once with the real board.

**Setup (T-10 min):** broker, backend, frontend and the simulator (`.venv/bin/python tools/site_sim.py`) running, as above. Projector: `http://localhost:5173/monitor`
at 1920 × 1080. Phone: `/control` → Demo → **Reset demo**. Check the monitor's bottom strip (all SIM tiles populated, GW-01 tile violet and Online) and wait
2 minutes so the machines have learned their baselines.

| Time | You do | Audience sees | Say |
|---|---|---|---|
| 0:00 | **The real board.** Projector on `/monitor`; point at the right-most tile. Press **BTN1**, **BTN0** on the board. | The **GW-01 · real board** tile is violet LIVE and Online with its Wi-Fi level and age; it is the only violet thing on the page. FL-01 moves on the map after BTN0. | "One thing here is real: this SiWx917. Everything violet comes from it. Everything grey is simulated, and says so." |
| 0:40 | **The campus.** Hover the map; open the camera menu (top-left of the map): *Campus overview*, then *Raw material store*, then *Interiors* on the map. | The whole campus from above: gate and weighbridge, car park, admin, canteen, two factory lines, utilities, the hazmat store far in the corner, solar roofs. The building card shows hazard level, PPE, devices (SIM) with ages. | "Every building is a zone with its hazard level and the PPE it needs, and its own sensors. Vehicles and people use separate graphs and meet only at marked crossings." |
| 1:10 | **A truck through the gate.** Phone → Move tab → **TR-02** → Dock at bay → Bay 1. | TR-02 drives in past the boom barrier (it lifts), over the weighbridge, into the yard and backs into Bay 1. Dock-bay monitor DB-01 flips to occupied; the Logistics tile ticks. | "Gate, weighbridge, yard, dock. The same server plans it and every screen follows." |
| 1:50 | **A machine anomaly.** Phone → Demo → **a. Degrade M-01**. | Within a minute the press shows an amber ring and an alert: abnormal vibration compared with its own baseline. Production tile OEE reacts. | "Each machine learned its own normal. This compares with it; it doesn't predict failure." |
| 2:30 | **A worker falls, and cancels.** Phone → Demo → **4. Simulate fall**, then within 30 s **Worker cancels**. | A pre-alert opens: *Possible fall: waiting 30 s for the worker to cancel*; after the cancel it closes, **falls today 1 (1 cancelled)**. | "The badge asks first. A false alarm is counted but doesn't wake anyone." |
| 3:00 | **A fall that isn't cancelled.** **Simulate fall** again and wait 30 s. | Critical **Man down** with the zone and the nearest first-aider; a pulsing ring at the location on the map; the worker's position is shown *because* of the alert. | "Now it's real: location and the nearest first-aider. Only now does the system show where the worker is; otherwise it shows zone counts." Then **Close** on the safety card. |
| 3:30 | **A gas leak and an evacuation.** Phone → Demo → **b. Gas leak in the hazardous store**. Then on the projector press **Start evacuation drill**. | Critical **Gas alarm**; badges in and next to the store get *evacuate*; green dashed routes to a muster point away from the leak; the **headcount** counts up as badges reach the muster points and lists who is unaccounted for and where they were last. | "Routes are advice; the system closes and locks nothing. The headcount tells the incident lead who is still missing." Press **End** when it reads all accounted for. |
| 4:30 | **Power.** Phone → Demo → **a. Grid failure**; switch the projector to **/energy**. | Critical *Grid failure*; grid import 0, solar 0, the generator picks up the critical loads only; mains devices elsewhere stop reporting. **Reset demo**. | "The generator keeps the fire pump house and the hazmat store on. Solar is computed from the time of day, and is labelled that way." |
| 5:00 | **The kits.** Projector: **/kits**, then open **Worker badge**. | Cards for each kit (BUILT only for the forklift pack), the wiring page with true-size parts and the banner **Reference design · simulated**. | "Every asset type has a kit with real parts and a wiring plan. Only the forklift pack is built; the others are designs, and say so." |
| 5:30 | **Back to the monitoring centre.** Projector: **/monitor** → **Incident timeline** → **Daily report (PDF)**. | Every alert of the run with who acknowledged and how fast, then the one-page report. | "Everything we just did is in the log, with response times." |

Fallbacks: a beat button says "Not connected to the MQTT broker" → check the broker terminal. The man-down beat needs the previous pre-alert to be over (**Reset demo**).
No fall? WK-01's badge must be online (10/10 badges online on the safety card).

## Rehearsal with the fake board (no hardware)

Shows a red FAKE BOARD banner on every page. Never in front of an audience.

```sh
./scripts/run_broker.sh
./scripts/run_backend.sh
cd frontend && npm run dev
.venv/bin/python tools/fake_board.py      # then type: b1, b0, b0, off 40
```

`b0`/`b1` press the buttons, `off <s>` drops the fake Wi-Fi for that long and then flushes the
buffered status messages, exactly like beat 4.

## Where every number comes from

From the code audit for this demo. "Server" = world state owned by the backend (seed data plus the
movement engine; manual, auto or device units). "Device" = a real MQTT message from the board.

| On screen | Source |
|---|---|
| Unit positions, states, tasks, battery, cargo, speeds | Server. Battery is simulated at 20× speed (world.py) so it visibly changes in a demo. |
| Operator names, models, carriers, plates, SKUs | Seed data in `backend/world/layout.json`. |
| Gateway values (RSSI, uptime, IP, counters, sensors, LED and button states, BLE sightings) | Device, each shown with its age; missing ones say *Waiting for device* / *Not reported*. |
| LIVE badges | Units whose `source` is `device` (the gateway; forklifts tracked by a calibrated BLE tag). |
| KPI cards | Computed in the browser from server units. Deltas compare with the last world snapshot this screen received, so two screens opened at different times can show different deltas. |
| Shipment stepper | Derived from the truck's server state and cargo count. |
| Planned path and "9 m" in the Control Room | Path from the server's dry run; the metres are summed in the browser from layout coordinates. |
| Smooth motion between updates | Browser interpolation towards the latest server pose (no extrapolation; nothing moves without an update). |
| "Live 10:24" clock, "12s ago" ages | Server clock (offset from `server_ts_ms`). |
| Control Room log *Not delivered* | The browser's own verdict (no socket / no reply in 5 s), kept visually apart from server *Rejected*. |
| RSSI chart history on `/device` | Accumulated in the browser from real `ble_tracks` messages since the page opened. |
| BLE threshold suggestions on `/device` | Computed in the browser from your captures (stored in this browser only). |
| Violet BLE range ring around the gateway | Radius is a layout constant (`gateway.ble_range_m`), not measured; it brightens only while the board is online. |
| RGB LED colour mix, LED/button descriptions | Derived from confirmed LED0/LED1 states; mapping and wording from HARDWARE.md. |
| Site selector | Local to each screen; WH-01 and FAC-01 come from `backend/world/sites.json`. |
| Operator avatar | Static UI (no sign-in). |
| Everything on FAC-01, /fleet, /rules | See `docs/value_audit.md` (every value on every page, with its source). |
