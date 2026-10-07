# Claude Code prompts for TwinDock

Put `CLAUDE.md` in the repo root first. Run these prompts in order, one per session or step.
Do not move to the next prompt until the current one works and is committed.

---

## Prompt 0: Hardware inventory (do this before any code)

```
Read CLAUDE.md. Before writing any code, help me build HARDWARE.md, the verified inventory
of my physical board.

My kit: [PASTE THE EXACT PART NUMBERS PRINTED ON THE BOARDS, e.g. radio board BRDxxxxA
on mainboard BRDxxxxA]. My SDK: WiSeConnect [version] in Simplicity Studio [version].
The SDK is installed at: [PATH].

1. Search the SDK folder for this board's config files (board/BSP headers, pin definitions,
   sl_si91x_led / button instance configs) and list every user LED, user button and onboard
   sensor that actually exists, with its SDK instance name and pin.
2. List anything the user guide mentions that you could NOT confirm in the SDK as
   "unverified", and ask me to check it.
3. Write HARDWARE.md with: kit identity, LEDs, buttons, sensors, how the board is powered,
   and an empty table for hotspot positions (% of photo width/height) that I will fill in
   after taking a top-down photo of the board.
Do not invent anything. If unsure, ask me.
```

---

## Prompt 1: Repo scaffold and message contract

```
Read CLAUDE.md and HARDWARE.md. Create the repo structure from CLAUDE.md.

1. In /shared, write schema.md and JSON Schema files for every MQTT topic and every
   WebSocket message (server→client: world_snapshot, unit_update, gateway_update,
   selection_changed, command_ack; client→server: move_unit, select_unit, led_command,
   set_auto_mode).
2. Add a docker-compose.yml (or a plain script if Docker is not available) that runs
   Mosquitto on port 1883 with a mosquitto.conf allowing LAN connections.
3. Add a tools/fake_board.py script that publishes messages EXACTLY like the firmware will,
   so I can develop the backend before the firmware is ready. It must print a loud
   "FAKE BOARD" banner and set fw_version to "fake", and the UI must show that clearly.
   This tool is for development only and is never used in the demo.
4. README with how to run everything. Credit Dilum Sanjaya's WareTrack concept as design inspiration.
```

---

## Prompt 2: Firmware (open the Simplicity Studio project folder in Claude Code)

```
Read CLAUDE.md and HARDWARE.md. I created this project in Simplicity Studio from the
WiSeConnect MQTT client example for my board, and it builds and runs as-is.

Extend it step by step. After each step, stop so I can build, flash and test, and tell me
exactly what I should see in the serial console and in `mosquitto_sub -v -t 'twin/#'`.

Step A: Wi-Fi + MQTT connection to my broker (SSID, password, broker IP in a config header).
  Publish retained twin/gateway/hello with the board identity from HARDWARE.md.
Step B: twin/gateway/status every 5 s with real values from the SDK: uptime, Wi-Fi RSSI,
  connection state, IP, fw_version, msgs_sent, reconnects. If the SDK cannot give a value,
  leave the field out rather than inventing one, and tell me.
Step C: Button events on twin/gateway/button (with debounce; explain the debounce time).
Step D: Subscribe to twin/gateway/cmd/led, drive the real LED, then publish the real LED
  state on twin/gateway/led as confirmation.
Step E: BLE scanning alongside Wi-Fi. Report devices whose name starts with "TD-" on
  twin/gateway/ble every 2 s. Explain how the SDK handles Wi-Fi/BLE coexistence and why you
  chose the scan window and interval.
Step F: Resilience. If Wi-Fi or MQTT drops, reconnect with backoff, buffer up to 50 status
  messages in RAM with original timestamps, then flush them on reconnect with
  "replay": true on each flushed message (so the backend keeps them as history and never
  mistakes one for the current status), and report the count in "buffered" on the next
  live status. Increment "reconnects".

Use only APIs that exist in my installed SDK; search the SDK headers to confirm every
function you call. Explain every function you add in a short comment so I can answer
interview questions about it.
```

---

## Prompt 3: Backend world engine

```
Read CLAUDE.md and /shared. Build the backend in /backend.

1. pydantic models for every entity and message.
2. backend/world/layout.json: a believable small yard and warehouse. 3 docks (Bay 1–3),
   2 rack rows (A, B) with 4 slots each, 2 chargers, zones A–C, a gate, a truck lane,
   and a waypoint graph with lanes connecting everything. Seed: 4 forklifts, 2 trucks
   (one docked at Bay 2, one inbound; Bay 1 starts free so LED0 starts off), 12 pallets, 1 gateway.
3. Movement engine at 20 Hz: units follow shortest paths on the graph at the speeds in
   CLAUDE.md, with smooth heading. Validate moves (a truck can only target docks or the
   gate, a forklift cannot pick a pallet that is already carried, a dock holds one truck).
4. MQTT bridge (aiomqtt): ingest gateway topics into gateway state with receive time,
   mark stale after 15 s, map BTN0/BTN1 to the actions in CLAUDE.md, drive LED0 from
   the Bay 1 rule, forward led_command from clients to twin/gateway/cmd/led.
5. WebSocket hub at /ws: send a world_snapshot on connect, then deltas. Broadcast shared
   selection so every screen highlights the same unit.
6. Auto mode (off by default) that gives idle forklifts sensible pick→carry→load tasks,
   marking those units source "auto".
7. Tests for pathfinding, move validation and the button mapping.
```

