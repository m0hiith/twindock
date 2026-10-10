# Firmware testing: Prompt 2, Steps A–D

Status: **written, builds with 0 errors and 0 warnings, not yet run on hardware.** Everything below
is what the code is written to print and publish. Where the real board shows something different,
the board is right: note it and fix the firmware or HARDWARE.md.

Project: [`twindock_gw/`](twindock_gw/), generated with `slc` from the WiSeConnect example
`wifi_embedded_mqtt_client_soc` for `brd2605a`.

## SDK note (read first)

The build uses **Simplicity SDK 2026.6.1 + WiSeConnect 4.1.1**, the pair installed by the Simplicity
Installer on this Mac (`~/.silabs/slt/installs/conan/p/...`). The `wiseconnect-3.5.3` folder in the repo
(which HARDWARE.md cites) needs Simplicity SDK 2025.6.2. That SDK isn't installed, so 3.5.3 can't build here.
The BRD2605A button and RGB LED pin configs are byte-identical in 3.5.3 and 4.1.1, so the pins in
HARDWARE.md still hold. Every SDK function the firmware calls was looked up in the 4.1.1 headers;
each file lists the ones it uses at the top.

## One-time setup

1. **Secrets.** `cp twindock_gw/td_secrets.example.h twindock_gw/td_secrets.h`, then set
   `TD_WIFI_SSID` (2.4 GHz, WPA2), `TD_WIFI_PASSPHRASE` and `TD_BROKER_IP` (the IP that
   `./scripts/run_broker.sh` prints). `td_secrets.h` is gitignored.
2. **Stop the fake board.** Quit `tools/fake_board.py`. It publishes on the same topics. Clear
   its retained hello: `mosquitto_pub -r -n -t twin/gateway/hello`.
3. **Network processor (NWP) firmware.** The NWP firmware must match WiSeConnect 4.1.1, which ships
   `SiWG917-B.2.16.5.1.0.8.rps`. In Simplicity Studio, the Launcher offers the update when the board
   is connected. From the command line (not tried yet, no board):
   ```sh
   COMMANDER=~/.silabs/slt/installs/archive/Commander.app/Contents/MacOS/commander
   $COMMANDER rps load ~/.silabs/slt/installs/conan/p/wiseca1ca655dfba28/p/connectivity_firmware/standard/SiWG917-B.2.16.5.1.0.8.rps --device SiWG917M111MGTBA
   ```
   A mismatch typically shows up as `[td] wifi: init failed 0x...` repeating at boot.
4. **Broker running:** `./scripts/run_broker.sh`, and in a second terminal:
   ```sh
   mosquitto_sub -h localhost -v -t 'twin/#'
   ```

## Build, flash, console

- **Steps on/off:** `twindock_gw/td_config.h`, `TD_ENABLE_STEP_B_STATUS`, `TD_ENABLE_STEP_C_BUTTONS`,
  `TD_ENABLE_STEP_D_LEDS` (1 = on). Step A is always on. All 8 combinations build with 0 warnings.
  The build's `fw_version` shows which steps are in it: `0.2.0+A`, `0.2.0+AB`, … `0.2.0+ABCD`.
- **Build (CLI):** `cd firmware/twindock_gw && make -j8 -f twindock_gw.Makefile`
  → `build/debug/twindock_gw.rps`.
  **Build (Studio):** File → Import → this folder (`twindock_gw.slcp`) → Build.
  After editing `twindock_gw.slcp`, regenerate first (Studio does this automatically).
- **Flash:** Studio "Flash to Device", or
  `$COMMANDER rps load build/debug/twindock_gw.rps --device SiWG917M111MGTBA`.
- **Serial console:** the J-Link VCOM at **115200 8N1**, e.g. `screen /dev/cu.usbmodem* 115200`
  (quit: Ctrl-A then K). Press RESET after connecting to see the boot lines.

Lines starting `[td]` come from TwinDock. The SDK may print its own lines in between; ignore them unless
something fails. `<...>` marks values that differ per run.

---

## Step A: Wi-Fi, MQTT, retained hello

