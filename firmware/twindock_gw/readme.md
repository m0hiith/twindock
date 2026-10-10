# TwinDock gateway firmware (SiWx917, BRD2605A)

Simplicity Studio / slc project, generated from the WiSeConnect 4.1.1 "embedded MQTT client"
example (`wifi_embedded_mqtt_client_soc`) for BRD2605A, on Simplicity SDK 2026.6.1.

How to build, flash and test each step: [../TESTING.md](../TESTING.md).

| File | Step | What it does |
|---|---|---|
| `td_config.h` | all | Settings, step switches, timing constants (with reasons) |
| `td_secrets.example.h` | A | Copy to `td_secrets.h` (gitignored): SSID, passphrase, broker IP |
| `app.c` | all | App thread, event queue, 5 s status schedule |
| `td_net.c` | A | Wi-Fi join, MQTT connect, retained `twin/gateway/hello`, publish helper |
| `td_status.c` | B | `twin/gateway/status` from SDK values |
| `td_buttons.c` | C | BTN0/BTN1 debounced on `twin/gateway/button` |
| `td_leds.c` | D | `twin/gateway/cmd/led` → RGB LED → `twin/gateway/led` confirmation |

The message contract is in `/shared/schema.md` and `/shared/schemas/mqtt/`.
