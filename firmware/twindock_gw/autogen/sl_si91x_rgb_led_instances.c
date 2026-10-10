/***************************************************************************/ 
/**
 * @file sl_si91x_rgb_led_instances.c.jinja
 * @brief RGB LED Instances
 *******************************************************************************
 * # License
 * <b>Copyright 2023 Silicon Laboratories Inc. www.silabs.com</b>
 *******************************************************************************
 *
 * SPDX-License-Identifier: Zlib
 *
 * The licensor of this software is Silicon Laboratories Inc.
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 *
 ******************************************************************************/

#include "sl_si91x_rgb_led.h"
#include "sl_si91x_rgb_led_config.h"

#ifdef SI917_RGB_DRIVER_OLD
sl_led_t led_red = {
  .port = SL_LED_RED_PORT,
  .pin = SL_LED_RED_PIN,
  .led_number = SL_LED_RED_NUMBER,
  .pad = SL_LED_RED_PAD,
};

sl_led_t led_green = {
  .port = SL_LED_GREEN_PORT,
  .pin = SL_LED_GREEN_PIN,
  .led_number = SL_LED_GREEN_NUMBER,
  .pad = SL_LED_GREEN_PAD,
};

sl_led_t led_blue = {
  .port = SL_LED_BLUE_PORT,
  .pin = SL_LED_BLUE_PIN,
  .led_number = SL_LED_BLUE_NUMBER,
  .pad = SL_LED_BLUE_PAD,
};
#else
  sl_led_t led_blue_red = {
    .port = SL_LED_BLUE_RED_PORT,
    .pin = SL_LED_BLUE_RED_PIN,
    .led_number = SL_LED_BLUE_RED_NUMBER,
    .pad = SL_LED_BLUE_RED_PAD,
  };

  sl_led_t led_blue_green = {
    .port = SL_LED_BLUE_GREEN_PORT,
    .pin = SL_LED_BLUE_GREEN_PIN,
    .led_number = SL_LED_BLUE_GREEN_NUMBER,
    .pad = SL_LED_BLUE_GREEN_PAD,
  };

  sl_led_t led_blue_blue = {
    .port = SL_LED_BLUE_BLUE_PORT,
    .pin = SL_LED_BLUE_BLUE_PIN,
    .led_number = SL_LED_BLUE_BLUE_NUMBER,
    .pad = SL_LED_BLUE_BLUE_PAD,
  };

  const sl_rgb_led_t led_blue = {
    .red = &led_blue_red,
    .green = &led_blue_green,
    .blue = &led_blue_blue,
  };
  sl_led_t led_green_red = {
    .port = SL_LED_GREEN_RED_PORT,
    .pin = SL_LED_GREEN_RED_PIN,
    .led_number = SL_LED_GREEN_RED_NUMBER,
    .pad = SL_LED_GREEN_RED_PAD,
  };

  sl_led_t led_green_green = {
    .port = SL_LED_GREEN_GREEN_PORT,
    .pin = SL_LED_GREEN_GREEN_PIN,
    .led_number = SL_LED_GREEN_GREEN_NUMBER,
    .pad = SL_LED_GREEN_GREEN_PAD,
  };

  sl_led_t led_green_blue = {
    .port = SL_LED_GREEN_BLUE_PORT,
    .pin = SL_LED_GREEN_BLUE_PIN,
    .led_number = SL_LED_GREEN_BLUE_NUMBER,
    .pad = SL_LED_GREEN_BLUE_PAD,
  };

  const sl_rgb_led_t led_green = {
    .red = &led_green_red,
    .green = &led_green_green,
    .blue = &led_green_blue,
  };
  sl_led_t led_red_red = {
    .port = SL_LED_RED_RED_PORT,
    .pin = SL_LED_RED_RED_PIN,
    .led_number = SL_LED_RED_RED_NUMBER,
    .pad = SL_LED_RED_RED_PAD,
  };

  sl_led_t led_red_green = {
    .port = SL_LED_RED_GREEN_PORT,
    .pin = SL_LED_RED_GREEN_PIN,
    .led_number = SL_LED_RED_GREEN_NUMBER,
    .pad = SL_LED_RED_GREEN_PAD,
  };

  sl_led_t led_red_blue = {
    .port = SL_LED_RED_BLUE_PORT,
    .pin = SL_LED_RED_BLUE_PIN,
    .led_number = SL_LED_RED_BLUE_NUMBER,
    .pad = SL_LED_RED_BLUE_PAD,
  };

  const sl_rgb_led_t led_red = {
    .red = &led_red_red,
    .green = &led_red_green,
    .blue = &led_red_blue,
  };
#endif

void rgb_led_init_instances(void)
{
#ifdef SI917_RGB_DRIVER_OLD
sl_si91x_rgb_led_init(&led_red);
sl_si91x_rgb_led_init(&led_green);
sl_si91x_rgb_led_init(&led_blue);
#else
sl_si91x_simple_rgb_led_init(&led_blue);
sl_si91x_simple_rgb_led_init(&led_green);
sl_si91x_simple_rgb_led_init(&led_red);
#endif
}