Set B, C and D to 0. Build, flash, reset.

**Serial console**
```
[td] TwinDock gateway 0.2.0+A on BRD2605A
[td] wifi: joining "<your SSID>"
[td] wifi: connected
[td] mqtt: connecting to <broker IP>:1883 as twindock-gw-01
[td] mqtt: connected
[td] pub twin/gateway/hello {"board":"BRD2605A","radio_board":"","fw_version":"0.2.0+A","leds":[],"buttons":[],"sensors":[]}
```
Then nothing more (Step A sends hello only).

**mosquitto_sub**
```
twin/gateway/hello {"board":"BRD2605A","radio_board":"","fw_version":"0.2.0+A","leds":[],"buttons":[],"sensors":[]}
```

**Checks**
- Retained: stop `mosquitto_sub`, start it again. The hello line appears immediately, without a
  board reset.
- `leds` and `buttons` are empty because Steps C and D are off. hello only lists hardware the
  running build handles. `sensors` stays `[]` until a sensor step exists and its part is verified
  (HARDWARE.md, "Gated").

**If it fails**
- `[td] wifi: join failed 0x..., retrying in 5 s`: wrong SSID or passphrase, a 5 GHz-only network,
  or a WPA3-only network (the default profile uses WPA2). It retries every 5 s.
- `[td] mqtt: connect failed 0x..., retrying in 5 s`: wrong `TD_BROKER_IP`, broker not running,
  or the Mac firewall is blocking port 1883. Test from another machine:
  `mosquitto_pub -h <broker IP> -t test -m hi`.

---

## Step B: status every 5 s

Set B = 1 (C and D = 0).

**Serial console**: the Step A lines with `0.2.0+AB`, then right after hello:
```
[td] pub twin/gateway/status {"ts_ms":<ms>,"uptime_s":<s>,"wifi_rssi_dbm":<-30..-90>,"wifi_connected":true,"ip":"<board IP>","fw_version":"0.2.0+AB","msgs_sent":1,"reconnects":0}
```
then one status line every 5 s.

**mosquitto_sub**: the same JSON on `twin/gateway/status`, every 5 s.

**Checks**
- `ts_ms` grows by ~5000 per message; `uptime_s` = `ts_ms` / 1000, rounded down. Both are board time since boot.
- `msgs_sent` goes up by 1 per message: it counts accepted publishes *before* this one, so the first
  status says 1 (the hello).
- `wifi_rssi_dbm` moves when you carry the board away from the AP. It's an average over the last 4 beacons,
  so it lags by a second or two.
- `ip` matches the board's DHCP lease in your router.
- `reconnects` is a real counter that stays 0: nothing reconnects until Step F.
- Fields left out on purpose: `buffered` and `replay` (Step F). If RSSI or IP can't be read (link
  down), those fields are left out of that message. Nothing is filled in.

**Known limit until Step F:** if Wi-Fi or the broker drops, the board prints
`[td] mqtt: disconnected (no reconnect before Step F; reset the board)` (or `[td] pub FAILED 0x...`
lines) and stops publishing. The twin shows the board offline after 15 s. Reset the board to recover.

---

## Step C: buttons

Set C = 1 (B can stay on).

**Serial console**: after hello (and the first status if B is on):
```
[td] buttons: ready (debounce 30 ms)
```
Press and release BTN0:
```
[td] pub twin/gateway/button {"ts_ms":<ms>,"button":"BTN0","state":"pressed"}
[td] pub twin/gateway/button {"ts_ms":<ms>,"button":"BTN0","state":"released"}
```
BTN1 is the same with `"button":"BTN1"`.

**mosquitto_sub**: hello now has `"buttons":["BTN0","BTN1"]`, and each press gives two lines on
`twin/gateway/button`, `pressed` then `released`.

**Checks (things only the board can confirm)**
- **Polarity.** If a press prints `released` and letting go prints `pressed`, the buttons are not
  active-low as the SDK driver suggests. Flip the comparison in `td_button_is_pressed()`
  (`td_buttons.c`) and record it in HARDWARE.md.
