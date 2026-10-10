# HARDWARE.md: verified inventory of the physical board

Status legend:
- **sdk-verified**: found in the WiSeConnect 3.5.3 board config for BRD2605A (file cited). Still needs a
  quick physical check by the developer (silkscreen label, location).
- **confirmed**: sdk-verified **and** confirmed by the developer on the physical board.
- **unverified**: mentioned in the user guide or product page only.

The UI and firmware may only expose rows that are **sdk-verified** or **confirmed**, and only the rows
listed under "Exposed in TwinDock".

SDK paths below are relative to `wiseconnect-3.5.3/components/board/silabs/`.

## Kit identity

| Field | Value | Source | Status |
|---|---|---|---|
| Kit | SiWx917-DK2605A (Wi-Fi 6 + BLE SoC Dev Kit) | developer | confirmed |
| Board | BRD2605A, revision A02 | `component/brd2605a.slcc` (`SL_BOARD_NAME "BRD2605A"`, `SL_BOARD_REV "A02"`) | sdk-verified (developer: check label) |
| Radio board | none (single board). `hello.radio_board = ""` | `brd2605a.slcc` | sdk-verified |
| SoC OPN | SiWG917M111MGTBA | `brd2605a.slcc` (`requires: siwg917m111mgtba`) | sdk-verified |
| Memory | Common flash mode, 8 MB external PSRAM, no external flash | `brd2605a.slcc` | sdk-verified |
| Console | VCOM over the onboard debugger USB | `brd2605a.slcc` tag `hardware:has:vcom` | sdk-verified |
| SDK | WiSeConnect 3.5.3, at `./wiseconnect-3.5.3` (also `~/Downloads/wiseconnect-3.5.3`) | on disk | confirmed |
| IDE | Simplicity Studio: _version? not found on this Mac yet (only the installer)_ | — | **open** |

## User LEDs

The board has **one RGB LED**, exposed by the SDK as a single instance `led0` with three channels.
There is no second user LED.

| Channel | SDK instance / API | GPIO | Source | Status |
|---|---|---|---|---|
| Red | `led0` red, `sl_si91x_rgb_led_on/off()` | HP GPIO 50 (port 3 pin 2, pad 14) | `config/brd2605a/sl_si91x_rgb_led_init_led0_config.h`, `RTE_Device_917.h` | sdk-verified |
| Green | `led0` green | HP GPIO 51 (port 3 pin 3, pad 15) | same | sdk-verified |
| Blue | `led0` blue | HP GPIO 15 (pad 8) | same | sdk-verified |

The official dev kit demo (`examples/si91x_soc/siwx917_dev_kit/sensors/rgb_led.c`) drives the channels
with `sl_si91x_rgb_led_on(&RED)` / `sl_si91x_rgb_led_off(&RED)` etc.

## User buttons

| UI name | SDK instance | GPIO | Interrupt | Source | Status |
|---|---|---|---|---|---|
| BTN0 | `btn0` (`sl_si91x_button_917`) | UULP_VBAT GPIO 2 | rise + fall edge | `config/brd2605a/sl_si91x_button_init_btn0_config.h` | sdk-verified |
| BTN1 | `btn1` (`sl_si91x_button_917`) | HP GPIO 49 (port 3 pin 1, pad 13) | rise + fall edge | `config/brd2605a/sl_si91x_button_init_btn1_config.h` | sdk-verified |

Rise and fall edge interrupts mean the firmware can report both `pressed` and `released`. Active
level is handled by the button driver (`sl_si91x_button_state()`), to be confirmed in step 2C.
The reset button is not a user button and is not exposed.

## Onboard sensors

