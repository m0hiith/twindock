# TwinDock live demo (3 minutes)

For the presenter. The projector shows `/twin` from the laptop; you drive from your phone on
`/control` and from the board's two buttons. Every beat below is real: the board's LED and buttons,
its Wi-Fi drop and its buffered messages. If a beat fails, use its fallback line and move on;
never fake a board value.

## Readiness: do not demo until every box is ticked

| | Item | State on 2026-10-08 |
|---|---|---|
| ☐ | **Firmware flashed** (PROMPTS.md step 2): hello, status every 5 s with `reconnects`/`buffered`, buttons, LED commands with confirmations, offline buffer + replay | **Not started.** `firmware/` is empty. Beats 1–4 need it. |
| ☐ | **Board twin** (step 7): the 3D board in the gateway card | **Blocked** on `frontend/public/board/top.jpg` and the hotspot table in HARDWARE.md. Until then beat 3 uses the gateway inspect card's LED switch. |
| ☐ | Laptop has a **fixed IP** on the demo router (DHCP reservation), and the firmware points at it | The router reboot in beat 4 must not move the broker. |
| ☐ | **Router boot time** measured: power off → board back online | Beat 4 leaves about 45 s for it. Slower? See beat 4's alternative. |
| ☐ | Fake board **stopped**; no red FAKE BOARD banner anywhere | `tools/fake_board.py` is for rehearsal only. |
| ☐ | BLE zones: not used in this script | Leave `backend/world/ble_zones.json` with empty `zones` unless calibrated on site. |

## Setup (T-30 min)

1. Router on. Laptop, board and phone on its Wi-Fi.
2. On the laptop, three terminals:
   ```sh
   ./scripts/run_broker.sh        # prints the laptop IP; must match the firmware
   ./scripts/run_backend.sh
   cd frontend && npm run dev
   ```
3. Projector: open **`http://localhost:5173/twin`** on the laptop, full screen. Use `localhost`, not the
   LAN IP, so the projector keeps working while the router is off in beat 4.
4. Phone: open `http://<laptop-ip>:5173/control`, add it to the home screen.
5. Power the board. Within 5 s the gateway pin in the twin turns violet and the board shows
   **Online** in the Control Room's Gateway tab.
6. Phone → **Reset world** (top bar). This restores the seed: TR-01 docked at Bay 2 with 2 pallets,
   TR-02 waiting on the road, FL-01 on the main aisle with a 2-step plan (pick at Rack A1, load at
   Bay 2), nothing selected, auto mode off.
7. Check: LED off on the board, Bay 1 empty, no event-log warnings, phone **Live**.

The inspect card on the projector follows the **shared** selection: when the phone or BTN1 selects
something, the card switches to it. The script re-opens the gateway card at beat 3 for that reason.

## The run

Movement times are from the simulator at the default pace (`TWINDOCK_PACE=2.5`): the truck docks
in about 12 s, FL-01 picks in about 9 s and loads in about 13 s. Times marked ~ add talking time;
the real board adds its own Wi-Fi and LED latency, so re-time them in your first rehearsal.

| Time | You do | Audience sees | Say |
|---|---|---|---|
| 0:00 | Projector on `/twin`. | The isometric site, three KPI cards, the violet LIVE gateway. | "This is a live twin of a warehouse. The violet board is real: everything violet comes from that SiWx917 over Wi-Fi." |
| 0:15 | **Beat 1.** Phone: tap **TR-02** → **Dock at bay** → **Bay 1** → **Confirm move**. | Planned path on the phone, then TR-02 drives in and backs into Bay 1 on the projector. Trucks-on-site and Docks-in-use KPIs tick. | "I'm the yard manager. One tap sends the truck; the server plans the route and every screen follows." |
| ~0:30 | Hold the board up. | **The real LED turns green.** The phone's Gateway tab shows LED0 *On · confirmed*. | "The rule 'Bay 1 occupied' is on the server; it told the board, and the twin only shows green after the board confirms." |
| ~0:40 | **Beat 2.** Press **BTN1** on the board once. | FL-01 gets the blue selection frame and pill; the event log says *Selected FL-01*. Selection is shared, so it shows on the phone too. | "The board's buttons are a physical controller." |
| ~0:45 | Press **BTN0**. | FL-01 drives to Rack A1 and lifts PL-01. | "BTN0 runs the forklift's next task." |
| ~0:55 | Press **BTN0** again. | FL-01 carries PL-01 to Bay 2 and loads it onto TR-01; TR-01's cargo goes 2 → 3 in the shipment card. | |
| ~1:15 | **Beat 3.** Projector: click the **gateway pole** (or `/` → `GW-01`), then flip **LED1** in its card. | Spinner (*waiting for the board*), then **the real LED turns cyan** (green + blue: both channels of the one RGB LED). | "Commands go the other way too, and again the twin waits for the board to confirm." |
| ~1:30 | **Beat 4.** Unplug the **router's power**. | Phone goes Reconnecting (expected, it's on that Wi-Fi). After ~15–20 s the board card dims to **Offline**, the gateway ring fades, event: *Board offline*. The rest of the twin keeps running on the laptop. | "The board just lost its network. It keeps measuring and buffers its status messages on the chip." |
| ~1:55 | Plug the router back in. Keep talking while it boots. | — | "Nothing in the twin is invented while it's away; you see the last values, greyed, with their age." |
| ~2:40 | — | Board **Online** again; **Reconnects +1** and **Flushed on last reconnect: N msgs** in the gateway card; phone reconnects. | "And here are the messages it saved while offline, delivered on reconnect." |
| 3:00 | Phone → **Reset world**. | The seed world snaps back. | "Thanks." |

### Fallbacks

- **Truck doesn't move**: the phone shows the server's reason (e.g. *Bay 1 is occupied*). Reset world and retry once.
- **LED stays pending > 5 s**: the backend logs *LED0: no confirmation from the board within 5 s* and retries after 30 s. Say "the board didn't confirm, so the twin won't pretend" and continue.
- **BTN presses do nothing**: check the event log on the phone. *no forklift selected* means press BTN1 first; *busy* means wait for the forklift.
- **Router takes longer than ~45 s to boot**: talk through the offline state. If you measured it in advance and it's slow, use the router's Wi-Fi on/off button (if it has one) instead of the power plug: same effect on the board, much faster.
- **Projector browser dies**: reopen `localhost:5173/twin`; it rebuilds from the server's snapshot.

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
| Site selector, operator avatar | Static UI (one site, no sign-in). |
