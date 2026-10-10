/*******************************************************************************
 * Step C: BTN0/BTN1 on twin/gateway/button, debounced.
 *
 * How the debounce works:
 * 1. The button driver calls sl_si91x_button_isr() on every edge (the BRD2605A
 *    config enables rise and fall interrupts for btn0 and btn1). In interrupt
 *    context we only set a thread flag for that button; no reads, no logging.
 * 2. The button thread wakes on the first edge, notes the time, then waits until
 *    the pins have been quiet for TD_BUTTON_DEBOUNCE_MS (every new edge restarts
 *    the wait).
 * 3. It then reads the real pin levels and reports each button whose settled
 *    state differs from the last reported one. A bounce or a glitch shorter than
 *    the window ends where it started and produces no message.
 *
 * Active level: the SDK button driver starts each button's soft state at 1
 * (released) and reports BUTTON_PRESSED when the pin reads differently, so the
 * buttons are active-low (pin 0 = pressed). Confirm on the board (TESTING.md, C).
 *
 * SDK calls used (confirmed in WiSeConnect 4.1.1 headers):
 *   sl_si91x_button_isr (weak, overridden), sl_si91x_button_state
 *       (device/silabs/si91x/mcu/drivers/hardware_drivers/button/inc/sl_si91x_button.h)
 *   button_btn0 / button_btn1   (generated sl_si91x_button_instances.h)
 *   osThreadNew, osThreadFlagsSet (ISR-safe), osThreadFlagsWait   (cmsis_os2.h)
 ******************************************************************************/
#include "td_app.h"

#if TD_ENABLE_STEP_C_BUTTONS

#include <inttypes.h>
#include <stdio.h>

#include "cmsis_os2.h"
#include "sl_si91x_button.h"
#include "sl_si91x_button_instances.h"

#define TD_BUTTON_COUNT 2
#define TD_BUTTON_FLAGS ((1U << TD_BUTTON_COUNT) - 1U)

static const sl_button_t *const td_buttons[TD_BUTTON_COUNT] = { &button_btn0, &button_btn1 };
static const char *const td_button_names[TD_BUTTON_COUNT]   = { "BTN0", "BTN1" };

static osThreadId_t td_button_thread_id; // NULL until the thread exists
static bool td_reported_pressed[TD_BUTTON_COUNT];

static bool td_button_is_pressed(uint8_t index)
{
  // Raw pin level from the driver (HP/ULP or UULP GPIO); active-low.
  return sl_si91x_button_state(td_buttons[index]->pin, td_buttons[index]->port) == 0;
}

/* Overrides the driver's weak callback. Runs in interrupt context. */
void sl_si91x_button_isr(uint8_t pin, int8_t state)
{
  (void)state; // the level is read later, after the pin has settled
  if (td_button_thread_id == NULL) {
    return; // edge before the thread started; the thread reads the level at start
  }
  for (uint8_t i = 0; i < TD_BUTTON_COUNT; i++) {
    if (td_buttons[i]->pin == pin) {
      (void)osThreadFlagsSet(td_button_thread_id, 1U << i);
    }
  }
}

static void td_button_thread(void *arg)
{
  (void)arg;
  for (;;) {
    // Sleep until the first edge on any button.
    (void)osThreadFlagsWait(TD_BUTTON_FLAGS, osFlagsWaitAny, osWaitForever);
    uint32_t first_edge_ms = td_now_ms();

    // Wait for a quiet period: osThreadFlagsWait returns a flag value while edges
    // keep arriving, and osFlagsErrorTimeout once none came for the whole window.
    while ((osThreadFlagsWait(TD_BUTTON_FLAGS, osFlagsWaitAny, TD_BUTTON_DEBOUNCE_MS) & osFlagsError) == 0U) {
    }

    for (uint8_t i = 0; i < TD_BUTTON_COUNT; i++) {
      bool pressed = td_button_is_pressed(i);
      if (pressed != td_reported_pressed[i]) {
        td_reported_pressed[i] = pressed;
        td_event_t ev          = { .type = TD_EV_BUTTON };
        ev.u.button.index      = i;
        ev.u.button.pressed    = pressed;
        ev.u.button.ts_ms      = first_edge_ms;
        (void)td_post_event(&ev);
      }
    }
  }
}

void td_buttons_start(void)
{
  // Baseline: whatever the buttons are doing at start is not reported as a change.
  for (uint8_t i = 0; i < TD_BUTTON_COUNT; i++) {
    td_reported_pressed[i] = td_button_is_pressed(i);
  }
  // Small stack: the thread only reads two pins and posts a 48-byte event.
  // Priority above the app thread so debounce timing is not delayed by publishing.
  static const osThreadAttr_t attr = {
    .name       = "td_buttons",
    .stack_size = 1024,
    .priority   = osPriorityBelowNormal,
  };
  td_button_thread_id = osThreadNew(td_button_thread, NULL, &attr);
  printf("[td] buttons: %s (debounce %d ms)\r\n", td_button_thread_id != NULL ? "ready" : "thread FAILED", TD_BUTTON_DEBOUNCE_MS);
}

void td_buttons_publish(const td_event_t *event)
{
  char buf[96];
  int n = snprintf(buf,
                   sizeof(buf),
                   "{\"ts_ms\":%" PRIu32 ",\"button\":\"%s\",\"state\":\"%s\"}",
                   event->u.button.ts_ms,
                   td_button_names[event->u.button.index],
                   event->u.button.pressed ? "pressed" : "released");
  if (n < 0 || (size_t)n >= sizeof(buf)) {
    return;
  }
  // QoS 1: a press drives a forklift in the twin, so it should not be lost.
  (void)td_net_publish(TD_TOPIC_BUTTON, buf, 1, false);
}

#endif // TD_ENABLE_STEP_C_BUTTONS
