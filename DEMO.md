# TwinDock demo: the real board, then a factory that behaves like one

Two parts. **Part 1** (3 min, laptop) is the real SiWx917 board: every violet value comes from it. **Part 2** (6 min,
the hosted link or the laptop without the board) is the simulated campus: every value is SIM, and every beat is a
cause followed by its effects, produced by a model you can name. The models and parameters are on `/model` and in
[docs/model_card.md](docs/model_card.md).

# Part 1: the real board (laptop)

For the presenter. The projector shows `/twin` from the laptop; you drive from your phone on
`/control` and from the board's two buttons. Every beat below is real: the board's LED and buttons,
its Wi-Fi drop and its buffered messages. If a beat fails, use its fallback line and move on;
never fake a board value.

## Readiness: do not demo until every box is ticked

| | Item | State on 2026-10-08 |
|---|---|---|
| ☐ | **Firmware flashed** (PROMPTS.md step 2): hello, status every 5 s with `reconnects`/`buffered`, buttons, LED commands with confirmations, offline buffer + replay | **Steps A–D written and building, untested on hardware** (2026-10-10, `firmware/TESTING.md`). Steps E (BLE) and F (offline buffer + replay, reconnects) are not written: beat 4's "Flushed on last reconnect" needs F. Update the NWP firmware first (HARDWARE.md). |
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

# Part 2: the factory, cause and effect (hosted)

**Where:** the hosted link (Hugging Face or Render; see [docs/deploy.md](docs/deploy.md)), or the laptop with the
board unplugged. The bottom of every page says "Hosted demo · Simulated factory": every value here is SIM.
Speeds ×5 and ×20 only work while no real board is online.

**Before you start (T-5 min):**
- Open the link once, so a sleeping free host wakes up. It fast-forwards 45 simulated minutes on start, so the line
  is running, the compressor has cycled and trucks are mid-route.
- Check the top-bar clock is **×1**. Then open `/twin` on the projector and `/control` on the phone.
- Prefer a time in **shift A or B** (06:00–22:00 site time). The night crew has no mechanic, so the bearing work
  order would wait for the morning, exactly as it would in a real plant.
- Avoid the meal breaks (12:00–12:30, 19:30–20:00): the line stands still in them.