---

## Prompt 4: 3D scene

```
Read CLAUDE.md, especially the visual design spec. Build the 3D scene in /frontend
(Vite + React + TS + R3F + drei + zustand + Tailwind).

1. theme.ts with every token from CLAUDE.md.
2. Procedural low-poly models as separate components: Warehouse (ribbed roof, roll-up
   doors D1–D3), Rack, Pallet with boxes (instanced), Forklift, BoxTruck (with our own
   TwinDock wordmark), Container, Tree, Road with dashed lines, floor zone outlines,
   Charger, GatewayPole with violet range ring.
3. Orthographic isometric camera with the limits in CLAUDE.md, soft shadows, 60 fps target.
4. Render units from the zustand store fed by the WebSocket; interpolate positions
   between server updates for smooth motion. Never move a unit without a server update.
5. Selection: corner-bracket ground frame plus floating pill label; hover outline;
   map pins for the active destination.
Take screenshots while you work (if you can) and compare against the design spec. Fix
anything that looks cluttered, mismatched in style, or cartoonish.
```

---

## Prompt 5: HUD (/twin page)

```
Read CLAUDE.md. Build the HUD over the 3D scene on the /twin route, matching the layout
diagram: top bar (logo, search with "/" shortcut, site selector, Live clock, notifications,
user), three KPI cards computed from real world state, map controls column, inspect card,
shipment tracking stepper + shipment card, and the Docks/Forklifts/Trucks tabbed panel.

All numbers come from the store. Clicking a row selects and centers the unit; clicking a unit
opens its inspect card. The "Live" pill turns grey with "Reconnecting" if the WebSocket drops.
Device-sourced units always carry the violet LIVE badge.
```

---

## Prompt 6: Control Room (/control page)

```
Read CLAUDE.md. Build the /control route: the operator's manual control page.
It must work well on a phone, because I will control the twin from my phone during the demo
while the /twin view is on the projector.

1. Simplified top-down 2D map of the same layout (SVG), showing all units live.
2. Tap a unit to select it (shared selection with /twin). Then tap a destination node
   (dock, rack slot, charger, zone, gate) to send move_unit. Show the planned path before
   confirming. Invalid destinations are disabled with a short reason.
3. Quick actions for the selected forklift: pick pallet, load onto docked truck, go charge.
   For trucks: dock at bay, depart.
4. Toggle for auto mode, and an "Event log" of every command with its ack/reject.
5. A gateway panel with LED toggles (pending until the board confirms) and live button
   indicators that light up when the physical buttons are pressed.
Every command goes to the server; the UI only updates from server messages.
```

---

## Prompt 7: Board twin

```
Read CLAUDE.md and HARDWARE.md. I added a top-down photo of my board at
frontend/public/board/top.jpg and filled in the hotspot positions in HARDWARE.md.

Build BoardTwin: a 3D model of the board (thin box with the photo texture, correct aspect
ratio, slight PCB thickness, rounded edges). Add hotspots exactly at the HARDWARE.md positions,
for only the LEDs and buttons listed there. Buttons depress on real button messages; LEDs glow
with bloom only on confirmed LED messages; clicking an LED sends led_command and shows pending;
a violet pulse plays on each BLE message; offline state after 15 s stale, with "Last seen Xs ago".

Show it in the gateway inspect card (rotatable, small), and on a /device page at large size
next to: status values with their ages, a live RSSI chart from real status messages, the BLE
sightings table, buffered and reconnect counters, and a raw MQTT message log.
```

---

## Prompt 8: BLE tags as live forklifts

```
Read CLAUDE.md. Map BLE sightings to units: a tag named TD-FL01 is forklift FL-01.
In the backend, smooth RSSI with a moving average over the last 5 readings and switch the
unit's zone only when the new zone is stable for 3 s (hysteresis), using calibrated
thresholds in a config file. Add a /device calibration helper that shows live smoothed RSSI
per tag so I can set thresholds by standing at each spot. Such units have source "device"
and show the violet LIVE badge; manual commands for them are disabled.
```

---

## Prompt 9: Demo hardening

```
Read CLAUDE.md. Prepare for a live demo:
1. A demo script (DEMO.md) of a 3-minute run: phone moves a truck to Bay 1 → LED0 turns on
   on the real board → BTN0 press drives FL-01 to pick and load → click LED1 in the twin →
   real LED turns on → unplug the router → board twin goes offline, data fades → reconnect →
   buffered messages flush and the counter shows it.
2. A reset endpoint and button that restores the seed world in one click.
3. Check the whole app for any value that is not traceable to the server state or a device
   message, and list it.
4. Performance pass: confirm 60 fps, no memory growth over 15 minutes.
```
