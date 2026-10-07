"""What the backend will accept from the board. Mirrors "Exposed in TwinDock" in HARDWARE.md.

The board's hello lists what it has; the backend only exposes the intersection of that list and
this one, so neither a firmware bug nor the fake board can make the UI show hardware that is not
verified on the real BRD2605A.
"""

EXPOSED_LEDS = ("LED0", "LED1")          # green and blue channels of the single RGB LED (led0)
EXPOSED_BUTTONS = ("BTN0", "BTN1")
EXPOSED_SENSORS = ("temperature", "humidity")  # Si7021

# LEDs driven by a backend rule, not by clients.
RULE_LEDS = {"LED0": "on while a truck is docked at Bay 1"}

STALE_AFTER_MS = 15_000       # CLAUDE.md: board is offline when status is older than 15 s (3 missed publishes)
SHORT_PRESS_MAX_MS = 800      # longer holds are not "short presses" and do nothing (reserved)
LED_CONFIRM_TIMEOUT_MS = 5_000  # pending LED command is dropped if the board does not confirm
RULE_LED_RETRY_MS = 30_000    # after a timeout, wait before re-sending a rule LED command