Si7021, VEML6035 and ICM-40627 sit behind a switch controlled by **SENSOR_ENABLE** = UULP_VBAT GPIO 1
(`SENSOR_ENABLE_GPIO_PIN` in `RTE_Device_917.h`; UG581 3.4.1, 3.4.3, 3.4.4). Driving it high powers them
from VMCU *and* connects their I2C/SPI lines to the SoC; a pull-down keeps it low by default. The
microphones have their own enable (MIC_ENABLE = UULP_VBAT GPIO 0, UG581 3.4.2).

| Sensor | Part | Bus / address | Pins | SDK driver | Status |
|---|---|---|---|---|---|
| Relative humidity + temperature | Si7021 | I2C2 (ULP_I2C) / 0x40 | SDA ULP_GPIO_6, SCL ULP_GPIO_7 | `si70xx_sensor` | sdk-verified + UG581 |
| Ambient light | VEML6035 | I2C2 (ULP_I2C) / 0x29 | same; ALS_INT UULP_VBAT GPIO 3 | `veml6035` | sdk-verified + UG581 |
| 6-axis IMU | ICM-40627 | SPI (ULP SSI) | MOSI ULP_GPIO_1, MISO ULP_GPIO_2, SCK ULP_GPIO_8, CS ULP_GPIO_10, INT UULP_VBAT GPIO 3 | `sl_icm40627` | sdk-verified + UG581 (chip marking: check when photographing) |
| MEMS microphones | ICS-43434 x2 | I2S0 | GPIO 46/47/48 | `sl_si91x_mic` | UG581, **skipped** (not used by TwinDock) |

The IMU and light sensor share one interrupt line (UULP_VBAT GPIO 3). The IMU CS (ULP_GPIO_10) is also on
breakout pad 10.

## Forklift sensor pack: `hardware/wiring.json`

The sensor pack (Si7021, VEML6035, ICM-40627 on board, plus VL53L1X and NAU7802 with a load cell over
Qwiic) is described in **`hardware/wiring.json`**, validated by **`shared/schemas/hardware/wiring.json`**.
It is the single source of truth for parts, buses, addresses, pins, wires and the boot sequence.
Firmware pins (`tools/gen_pins.py`), the `/wiring` page and the hardware sheet are generated from it.
Every value carries `evidence` (`sdk-verified`, `user-guide`, `datasheet`, `confirmed`, `unverified`);
every part and connection carries `status` (`planned`, `wired`, `verified` = firmware has read a plausible value).
Status on 2026-10-10: SoC, Qwiic connector, Si7021, VEML6035, ICM-40627 and their PCB traces are
`wired` (connected by the board); VL53L1X, NAU7802, the load cell and the Qwiic cables are `planned`.
Nothing is `verified` yet. The `/wiring` page draws all of it (board outline from UG581 Figure 1.1
until the photo exists).

### Qwiic connector (UG581 3.6.2, Table 3.3)

| Qwiic pin | Connection | Wire |
|---|---|---|
| GND | GND | black |
| 3.3V | **VMCU** (not switched by SENSOR_ENABLE) | red |
| SDA | ULP_GPIO_6, shared with on-board I2C sensors and breakout pad 16 | blue |
| SCL | ULP_GPIO_7, shared with on-board I2C sensors and breakout pad 15 | yellow |

Daisy chain: board → VL53L1X → NAU7802 → load cell (4 wires: E+, E-, A-, A+).

### I2C2 addresses and the VL53L1X boot sequence

The VL53L1X powers up at **0x29**, the same as the VEML6035. Firmware moves it to **0x30** at boot:

1. Drive SENSOR_ENABLE low: Si7021/VEML6035 are unpowered and disconnected from the bus; Qwiic devices
   stay powered (VMCU).
2. Probe 0x30. If it answers with model ID 0xEACC (register 0x010F), the VL53L1X was already moved
   (MCU-only reset does not cut its power): go to step 5.
3. Probe 0x29, check model ID 0xEACC, write 0x30 to `I2C_SLAVE__DEVICE_ADDRESS` (register 0x0001).
4. Confirm at 0x30. If neither address answers: `sensor_error` for fork_distance, no value published.
5. Drive SENSOR_ENABLE high, then initialise Si7021 and VEML6035.

