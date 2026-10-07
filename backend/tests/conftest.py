from __future__ import annotations

import json
import os
from typing import Any

import pytest

os.environ.setdefault("TWINDOCK_MQTT", "0")  # tests never touch a real broker

from twindock.contract import first_error, validator
from twindock.engine import Engine, MqttOut, WsOut
from twindock.graph import load_layout


class Clock:
    def __init__(self) -> None:
        self.ms = 1_700_000_000_000

    def __call__(self) -> int:
        return self.ms


class Harness:
    """Engine with a controllable clock. Every outgoing WS message is schema-checked."""

    def __init__(self) -> None:
        self.clock = Clock()
        self.engine = Engine(load_layout(), clock=self.clock)
        self.ws: list[WsOut] = []
        self.mqtt: list[MqttOut] = []

    @property
    def world(self):  # type: ignore[no-untyped-def]
        return self.engine.world

    def collect(self) -> None:
        for o in self.engine.drain():
            if isinstance(o, WsOut):
                err = first_error(validator(f"ws/{o.msg['type']}"), o.msg)
                assert err is None, f"{o.msg['type']} violates schema: {err}\n{o.msg}"
                self.ws.append(o)
            else:
                err = first_error(validator("mqtt/gateway_cmd_led"), o.payload)
                assert err is None, err
                self.mqtt.append(o)

    def run(self, seconds: float, dt: float = 0.05) -> None:
        for _ in range(round(seconds / dt)):
            self.clock.ms += int(dt * 1000)
            self.engine.tick(dt)
            self.collect()

    def mqtt_in(self, topic: str, payload: dict[str, Any], retained: bool = False) -> None:
        self.engine.on_mqtt(topic, json.dumps(payload).encode(), retained)
        self.collect()

    def client(self, msg: dict[str, Any], cid: str = "client-1") -> None:
        self.engine.handle_client(cid, json.dumps(msg))
        self.collect()

    def of_type(self, t: str) -> list[dict[str, Any]]:
        return [o.msg for o in self.ws if o.msg["type"] == t]

    def last_ack(self) -> dict[str, Any]:
        return self.of_type("command_ack")[-1]

    def board_online(self, fake: bool = False) -> None:
        self.engine.set_mqtt_connected(True)
        self.mqtt_in("twin/gateway/hello", {"board": "FAKE" if fake else "BRD2605A", "radio_board": "",
                                            "fw_version": "fake" if fake else "1.0.0", "leds": ["LED0", "LED1"],
                                            "buttons": ["BTN0", "BTN1"], "sensors": ["temperature", "humidity"]})
        self.mqtt_in("twin/gateway/status", {"ts_ms": 1000, "uptime_s": 1, "wifi_rssi_dbm": -50})
        self.collect()

    def press(self, button: str, ts_ms: int, held_ms: int = 120) -> None:
        self.mqtt_in("twin/gateway/button", {"ts_ms": ts_ms, "button": button, "state": "pressed"})
        self.mqtt_in("twin/gateway/button", {"ts_ms": ts_ms + held_ms, "button": button, "state": "released"})


@pytest.fixture
def h() -> Harness:
    return Harness()
