"""Gateway (board) state, built only from MQTT messages the board actually sent.

Nothing here is ever defaulted: a value that never arrived stays None and the UI shows
"Waiting for device".
"""

from __future__ import annotations

from typing import Any

from .hardware import EXPOSED_BUTTONS, EXPOSED_LEDS, EXPOSED_SENSORS, STALE_AFTER_MS
from .models import ButtonState, Gateway, LedState, Timed, TimedHello


class GatewayStore:
    def __init__(self) -> None:
        self.hello: TimedHello | None = None
        self.status: Timed | None = None
        self.buttons: dict[str, ButtonState] = {}
        self.leds: dict[str, LedState] = {}
        self.ble: Timed | None = None
        self.sensors: dict[str, Timed] = {}
        self.last_seen_ms: int | None = None
        self.last_status_ms: int | None = None  # includes replays: any status proves the board is reachable
        self.replays_received = 0
        self.online = False

    @property
    def fake(self) -> bool:
        if self.hello and (self.hello.data.get("fw_version") == "fake" or self.hello.data.get("board") == "FAKE"):
            return True
        return bool(self.status and self.status.data.get("fw_version") == "fake")

    def _listed(self, key: str, allowed: tuple[str, ...]) -> list[str]:
        if self.hello is None:
            return []
        return [x for x in self.hello.data.get(key, []) if x in allowed]

    @property
    def leds_available(self) -> list[str]:
        return self._listed("leds", EXPOSED_LEDS)

    @property
    def buttons_available(self) -> list[str]:
        return self._listed("buttons", EXPOSED_BUTTONS)

    @property
    def sensors_available(self) -> list[str]:
        return self._listed("sensors", EXPOSED_SENSORS)

    def set_hello(self, data: dict[str, Any], now: int, retained: bool) -> list[str]:
        """Store hello and reshape LED/button/sensor maps. Returns names that were ignored."""
        self.hello = TimedHello(data=data, received_ms=now, retained=retained)
        ignored = ([x for x in data["leds"] if x not in EXPOSED_LEDS] +
                   [x for x in data["buttons"] if x not in EXPOSED_BUTTONS] +
                   [x for x in data["sensors"] if x not in EXPOSED_SENSORS])
        self.leds = {n: self.leds.get(n, LedState(on=None, received_ms=None, pending=None)) for n in self.leds_available}
        self.buttons = {n: b for n, b in self.buttons.items() if n in self.buttons_available}
        self.sensors = {n: s for n, s in self.sensors.items() if n in self.sensors_available}
        return ignored

    def refresh_online(self, now: int) -> bool:
        """Recompute online. Returns True if it changed."""
        online = self.last_status_ms is not None and now - self.last_status_ms <= STALE_AFTER_MS
        changed = online != self.online
        self.online = online
        return changed

    def wire(self) -> Gateway:
        return Gateway(online=self.online, fake=self.fake, last_seen_ms=self.last_seen_ms, hello=self.hello,
                       status=self.status, buttons=self.buttons, leds=self.leds, ble=self.ble, sensors=self.sensors)