Why 0x30: free on this bus (0x29 VEML6035, 0x2A NAU7802, 0x40 Si7021), outside the reserved ranges
0x00–0x07 and 0x78–0x7F, and not adjacent to 0x29/0x2A, so a bus scan shows at a glance whether the
move worked (0x29 alone = not moved yet). Resulting bus:
**0x29 VEML6035, 0x2A NAU7802, 0x30 VL53L1X, 0x40 Si7021.**

Open: whether the bus still has pull-ups with SENSOR_ENABLE low (UG581 doesn't show where they are;
most Qwiic breakouts carry their own), the exact breakouts and load cell, and the IMU chip marking.

## Power

From UG581 2.1 and 3.2.

| Option | Notes | Status |
|---|---|---|
| USB Type-C (debugger connector) | 5 V VBUS, on-board LDO to 3.3 V VMCU; power + debug + VCOM | user-guide |
| Mini Simplicity connector / breakout pads | 3.3 V injected on VMCU (1.9–3.6 V); remove USB first. Connector not mounted | user-guide |

No battery holder on the board.

## Exposed in TwinDock

Decided by the developer on 2026-10-07, extended on 2026-10-10. Nothing else may appear in the UI or firmware.

| TwinDock name | Hardware | Driven by | Status |
|---|---|---|---|
| BTN0 | `btn0` | physical press → selected forklift drives to next waypoint | confirmed |
| BTN1 | `btn1` | physical press → select next forklift | confirmed |
| LED0 | `led0` **green** channel (HP GPIO 51) | rule: on while a truck is docked at Bay 1 | confirmed |
| LED1 | `led0` **blue** channel (HP GPIO 15) | manual from the twin | confirmed |
| `temperature` (°C) | Si7021 | `twin/gateway/sensor/temperature` every 10 s | confirmed |
| `humidity` (%RH) | Si7021 | `twin/gateway/sensor/humidity` every 10 s | confirmed |
| `light` (lux) | VEML6035 | `twin/gateway/sensor/light` | approved, gated |
| `motion`, `impact` | ICM-40627 | `twin/gateway/sensor/motion`, `/impact` | approved, gated |
| `fork_distance` (mm) | VL53L1X (Qwiic) | `twin/gateway/sensor/fork_distance` | approved, gated |
| `fork_load` (g, demo scale) | NAU7802 + load cell (Qwiic) | `twin/gateway/sensor/fork_load` | approved, gated |

**Gated** = approved on 2026-10-10, but it appears in the UI and in `hello.sensors` only once its part
has `status: "verified"` in `hardware/wiring.json` (firmware has read real values from it).

The red channel and the microphones are **not** exposed.

LED0 and LED1 are two colours of the **same** physical LED: green only, blue only, both on = cyan.
The board twin renders one LED at the RGB LED position whose colour is the mix of LED0/LED1.

`hello` payload the firmware must send (sensors list grows as gated sensors are verified):
`{"board":"BRD2605A","radio_board":"","fw_version":"<ver>","leds":["LED0","LED1"],"buttons":["BTN0","BTN1"],"sensors":["temperature","humidity"]}`

## Open items

1. Confirm on the board: silkscreen says BRD2605A **A02**, buttons are labelled BTN0/BTN1, IMU marking ICM-40627.
2. Simplicity Studio: install it (only the installer was found) and note the version above.
3. Sensor pack parts: VL53L1X and NAU7802 breakouts (two Qwiic connectors each?), load cell model.

## Hotspot positions (board twin)

Positions are % of the top-down photo `frontend/public/board/top.jpg` (0,0 = top-left).
Fill in after taking the photo.

| Element | x % | y % | Notes |
|---|---|---|---|
| RGB LED (led0) | | | |
| BTN0 | | | |
| BTN1 | | | |
