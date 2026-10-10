/*******************************************************************************
 * Step D: twin/gateway/cmd/led drives the real LED; twin/gateway/led confirms.
 *
 * HARDWARE.md: the board has one RGB LED (instance led0).
 *   LED0 = its green channel, LED1 = its blue channel. Red is not exposed and is
 *   only switched off at boot so the LED shows nothing we do not report.
 *
 * Flow:
 * 1. td_leds_on_message() runs on the SDK event thread. It validates the payload
 *    against shared/schemas/mqtt/gateway_cmd_led.json and posts the command to the
 *    app thread. Invalid commands are logged and dropped: no confirmation is sent,
 *    so the backend's LED timeout fires (an honest failure).
 * 2. The app thread drives the GPIO, then reads the pin's output state back from
 *    the driver and publishes that, with the command's cmd_id. The confirmation
 *    reports what the pin is doing, not what was asked for.
 * 3. After every MQTT connect, both LEDs' real state is published once (no cmd_id)
 *    so the twin starts from the truth after a board reboot.
 *
 * SDK calls used (confirmed in WiSeConnect 4.1.1 headers):
 *   sl_si91x_rgb_led_on / _off / _get_current_state
 *       (device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/inc/sl_si91x_rgb_led.h)
 *   led_red / led_green / led_blue   (generated sl_si91x_rgb_led_instances.h; pins
 *       HP 50 / 51 / 15 from config/sl_si91x_rgb_led_init_config.h, as in HARDWARE.md)
 ******************************************************************************/
#include "td_app.h"

#if TD_ENABLE_STEP_D_LEDS

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "sl_si91x_rgb_led.h"
#include "sl_si91x_rgb_led_instances.h"

#define TD_LED_COUNT 2

static const char *const td_led_names[TD_LED_COUNT] = { "LED0", "LED1" };

static const sl_led_t *td_led_channel(uint8_t index)
{
  return (index == 0) ? &led_green : &led_blue;
}

static bool td_led_is_on(uint8_t index)
{
  // The channel is active-low (the driver's _on() clears the pin), and
  // _get_current_state() returns the pin's output level: 0 means lit.
  return sl_si91x_rgb_led_get_current_state(td_led_channel(index)) == 0;
}

/* ---- Minimal strict parser for {"led":"LEDn","on":bool,"cmd_id":"..."} ----
 * Accepts exactly the schema: these three keys, any order, nothing else, no
 * escapes in strings (cmd_id is a UUID from the backend). Rejecting escapes and
 * control characters also makes cmd_id safe to echo into our JSON unchanged. */

static const char *td_skip_ws(const char *p)
{
  while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') {
    p++;
  }
  return p;
}

// Reads a JSON string at *p into out (NUL-terminated). Returns its length, or -1.
static int td_read_string(const char **p, char *out, size_t cap)
{
  const char *s = *p;
  if (*s != '"') {
    return -1;
  }
  s++;
  size_t n = 0;
  while (*s != '"') {
    if (*s == '\0' || *s == '\\' || (unsigned char)*s < 0x20 || n + 1 >= cap) {
      return -1;
    }
    out[n++] = *s++;
  }
  out[n] = '\0';
  *p     = s + 1;
  return (int)n;
}

static bool td_parse_led_cmd(const char *json, uint8_t *led, bool *on, char *cmd_id)
{
  bool have_led = false, have_on = false, have_id = false;
  char key[8];
  char val[TD_CMD_ID_MAX_LEN + 1];
  const char *p = td_skip_ws(json);

  if (*p++ != '{') {
    return false;
  }
  for (;;) {
    p = td_skip_ws(p);
    if (td_read_string(&p, key, sizeof(key)) < 0) {
      return false;
    }
    p = td_skip_ws(p);
    if (*p++ != ':') {
      return false;
    }
    p = td_skip_ws(p);

    if (strcmp(key, "led") == 0) {
      if (td_read_string(&p, val, sizeof(val)) < 0) {
        return false;
      }
      have_led = false;
      for (uint8_t i = 0; i < TD_LED_COUNT; i++) {
        if (strcmp(val, td_led_names[i]) == 0) {
          *led     = i;
          have_led = true;
        }
      }
      if (!have_led) {
        printf("[td] led: no such LED \"%s\" (HARDWARE.md exposes LED0, LED1)\r\n", val);
        return false;
      }
    } else if (strcmp(key, "on") == 0) {
      if (strncmp(p, "true", 4) == 0) {
        *on = true;
        p += 4;
      } else if (strncmp(p, "false", 5) == 0) {
        *on = false;
        p += 5;
      } else {
        return false;
      }
      have_on = true;
    } else if (strcmp(key, "cmd_id") == 0) {
      int n = td_read_string(&p, val, sizeof(val));
      if (n < 1 || n > TD_CMD_ID_MAX_LEN) {
        return false;
      }
      memcpy(cmd_id, val, (size_t)n + 1);
      have_id = true;
    } else {
      return false; // schema: additionalProperties false
    }

    p = td_skip_ws(p);
    if (*p == ',') {
      p++;
      continue;
    }
    if (*p != '}') {
      return false;
    }
    p = td_skip_ws(p + 1);
    return *p == '\0' && have_led && have_on && have_id;
  }
}