| Time | You do | Audience sees | Say | Model and parameters behind it |
|---|---|---|---|---|
| 0:00 | Projector `/twin`, factory view. Phone `/control` → **Factory**. | Four machines running or blocked, OEE, the compressor cycling, people on their rounds. | "This factory has been running for 45 minutes. Nothing here is a random number: every value has a cause." | Warm start (`TWINDOCK_WARM_START_MIN` 45, seed from the date). Shift calendar `production.shifts.*`; line press → buffer (12) → packer (`production.material.buffer_capacity`): the 6 s press is blocked behind the 8 s packer. |
| 0:30 | **Bearing, 1/4.** Phone → **Demo** → **Degrade M-01**. | Nothing yet. | "I've seeded a bearing defect in the press. Watch its vibration." | `production.wear.demo_defect_rate_per_s` 0.003/s; wear grows as dw/dt = r(1 + 3w) (`wear.acceleration` 3). |
| ~1:15 | Click **M-01** on the projector. | Vibration rising above its learned band; the machine's ISO zone moves from B towards C; an **Abnormal vibration** alert. | "The twin learned this press's own normal and sees it leave it. In this plant that really predicts a failure." | Vibration = healthy (1.1 mm/s, ISO 10816-1 class I zone B) + 4 mm/s × w² (`wear.vibration_mm_s_at_limit`). Baseline z-score > 3 for 10 samples (`sites.json production.z_threshold`, `window_samples`). |
| ~1:30 | **Bearing, 2/4.** Phone → **Maintenance**. | Work order **WO-0001 Bearing change · Needs approval**, with a decision card: "Stop M-01 for a bearing change (about 25 min)". | "Stopping production is a person's decision. The twin recommends; I approve." Tap **Approve**. | `backend/twindock/control.py`; `sites.json cmms.bearing_change_min` 25. |
| ~1:45 | Watch the projector. | The mechanic (WK-06 on shift A, WK-15 on B) walks from the workshop along the walkways to the press. | "The technician's badge walks the real walkways. The job starts when the badge is at the machine." | People walk at 1.3 m/s (`people.walk_speed_mps`) on the pedestrian graph; arrival within 4 m (`cmms.arrive_m`); badge positions carry BLE error (σ 1.2 m, `sensors.badge.position`). |
| ~2:45 | **Bearing, 3/4.** When M-01 shows **Under maintenance**, set the top-bar speed to **×20**. | The 25-minute job passes in about 75 s; M-01 runs again; WO-0001 **Done**: "vibration before ~2.4 mm/s (baseline ~1.4) … new bearing fitted; baseline relearning". | "Cause, action, result: all in the log." Show **Automatic actions** in the Maintenance tab. | Repair resets wear to a new bearing (`wear.new` 0.02); the baseline relearns (90 s, `production.baseline_s`). Had I waited, the bearing would have failed at its own limit (normal around 1.0, `wear.limit`) and the work order would have closed as "broke down first". |
| ~4:00 | Speed back to **×1**. **Low air, 1/2.** Demo → **Compressor fault**. | CP-01 trips; header pressure falls ~0.06 bar/s; below 6 bar a **Low air pressure** alert, below 5 bar the presses and packers stop with alarm **Low air pressure**. | "The duty compressor tripped. The machines are still drawing air, so pressure falls." | Receiver: dP/dt = (Q_comp − Q_demand − Q_leak)·P_atm/(60·V), V 0.5 m³ (`air.receiver_m3`), machines 0.5/0.3 Nm³/min, leaks ∝ pressure. Trip at 5.0 bar, reset at 5.8 (`air.trip_bar`, `trip_reset_bar`). |
| ~4:30 | **Low air, 2/2.** Keep watching. | After its 15 s sequencer delay and a 6 s star-delta start, standby **CP-02 loads**; pressure recovers; above 5.8 bar the line restarts. | "The standby saved the line, but only after a real delay. That's why the dip happened at all." | `air.standby_start_bar` 6.2, `standby_start_delay_s` 15, `star_delta_s` 6, standby band 6.2–7.2 bar. |
| ~5:00 | **Grid failure.** Demo → **Grid failure**. Phone or projector → `/energy`. | Grid import 0; generator: start delay → cranking → running in 9 s, then transfer; critical zones stay on, the production line and EV chargers are shed; diesel starts falling. | "Mains is gone. The generator's controller confirms, cranks, runs up and transfers the critical loads within ten seconds." | AMF sequence: 2 s confirm, 3 s crank, 4 s run-up (`power.generator.*`, ISO 8528-12 / NFPA 110 type 10). Fuel 3.5 L/h + 0.24 L/kWh. Non-critical zones shed (`sites.json utilities.critical_zones`). |
| ~5:30 | Demo → **Reset demo** (restores the grid). | After 60 s stable mains the load transfers back; the generator cools down for 2 min, then stops. | "It doesn't jump back on the first second of mains: it waits, transfers, cools down." | `power.generator.retransfer_delay_s` 60, `cooldown_s` 120. |
| ~6:00 | **Truck, gate to dock.** Phone → **Logistics**. If no truck is due within a few minutes, use **×20** briefly. | A truck goes gate → **weighbridge** (ticket: gross = tare + its pallets) → yard queue → dock; forklifts unload it pallet by pallet. | "The weighbridge weight is the truck plus the pallets actually on it: 5.4 t + 4 × 455 kg." | Schedule slots + lognormal delay (median 6 min); check-in, weighbridge and paperwork times (`logistics.gate.*`); weights `logistics.trucks.tare_kg`, `logistics.pallets.kg`. Forklift batteries in Ah (`logistics.forklift.*`). |
| ~7:00 | **Shift report.** `/monitor` → **Shift report (PDF)**. | Output, OEE losses by reason (the bearing change, the air trip, the shed line), downtime with alarms, energy per carton, alerts with response times, work orders. | "Every number in this report is read back from the historian: nothing was set by hand." | `backend/twindock/report.py` over the SQLite historian (24 h kept, deadband-compressed). |
| ~7:30 | `/model`. | Every model, its equations, every parameter with its source, the validation run. | "And if you want to check any of it, it's all here." | `backend/sim/params/*.yaml` (datasheet / standard / typical / assumption counted); `docs/validation.json`. |

### Fallbacks

- **No anomaly after the degrade**: the press may be blocked (not cycling, so no wear). Wait 30 s, or degrade M-03 instead.
- **The work order waits ("no mechanical technician reachable")**: it's the night shift. Say so. That's the roster; approve it and show that it waits.
- **The bearing fails before you approve**: show the work order "broke down first" and the breakdown in the shift report. That is the cost of not acting on the warning.
- **Speed buttons greyed out**: a real board is online on this backend; board data always runs at ×1.
- **The free host was asleep**: the first load takes about a minute (container start + 45-minute warm start); the factory is running when it opens.

### Each beat's chain, in one line

- Bearing: seeded defect → wear ↑ → vibration ↑ (∝ w²) → z > 3 → alert → work order → a person approves → technician walks → maintenance → new bearing → baseline relearns.
- Low air: duty trip → supply < demand + leaks → pressure ↓ → < 6 bar alert → < 5 bar line stops → standby (after delay + start) → pressure ↑ → > 5.8 bar line restarts.
- Grid: mains lost → AMF confirm → crank → run-up → transfer critical bus → non-critical shed → fuel ↓; mains back → wait 60 s → retransfer → cool-down → stop.
- Truck: slot + delay → gate → weighbridge (tare + cargo) → queue → dock → forklifts unload (Ah drawn) → paperwork → weighbridge out → gone.
