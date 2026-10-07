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

All sit on the ULP I2C bus (I2C2) behind a **sensor power enable** pin:
`SENSOR_ENABLE_GPIO_PIN = RTE_UULP_GPIO_1_PIN` (UULP GPIO 1, `RTE_Device_917.h` line ~5563). The dev kit
demo drives it high before talking to any sensor (`siwx917_dev_kit/sensors/light_sensor.c`).

| Sensor | Part | Bus / address | SDK driver | Status |
|---|---|---|---|---|
| Relative humidity + temperature | Si7021 | ULP_I2C / 0x40 | `si70xx_sensor` (`SI7021_ADDR 0x40`) | sdk-verified |
| Ambient light | VEML6035 | ULP_I2C / 0x29 | `veml6035` (`VEML6035_SLAVE_ADDR 0x29`) | sdk-verified |
| 6-axis IMU | ICM-40627 | SPI (ULP SSI primary) | `sl_icm40627` (board override for ULP SSI) | sdk-verified |
| MEMS microphones | ICS-43434 (x2, per product page) | I2S0 | `sl_si91x_mic` (board override) | sdk-verified driver, count unverified |

## Power

| Option | Notes | Status |
|---|---|---|
| USB (debugger connector) | Power + debug + VCOM | unverified (developer: confirm connector) |
| Other (battery / coin cell) | User guide not readable from here (403) | unverified |

## Exposed in TwinDock

Decided by the developer on 2026-10-07. Nothing else may appear in the UI or firmware.

| TwinDock name | Hardware | Driven by | Status |
|---|---|---|---|
| BTN0 | `btn0` | physical press → selected forklift drives to next waypoint | confirmed |
| BTN1 | `btn1` | physical press → select next forklift | confirmed |
| LED0 | `led0` **green** channel (HP GPIO 51) | rule: on while a truck is docked at Bay 1 | confirmed |
| LED1 | `led0` **blue** channel (HP GPIO 15) | manual from the twin | confirmed |
| `temperature` (°C) | Si7021 | `twin/gateway/sensor/temperature` every 10 s | confirmed |
| `humidity` (%RH) | Si7021 | `twin/gateway/sensor/humidity` every 10 s | confirmed |

The red channel, VEML6035, ICM-40627 and the microphones are **not** exposed.

LED0 and LED1 are two colours of the **same** physical LED: green only, blue only, both on = cyan.
The board twin renders one LED at the RGB LED position whose colour is the mix of LED0/LED1.

`hello` payload the firmware must send:
`{"board":"BRD2605A","radio_board":"","fw_version":"<ver>","leds":["LED0","LED1"],"buttons":["BTN0","BTN1"],"sensors":["temperature","humidity"]}`

## Open items

1. Confirm on the board: silkscreen says BRD2605A **A02**, buttons are labelled BTN0/BTN1.
2. Simplicity Studio: install it (only the installer was found) and note the version above.
3. Power options: confirm from the user guide.

## Hotspot positions (board twin)

Positions are % of the top-down photo `frontend/public/board/top.jpg` (0,0 = top-left).
Fill in after taking the photo.

| Element | x % | y % | Notes |
|---|---|---|---|
| RGB LED (led0) | | | |
| BTN0 | | | |
| BTN1 | | | |