/* SDK event thread. Validates, then hands the command to the app thread. */
static void td_leds_on_message(void *client, sl_mqtt_client_message_t *message, void *context)
{
  (void)client;
  (void)context;
  char payload[TD_CMD_PAYLOAD_MAX + 1];

  if (message->content == NULL || message->content_length == 0 || message->content_length > TD_CMD_PAYLOAD_MAX) {
    printf("[td] led: command rejected (empty or longer than %d bytes)\r\n", TD_CMD_PAYLOAD_MAX);
    return;
  }
  memcpy(payload, message->content, message->content_length);
  payload[message->content_length] = '\0';

  td_event_t ev = { .type = TD_EV_LED_CMD };
  if (!td_parse_led_cmd(payload, &ev.u.led_cmd.index, &ev.u.led_cmd.on, ev.u.led_cmd.cmd_id)) {
    printf("[td] led: command rejected, not valid against gateway_cmd_led.json: %s\r\n", payload);
    return;
  }
  printf("[td] led: command %s -> %s (cmd_id %s)\r\n",
         td_led_names[ev.u.led_cmd.index],
         ev.u.led_cmd.on ? "on" : "off",
         ev.u.led_cmd.cmd_id);
  (void)td_post_event(&ev);
}

static void td_leds_publish_state(uint8_t index, const char *cmd_id)
{
  char buf[128];
  int n;
  if (cmd_id != NULL) {
    n = snprintf(buf,
                 sizeof(buf),
                 "{\"ts_ms\":%" PRIu32 ",\"led\":\"%s\",\"on\":%s,\"cmd_id\":\"%s\"}",
                 td_now_ms(),
                 td_led_names[index],
                 td_led_is_on(index) ? "true" : "false",
                 cmd_id);
  } else {
    n = snprintf(buf,
                 sizeof(buf),
                 "{\"ts_ms\":%" PRIu32 ",\"led\":\"%s\",\"on\":%s}",
                 td_now_ms(),
                 td_led_names[index],
                 td_led_is_on(index) ? "true" : "false");
  }
  if (n < 0 || (size_t)n >= sizeof(buf)) {
    return;
  }
  // QoS 1: the UI shows a pending LED until this confirmation arrives.
  (void)td_net_publish(TD_TOPIC_LED, buf, 1, false);
}

void td_leds_init(void)
{
  // The driver configures the pins as outputs at system init; force all three
  // channels off so the LED starts dark and in a known state.
  sl_si91x_rgb_led_off(&led_red);
  sl_si91x_rgb_led_off(&led_green);
  sl_si91x_rgb_led_off(&led_blue);
}

void td_leds_on_connected(void)
{
  // QoS 1 subscription so a command is not lost on a busy link.
  (void)td_net_subscribe(TD_TOPIC_CMD_LED, 1, td_leds_on_message);
  for (uint8_t i = 0; i < TD_LED_COUNT; i++) {
    td_leds_publish_state(i, NULL);
  }
}

void td_leds_handle_command(const td_event_t *event)
{
  uint8_t index = event->u.led_cmd.index;
  if (event->u.led_cmd.on) {
    sl_si91x_rgb_led_on(td_led_channel(index));
  } else {
    sl_si91x_rgb_led_off(td_led_channel(index));
  }
  // Always confirm, even when the LED was already in that state: the backend
  // waits for this cmd_id (same behaviour as tools/fake_board.py).
  td_leds_publish_state(index, event->u.led_cmd.cmd_id);
}

#endif // TD_ENABLE_STEP_D_LEDS
