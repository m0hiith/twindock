/*******************************************************************************
 * TwinDock gateway firmware: shared types and module interfaces.
 *
 * Threading model (why it looks like this):
 * - One app thread owns the MQTT client. Every publish happens there, so the
 *   counters need no locks and publishes never interleave.
 * - SDK callbacks (MQTT messages, events) and the button ISR never publish.
 *   They post a small fixed-size td_event_t to the app thread's queue, which
 *   copies it by value: no dynamic allocation on these hot paths.
 ******************************************************************************/
#ifndef TD_APP_H
#define TD_APP_H

#include <stdbool.h>
#include <stdint.h>
#include "sl_mqtt_client.h"
#include "sl_status.h"
#include "td_config.h"

/* ---- Topics (shared/schema.md) ------------------------------------------- */
#define TD_TOPIC_HELLO   "twin/gateway/hello"
#define TD_TOPIC_STATUS  "twin/gateway/status"
#define TD_TOPIC_BUTTON  "twin/gateway/button"
#define TD_TOPIC_LED     "twin/gateway/led"
#define TD_TOPIC_CMD_LED "twin/gateway/cmd/led"

/* ---- Events posted to the app thread ------------------------------------- */
typedef enum {
  TD_EV_MQTT_DOWN, // broker connection lost (SDK event thread)
  TD_EV_BUTTON,    // debounced button change (button thread)
  TD_EV_LED_CMD,   // valid twin/gateway/cmd/led received (SDK event thread)
} td_event_type_t;

typedef struct {
  td_event_type_t type;
  union {
    struct {
      uint8_t index; // 0 = BTN0, 1 = BTN1
      bool pressed;
      uint32_t ts_ms; // board time of the first edge of this change
    } button;
    struct {
      uint8_t index; // 0 = LED0, 1 = LED1
      bool on;
      char cmd_id[TD_CMD_ID_MAX_LEN + 1];
    } led_cmd;
  } u;
} td_event_t;

/* ---- app.c --------------------------------------------------------------- */
// Board time in ms since boot (contract: ts_ms). Based on the RTOS tick, so it
// wraps after 2^32 ms = 49.7 days of uptime.
uint32_t td_now_ms(void);
// Queue an event for the app thread. Safe from threads; never blocks.
// Returns false if the queue is full (the event is dropped and logged).
bool td_post_event(const td_event_t *event);

/* ---- td_net.c (Step A) --------------------------------------------------- */
// Join Wi-Fi with the credentials from td_secrets.h; retries until it succeeds.
void td_net_wifi_up(void);
// Connect to the broker; retries until it succeeds.
void td_net_mqtt_connect(void);
bool td_net_mqtt_connected(void);
void td_net_mqtt_mark_down(void);
// Publish from the app thread only. Counts successful publishes in msgs_sent.
sl_status_t td_net_publish(const char *topic, const char *payload, uint8_t qos, bool retained);
// Subscribe from the app thread only; handler runs on the SDK event thread.
sl_status_t td_net_subscribe(const char *topic, uint8_t qos, sl_mqtt_client_message_received_t handler);
// Retained twin/gateway/hello.
sl_status_t td_net_publish_hello(void);
uint32_t td_net_msgs_sent(void);
uint32_t td_net_reconnects(void);

/* ---- td_status.c (Step B) ------------------------------------------------ */
void td_status_publish(void);

/* ---- td_buttons.c (Step C) ----------------------------------------------- */
void td_buttons_start(void);
void td_buttons_publish(const td_event_t *event);

/* ---- td_leds.c (Step D) -------------------------------------------------- */
void td_leds_init(void);
// After every (re)connect: subscribe to cmd/led and report both LEDs' real state.
void td_leds_on_connected(void);
void td_leds_handle_command(const td_event_t *event);

#endif // TD_APP_H
