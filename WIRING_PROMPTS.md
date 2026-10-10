# Forklift sensor pack + wiring view: Claude Code prompts

Run these after firmware Prompt 2 Steps A–D work on the real board. The wiring view is only
honest if the sensors it shows are really wired and really read by your firmware.

Goal: the SiWx917 Dev Kit (BRD2605A) is mounted on forklift FL-01 as its "sensor pack".
Its on-board sensors plus two Qwiic sensors make FL-01 a real, live unit in the twin, and a
Tinkercad-style wiring page shows exactly how everything is connected.

Sensor pack:

| Sensor | Where | Forklift use |
|---|---|---|
| ICM-40627 6-axis IMU (SPI) | On board | Moving vs idle, impact/collision alert, tilt |
| Si7021 temperature + humidity | On board | Ambient conditions at the forklift (cold-zone checks) |
| VEML6035 ambient light | On board | Aisle lighting level, inside vs outside |
| ICS-43434 microphones | On board | Skipped (decided 2026-10-10) |
| VL53L1X distance (Qwiic) | External | Pallet present on the forks |
| NAU7802 + small load cell (Qwiic) | External | Load on the forks (demo-scale weight) |

Status: W0 done (`hardware/wiring.json`, HARDWARE.md). Qwiic shares I2C2 with the on-board sensors;
the VL53L1X is moved from 0x29 to 0x30 at boot (sequence in HARDWARE.md and wiring.json).

---

## Prompt W0: Verify the sensors and create the single source of truth

```
Read CLAUDE.md and HARDWARE.md. My board is the SiWx917 Dev Kit BRD2605A.

1. From the board's BSP/config files in my WiSeConnect SDK and the BRD2605A user guide (UG581),
   confirm for each on-board sensor (ICM-40627, Si7021, VEML6035, ICS-43434): which bus it uses
   (I2C, SPI, I2S), the pins, its address if I2C, any enable/power pin, and which SDK driver or
   example exists for it. Mark anything you cannot confirm as "unverified" and ask me.
2. Confirm which pins the Qwiic connector uses and whether it shares a bus with on-board sensors.
   Check that VL53L1X and NAU7802 default addresses do not clash with anything on that bus, and
   that both run at the Qwiic voltage.
3. Create hardware/wiring.json as the single source of truth: every part (id, name, part number,
   location on-board/external, bus, address, pins), every connection (from pin, to pin, signal,
   wire color), and a status per part: "planned", "wired" or "verified" (verified = firmware has
   read a plausible value from it). Use the Qwiic color code: red 3.3 V, black GND, blue SDA,
   yellow SCL.
4. Add a JSON Schema for wiring.json in /shared and update HARDWARE.md to reference it.
Do not invent pins or addresses.
```

---

## Prompt W1: Firmware reads the sensors

```
Read CLAUDE.md, HARDWARE.md and hardware/wiring.json. Extend the firmware (Steps A–D already work).
Add one sensor at a time, and stop after each so I can flash and check the values in
`mosquitto_sub -v -t 'twin/#'`:

1. Si7021 → twin/gateway/sensor/temperature and /humidity every 5 s.
2. VEML6035 → /light (lux) every 5 s.
3. ICM-40627 → sample at a rate you justify; publish /motion every 1 s with
   {moving: bool, accel_rms_g, tilt_deg} and an immediate /impact event when acceleration
   exceeds a threshold in a config header. Explain the threshold and the moving/idle logic.
4. VL53L1X over Qwiic → /fork_distance (mm) every 500 ms.
5. NAU7802 over Qwiic → /fork_load (raw and calibrated grams) every 1 s, with a tare command
   on twin/gateway/cmd/tare and a two-point calibration I can run with a known weight.
6. Generate firmware/config/wiring_pins.h FROM hardware/wiring.json with a script
   (tools/gen_pins.py), so firmware pins and the wiring diagram can never disagree.

Every sensor message follows the contract (ts_ms, value, unit). If a sensor fails to respond,
publish a /sensor_error event and never send a made-up value. Use only SDK APIs that exist in my
install; comment why each rate and threshold was chosen.
```

---

