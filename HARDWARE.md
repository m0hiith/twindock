# HARDWARE.md: verified inventory of the physical board

> **Status: DRAFT, NOTHING VERIFIED YET.**
> Every row below is marked `unverified` until it has been confirmed against the WiSeConnect SDK
> board config for BRD2605A **and** by the developer. The UI and firmware may only expose rows
> marked `verified`.

## Kit identity

| Field | Value | Status |
|---|---|---|
| Kit | SiWx917-DK2605A (Wi-Fi 6 + Bluetooth LE SoC Dev Kit) | confirmed by developer |
| Board | BRD2605A (revision: _fill in from label, e.g. A02_) | unverified |
| SoC | SiWx917 (exact OPN: _fill in from chip marking_) | unverified |
| Debugger | Onboard SEGGER J-Link over USB Type-C | unverified |
| SDK | WiSeConnect _version_ in Simplicity Studio _version_ | **not installed yet** |
| SDK path | _fill in after install_ | **not installed yet** |

## User LEDs

Source so far: product page / user guide summary only ("one RGB LED"). How the SDK exposes it
(one `sl_si91x_led` instance per colour? which colours?) must be checked in the board config.

| UI name | SDK instance | Pin | Colour | Status |
|---|---|---|---|---|
| LED0 | _?_ | _?_ | _?_ | unverified |
| LED1 | _?_ | _?_ | _?_ | unverified |

## User buttons

Source so far: user guide summary ("two push buttons" plus a reset button that is not a user button).

| UI name | SDK instance | Pin | Active level | Status |
|---|---|---|---|---|
| BTN0 | _?_ | _?_ | _?_ | unverified |
| BTN1 | _?_ | _?_ | _?_ | unverified |

## Onboard sensors

Source so far: user guide summary. None may be shown in the UI until verified and a firmware driver exists.

| Sensor | Part | Bus / address | Enable pin | MQTT name | Status |
|---|---|---|---|---|---|
| Relative humidity + temperature | Si7021 | I2C / _?_ | _?_ | `temperature`, `humidity` | unverified |
| 6-axis IMU | ICM-40627 | SPI or I2C / _?_ | _?_ | _not planned_ | unverified |
| Ambient light | _part?_ | I2C / _?_ | _?_ | `light` | unverified |
| MEMS microphones (x2) | ICS-43434 | I2S | _?_ | _not planned_ | unverified |

## Power

| Option | Notes | Status |
|---|---|---|
| USB Type-C | Power + J-Link debug + VCOM | unverified |
| Battery / other | _check user guide_ | unverified |

## Questions for the developer

1. Board label revision (e.g. BRD2605A **A02**) and SoC OPN.
2. WiSeConnect and Simplicity Studio versions, and the SDK path once installed.
3. Is the RGB LED one LED (three channels) or does the SDK expose it as separate LED instances?
   Which colours do you want as LED0 / LED1?
4. Which sensors do you actually want in the twin (Si7021 temperature/humidity is the easy one)?

## Hotspot positions (board twin)

Positions are % of the top-down photo `frontend/public/board/top.jpg` (0,0 = top-left).
Fill in after taking the photo.

| Element | x % | y % | Notes |
|---|---|---|---|
| LED0 | | | |
| LED1 | | | |
| BTN0 | | | |
| BTN1 | | | |
