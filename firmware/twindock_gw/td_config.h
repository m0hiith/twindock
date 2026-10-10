/*******************************************************************************
 * TwinDock gateway firmware: build-time configuration.
 *
 * Network secrets (SSID, passphrase, broker IP) live in td_secrets.h, which is
 * gitignored. Copy td_secrets.example.h to td_secrets.h and fill it in.
 ******************************************************************************/
#ifndef TD_CONFIG_H
#define TD_CONFIG_H

#if __has_include("td_secrets.h")
#include "td_secrets.h"
#else
#error "Copy td_secrets.example.h to td_secrets.h and set your Wi-Fi SSID, passphrase and broker IP."
#endif

/* ---- Steps ---------------------------------------------------------------
 * Step A (Wi-Fi, MQTT, retained hello) is always built. Steps B-D can be switched
 * off so they can be brought up one at a time on the board (see TESTING.md).
 * hello only lists the buttons/LEDs whose step is enabled, so the backend never
 * expects hardware the running firmware does not handle. */
#ifndef TD_ENABLE_STEP_B_STATUS
#define TD_ENABLE_STEP_B_STATUS 1
#endif
#ifndef TD_ENABLE_STEP_C_BUTTONS
#define TD_ENABLE_STEP_C_BUTTONS 1
#endif
#ifndef TD_ENABLE_STEP_D_LEDS
#define TD_ENABLE_STEP_D_LEDS 1
#endif

/* ---- Identity (HARDWARE.md, "Kit identity") ------------------------------ */
#define TD_BOARD       "BRD2605A"
#define TD_RADIO_BOARD "" // single-board kit, no radio board

// fw_version = semantic version + the steps compiled in, e.g. "0.2.0+ABCD",
// so the twin shows exactly which features the flashed build has.
#define TD_FW_SEMVER "0.2.0"
#define TD_STEP_STR_A "A"
#if TD_ENABLE_STEP_B_STATUS
#define TD_STEP_STR_B "B"
#else
#define TD_STEP_STR_B ""
#endif
#if TD_ENABLE_STEP_C_BUTTONS
#define TD_STEP_STR_C "C"
#else
#define TD_STEP_STR_C ""
#endif
#if TD_ENABLE_STEP_D_LEDS
#define TD_STEP_STR_D "D"
#else
#define TD_STEP_STR_D ""
#endif
#define TD_FW_VERSION TD_FW_SEMVER "+" TD_STEP_STR_A TD_STEP_STR_B TD_STEP_STR_C TD_STEP_STR_D

/* ---- MQTT ---------------------------------------------------------------- */
#ifndef TD_BROKER_PORT
#define TD_BROKER_PORT 1883 // plain MQTT to Mosquitto on the laptop (broker/mosquitto.conf)
#endif
#define TD_MQTT_CLIENT_ID "twindock-gw-01"

// 30 s keep-alive: the broker notices a dead board within 1.5 x 30 s. The backend
// does not rely on this; it marks the board stale after 15 s without status.
#define TD_MQTT_KEEPALIVE_S 30

// Synchronous connect/publish/subscribe timeouts. Generous because the NWP may be
// busy with a DHCP renew or scan; they only bound how long the app thread blocks.
#define TD_MQTT_CONNECT_TIMEOUT_MS   10000
#define TD_MQTT_PUBLISH_TIMEOUT_MS   3000
#define TD_MQTT_SUBSCRIBE_TIMEOUT_MS 3000

// Boot-time retry interval for Wi-Fi join and the first MQTT connect. Reconnecting
// after a drop (with backoff, buffering and "reconnects") is Step F, not written yet.
#define TD_BOOT_RETRY_MS 5000

/* ---- Step B -------------------------------------------------------------- */
#define TD_STATUS_PERIOD_MS 5000 // contract: twin/gateway/status every 5 s

/* ---- Step C -------------------------------------------------------------- */
// A button state is reported only after its pin has been quiet for this long.
// Tactile switches bounce for roughly 1-10 ms; 30 ms covers worn switches with
// margin, and is still far below the ~100 ms where a person notices lag.
#define TD_BUTTON_DEBOUNCE_MS 30

/* ---- Step D -------------------------------------------------------------- */
#define TD_CMD_ID_MAX_LEN   36  // contract: cmd_id is at most 36 chars (a UUID)
#define TD_CMD_PAYLOAD_MAX  160 // longest valid cmd/led payload is ~80 bytes

#endif // TD_CONFIG_H
