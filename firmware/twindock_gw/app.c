/*******************************************************************************
 * TwinDock gateway firmware: app thread.
 *
 * Based on the WiSeConnect "embedded MQTT client" example (Zlib licence,
 * Copyright 2022 Silicon Laboratories Inc.), rewritten for TwinDock: the example's
 * demo topics are replaced by the contract in shared/schema.md.
 *
 * Steps (Prompt 2 in PROMPTS.md), each in its own file and switch in td_config.h:
 *   A  td_net.c      Wi-Fi + MQTT, retained twin/gateway/hello       (always on)
 *   B  td_status.c   twin/gateway/status every 5 s                   TD_ENABLE_STEP_B_STATUS
 *   C  td_buttons.c  twin/gateway/button, debounced                  TD_ENABLE_STEP_C_BUTTONS
 *   D  td_leds.c     twin/gateway/cmd/led -> LED -> twin/gateway/led  TD_ENABLE_STEP_D_LEDS
 ******************************************************************************/
#include <inttypes.h>
#include <stdio.h>

#include "cmsis_os2.h"
#include "sl_utility.h"

#include "app.h"
#include "td_app.h"

// 16 events: a burst of button edges plus a few LED commands while a publish is
// in flight. Each slot is sizeof(td_event_t) (~48 bytes), allocated once at boot.
#define TD_EVENT_QUEUE_LEN 16

static osMessageQueueId_t td_queue;

static const osThreadAttr_t td_app_thread_attr = {
  .name       = "td_app",
  .stack_size = 3072, // as in the SDK example; JSON buffers are small or static
  .priority   = osPriorityLow,
};

uint32_t td_now_ms(void)
{
  // 64-bit intermediate so the conversion is exact for any tick rate.
  return (uint32_t)(((uint64_t)osKernelGetTickCount() * 1000U) / osKernelGetTickFreq());
}

bool td_post_event(const td_event_t *event)
{
  // Timeout 0: never block the SDK event thread or the button thread.
  if (td_queue == NULL || osMessageQueuePut(td_queue, event, 0, 0) != osOK) {
    printf("[td] event queue full, dropped event type %d\r\n", (int)event->type);
    return false;
  }
  return true;
}

/* Everything that must happen after each successful MQTT connect. */
static void td_on_mqtt_connected(void)
{
  (void)td_net_publish_hello();
#if TD_ENABLE_STEP_D_LEDS
  td_leds_on_connected();
#endif
#if TD_ENABLE_STEP_B_STATUS
  td_status_publish(); // first status right away instead of 5 s later
#endif
}

static void td_app_thread(void *argument)
{
  UNUSED_PARAMETER(argument);
  printf("\r\n[td] TwinDock gateway %s on %s\r\n", TD_FW_VERSION, TD_BOARD);

#if TD_ENABLE_STEP_D_LEDS
  td_leds_init();
#endif

  td_net_wifi_up();
  td_net_mqtt_connect();
  td_on_mqtt_connected();

#if TD_ENABLE_STEP_C_BUTTONS
  td_buttons_start();
#endif

#if TD_ENABLE_STEP_B_STATUS
  uint32_t next_status_ms = td_now_ms() + TD_STATUS_PERIOD_MS;
#endif

  for (;;) {
    // Sleep until an event arrives or the next status is due. Without Step B,
    // the thread simply waits for events.
    uint32_t timeout = osWaitForever;
#if TD_ENABLE_STEP_B_STATUS
    uint32_t now = td_now_ms();
    timeout      = ((int32_t)(next_status_ms - now) > 0) ? (next_status_ms - now) : 0U;
#endif

    td_event_t ev;
    if (osMessageQueueGet(td_queue, &ev, NULL, timeout) == osOK) {
      switch (ev.type) {
        case TD_EV_MQTT_DOWN:
          // Reconnecting with backoff and buffering is Step F. Until then the board
          // logs it, stops publishing, and the twin shows it stale after 15 s.
          td_net_mqtt_mark_down();
          printf("[td] mqtt: disconnected (no reconnect before Step F; reset the board)\r\n");
          break;
        case TD_EV_BUTTON:
#if TD_ENABLE_STEP_C_BUTTONS
          td_buttons_publish(&ev);
#endif
          break;
        case TD_EV_LED_CMD:
#if TD_ENABLE_STEP_D_LEDS
          td_leds_handle_command(&ev);
#endif
          break;
      }
    }

#if TD_ENABLE_STEP_B_STATUS
    if ((int32_t)(td_now_ms() - next_status_ms) >= 0) {
      if (td_net_mqtt_connected()) {
        td_status_publish();
      }
      // Fixed schedule (no drift from publish time); if we fell a whole period
      // behind, restart the schedule instead of sending a burst.
      next_status_ms += TD_STATUS_PERIOD_MS;
      if ((int32_t)(td_now_ms() - next_status_ms) >= 0) {
        next_status_ms = td_now_ms() + TD_STATUS_PERIOD_MS;
      }
    }
#endif
  }
}

void app_init(void)
{
  td_queue = osMessageQueueNew(TD_EVENT_QUEUE_LEN, sizeof(td_event_t), NULL);
  osThreadNew(td_app_thread, NULL, &td_app_thread_attr);
}
