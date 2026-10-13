# Screenshot checklist

Captured on 2026-10-13 by `tools/screenshots/capture.py` from a freshly started local app (backend with the embedded
simulator, no MQTT broker, no board; Vite dev server). Every image was opened and checked by eye. Desktop images are
1440 × 900 at 1×; the phone image is 390 × 844 at 2×. No image is cropped or edited.

Conditions that hold for every image: the real board (GW-01) was **not connected**, so it shows "Waiting for device",
"Board offline" or "Never"; the FAKE BOARD banner never appears (the script stops if it does); auto mode was on, so the
warehouse and factory units move on their own (`source: "auto"`).

| Image | What it shows | LIVE / SIM labels | Result |
|---|---|---|---|
| `twin-overview.png` | `/twin`, warehouse (WH-01): KPI cards, alerts, minimap, shipment stepper, forklift table, the 3D yard with trucks, forklifts and racks | Gateway pole's violet ring is faint (board offline); warehouse units carry no badge (server world state) | Pass |
| `twin-inspect-forklift.png` | `/twin` with FL-01 selected through search: inspect card (battery, model, location, next step, source), pill label in the scene | Source row reads "Auto mode" | Pass. Note: the floating pill label sits partly behind the map controls at this zoom |
| `campus-factory.png` | `/twin` switched to FAC-01: production KPIs, worker safety panel, alerts, the factory, utilities and ETP in 3D | SIM on every factory KPI and on worker safety | Pass |
| `control-room.png` | `/control` desktop: unit chips, warehouse map, Move tab with destinations | Gateway range ring in violet on the map | Pass after a fix: the side panel ran off the right edge at 1440 px (commit 12fd77e) |
| `control-phone.png` | `/control` at 390 × 844: chips, map, Move / Gateway / Factory / Maintenance / Logistics tabs, FL-01 actions | n/a | Pass. Unit labels overlap where FL-02 and FL-03 share the chargers |
| `device-page.png` | `/device`: GW-01 Wi-Fi signal chart, BLE tag table, calibration capture | LIVE on GW-01 | Pass. Empty by design: no board, so no RSSI history and no TD- tags ("Collecting history…", "No TD- tags in the latest scan") |
| `wiring-breadboard-fl01.png` | `/wiring/fl01_sensor_pack`, breadboard view: BRD2605A at true proportions, Qwiic chain to VL53L1X and NAU7802, load cell | "Built and verified" banner; parts read "Waiting for firmware" or "Not connected yet" | Pass |
| `wiring-schematic-fl01.png` | Same kit, schematic: I2C bus with Si7021 0x40, VEML6035 0x29, VL53L1X 0x29 → 0x30 at boot, NAU7802 0x2A; SPI IMU; control lines | as above | Pass |
| `wiring-reference-kit.png` | `/wiring/machine_monitor`, breadboard view | "Simulated kit" banner, "readings come from the simulator (SIM)" | Pass |
| `kits-index.png` | `/kits`: one card per kit (radio, power, parts, bill of materials, used by) | FL-01 BUILT, every other kit SIM | Pass |
| `fleet.png` | `/fleet` with the "Needs attention" filter: GW-01 and RB-01 first (offline, never seen), then off-shift badges | LIVE on GW-01 and RB-01, SIM on the rest; "2 real (LIVE) · 88 simulated (SIM)" | Pass |
| `monitor.png` | `/monitor`: whole campus, open alerts, worker safety, KPI strip | SIM on every KPI; GW-01 tile LIVE with "Waiting for device" | Pass |
| `rules.png` | `/rules`: 32 rules in plain language, alerts list with acknowledge and resolved items | n/a | Pass |
| `energy.png` | `/energy`: demand, solar, grid import, generator, PF, 15-min demand, cost, kW by building, how the numbers are made | SIM on every card | Pass |
| `model.png` | `/model`: parameter counts by source, the 4-hour validation (all pass), model card | n/a | Pass |
| `forklift-route.mp4` | 13 s of `/twin`: FL-01 is sent to FAC_AISLE_2 with a `move_unit` intent (as from `/control`), waits for FL-04 to clear the lane, then drives | Inspect card shows "Source: Manual" | Pass |

Not captured: `planner.png` (`/plan`). That page does not exist yet (site step S8 is on the roadmap), so there is no
planner and no capacity simulation to screenshot. See [../readme_blockers.md](../readme_blockers.md).

Re-capture:

```sh
.venv/bin/pip install -r tools/screenshots/requirements.txt && .venv/bin/python -m playwright install chromium   # once
.venv/bin/python tools/screenshots/capture.py                          # app on http://localhost:5173
.venv/bin/python tools/screenshots/capture.py --base http://localhost:7860   # the container
```