- **Labels.** BTN0 is UULP_VBAT GPIO 2 and BTN1 is HP GPIO 49 (HARDWARE.md). Check that the button marked BTN0
  on the silkscreen produces `"BTN0"`.
- **Debounce.** 20 quick taps should give exactly 20 `pressed` and 20 `released`, never two `pressed` in a
  row. A tap shorter than about 30 ms can be missed, by design.
- `ts_ms` of `pressed` is when the first edge arrived; it shows up in the console ~30 ms later.
- Holding a button sends one `pressed`, nothing while held, then one `released`.

---

## Step D: LED commands with confirmation

Set D = 1 (all steps on: `0.2.0+ABCD`).

**Serial console**: after hello:
```
[td] sub twin/gateway/cmd/led -> 0x0
[td] pub twin/gateway/led {"ts_ms":<ms>,"led":"LED0","on":false}
[td] pub twin/gateway/led {"ts_ms":<ms>,"led":"LED1","on":false}
```
The RGB LED is dark after boot (all three channels are switched off).

Send a command from the laptop:
```sh
mosquitto_pub -h localhost -t twin/gateway/cmd/led -m '{"led":"LED0","on":true,"cmd_id":"t1"}'
```
**Serial console**
```
[td] led: command LED0 -> on (cmd_id t1)
[td] pub twin/gateway/led {"ts_ms":<ms>,"led":"LED0","on":true,"cmd_id":"t1"}
```
**mosquitto_sub**
```
twin/gateway/cmd/led {"led":"LED0","on":true,"cmd_id":"t1"}
twin/gateway/led {"ts_ms":<ms>,"led":"LED0","on":true,"cmd_id":"t1"}
```
**On the board:** the LED lights **green**.

| Command | LED shows |
|---|---|
| `{"led":"LED0","on":true,"cmd_id":"t1"}` | green |
| `{"led":"LED1","on":true,"cmd_id":"t2"}` | green + blue = **cyan** |
| `{"led":"LED0","on":false,"cmd_id":"t3"}` | **blue** |
| `{"led":"LED1","on":false,"cmd_id":"t4"}` | off |

**Checks**
- `"on"` in the confirmation is read back from the pin after switching, not copied from the command.
- Sending the same command twice still gets a confirmation each time, with its own `cmd_id`.
- Invalid commands get **no** confirmation, so the backend's LED timeout fires, which is the honest result:
  ```sh
  mosquitto_pub -h localhost -t twin/gateway/cmd/led -m '{"led":"LED2","on":true,"cmd_id":"x"}'
  ```
  prints `[td] led: no such LED "LED2" (HARDWARE.md exposes LED0, LED1)` and
  `[td] led: command rejected, not valid against gateway_cmd_led.json: ...`.
  Missing `cmd_id`, `"on":1`, a `cmd_id` over 36 characters or an extra key are rejected the same way.
- **Colour mapping.** If LED0 lights blue (or red), the channel mapping is wrong: fix
  `td_led_channel()` in `td_leds.c` and HARDWARE.md.
- **End to end:** start the backend and frontend, open `/device`, click LED1. The UI shows pending,
  then on, only after the `twin/gateway/led` line appears.

---

## Verified without the board (2026-10-10)

- `make` with the project's own flags (`-Wall -Werror`): 0 errors, 0 warnings, for all 8 on/off
  combinations of Steps B, C and D.
- Extra pass with `-Wextra -Wshadow -Wformat=2 -Wundef`: no warnings from TwinDock files (the SDK's
  own headers do warn under those flags, so they aren't the project default).
- The LED command parser and the command → GPIO → confirmation path were compiled for the Mac against
  stub SDK headers: 15 valid and invalid payloads behaved as expected.
- Every payload the firmware can produce (hello, status with and without Wi-Fi, button, LED with and
  without `cmd_id`) passes its JSON schema in `shared/schemas/mqtt/`.

Not verified: anything that needs the board (Wi-Fi join, MQTT, button polarity, LED colours, RSSI values).