## Prompt W2: Contract and backend

```
Read CLAUDE.md, /shared and hardware/wiring.json.

1. Add the new sensor topics and the tare command to /shared, regenerate types, and update
   CLAUDE.md in the same commit.
2. In the backend, attach the board's sensor pack to forklift FL-01 (configurable). FL-01 gets
   a sensors block with each value and its receive time. Rules:
   - moving/idle comes from the IMU, not from the movement engine, while the board is online
   - pallet on forks = fork_distance below a configurable threshold
   - fork load shown in grams with a "demo scale" note
   - an impact event creates a critical event and a notification
   - when the board is offline, sensor values go stale exactly like other board data
3. GET /api/wiring serves hardware/wiring.json, plus each part's latest reading and status.
4. Tests for the sensor rules, staleness and the impact event.
```

---

## Prompt W3: Tinkercad-style wiring page (/wiring)

```
Read CLAUDE.md and hardware/wiring.json. Build /wiring: an interactive, Tinkercad-style view of how
the sensor pack is connected, generated entirely from /api/wiring (no hard-coded parts or wires).

Three views with a toggle at the top: "Breadboard", "Schematic", "Parts list".

Breadboard view (SVG, pan and zoom):
- The real board drawn from frontend/public/board/top.jpg at true proportions, with its pads and
  the Qwiic connector positioned from wiring.json.
- External modules (VL53L1X, NAU7802, load cell) drawn as clean, generic flat SVG modules labeled
  with their part numbers, not copies of any vendor's artwork.
- Wires as smooth curves in their real colors (Qwiic: red 3.3 V, black GND, blue SDA, yellow SCL),
  routed so they do not cross components.
- On-board sensors shown as highlighted outlines on the board photo at their real positions.
- Hover a pin: name, signal, bus, address. Hover a wire: from → to and signal.
- Click a part: side panel with what it measures, why it is on the forklift, bus/address,
  status badge (planned / wired / verified), and its live reading with age.
- When a reading arrives, animate a short pulse along that part's data wire towards the board.

Schematic view: block schematic of the same data (SoC, buses, each sensor on its bus with address).

Parts list: table of every part with part number, quantity, location, bus, address and status.

Rules: a part with status "planned" is drawn dashed and greyed with "Not connected yet". Live
readings only from real messages; offline board = all readings greyed with age. Add "Export PNG"
and "Export PDF" for the current view. Match the CLAUDE.md design tokens and keep the page
usable on a laptop projector.
```

---

## Prompt W4: Connect it to the twin

```
Read CLAUDE.md. Integrate the sensor pack into the existing pages:
1. FL-01 inspect card on /twin: a "Sensor pack" section with motion, fork load, pallet on forks,
   temperature, light, each with age, the violet LIVE badge, and a "View wiring" button to /wiring.
2. In the 3D scene, FL-01 shows a small board mounted on its overhead guard, and a pallet appears
   on its forks only when fork_distance says one is there.
3. Impact events: a red pulse ring on FL-01 in the scene and an entry in notifications and the
   event log.
4. /device page: add the sensor readings with live charts (from real messages only) and the
   tare/calibrate controls for the load cell.
```

---

## Prompt W5: Consistency checks

```
Read CLAUDE.md. Add automated checks and run them:
1. wiring.json validates against its schema; no two connections drive the same pin; no I2C
   address clashes per bus; every external part's voltage matches its supply.
2. firmware/config/wiring_pins.h is up to date with wiring.json (fail if regenerating changes it).
3. Every sensor topic the firmware publishes exists in /shared and in wiring.json.
4. The /wiring page renders every part and connection in wiring.json (a test that counts them).
Report anything that does not match.
```

---

## Prompt W6: One-page hardware sheet for the panel

```
Read CLAUDE.md and hardware/wiring.json. Generate docs/hardware_sheet.pdf (one page, A4 landscape)
from the same data: the breadboard view image, the parts table, a short "what each sensor does on
the forklift" list, the data path (sensor → SiWx917 → Wi-Fi → MQTT → backend → twin), and the
measured numbers I have (button-to-screen latency, publish rates).
```
