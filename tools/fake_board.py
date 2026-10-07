#!/usr/bin/env python3
"""FAKE BOARD: development stand-in for the SiWx917 firmware.

Publishes exactly the topics and payloads defined in shared/schemas/mqtt (every payload is
validated against those schemas before it is sent), so the backend and UI can be built before
the firmware is ready. It identifies itself with board="FAKE" and fw_version="fake"; the
backend flags that and the UI shows a FAKE BOARD banner.

Development only. Never run this during the demo.

Interactive commands (type and press Enter):
  b0 / b1        short press of BTN0 / BTN1 (pressed, then released after 150 ms)
  h0 / h1        toggle hold of BTN0 / BTN1
  off <seconds>  simulate a Wi-Fi drop: disconnect, buffer status messages, reconnect, flush
  q              quit
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import jsonschema
import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "shared" / "schemas" / "mqtt"

BANNER = """
################################################################
#                                                              #
#   FAKE BOARD  -  FAKE BOARD  -  FAKE BOARD  -  FAKE BOARD    #
#                                                              #
#   This is tools/fake_board.py, NOT the SiWx917.              #
#   fw_version = "fake". Development only. Never demo this.    #
#                                                              #
################################################################
"""

STATUS_PERIOD_S = 5.0  # matches the firmware contract in CLAUDE.md
BLE_PERIOD_S = 2.0
BUFFER_MAX = 50  # firmware buffers up to 50 status messages while offline
SENSOR_PERIOD_S = 10.0  # matches HARDWARE.md (Si7021 every 10 s)


def load_validators() -> dict[str, jsonschema.Draft202012Validator]:
    names = ["hello", "status", "button", "led", "ble", "sensor", "cmd_led"]
    return {
        n: jsonschema.Draft202012Validator(json.loads((SCHEMA_DIR / f"gateway_{n}.json").read_text()))
        for n in names
    }


class FakeBoard:
    def __init__(self, host: str, port: int, leds: list[str], buttons: list[str], tags: list[str]) -> None:
        self.host = host
        self.port = port
        self.leds = leds
        self.buttons = buttons
        self.v = load_validators()
        self.boot = time.monotonic()
        self.led_state = {led: False for led in leds}
        self.btn_held = {b: False for b in buttons}
        self.msgs_sent = 0
        self.reconnects = 0
        self.buffered_last = 0
        self.offline_until = 0.0
        self.buffer: deque[dict[str, Any]] = deque(maxlen=BUFFER_MAX)
        self.rssi = -48.0
        self.tags = [{"name": t, "addr": self._addr(i), "rssi": -65.0} for i, t in enumerate(tags)]
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.connected = threading.Event()

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="twindock-fake-board")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    @staticmethod
    def _addr(i: int) -> str:
        return f"FA:CE:00:00:00:{i + 1:02X}"

    def ts_ms(self) -> int:
        return int((time.monotonic() - self.boot) * 1000)

    def online(self) -> bool:
        return time.monotonic() >= self.offline_until

    # ---- publishing -------------------------------------------------------

    def publish(self, kind: str, topic: str, payload: dict[str, Any], retain: bool = False) -> None:
        self.v[kind].validate(payload)  # never send anything the contract does not allow
        self.client.publish(topic, json.dumps(payload, separators=(",", ":")), qos=0, retain=retain)
        self.msgs_sent += 1
        print(f"  -> {topic} {json.dumps(payload)}")

    def hello(self) -> None:
        self.publish(
            "hello",
            "twin/gateway/hello",
            {
                "board": "FAKE",
                "radio_board": "",
                "fw_version": "fake",
                "leds": self.leds,
                "buttons": self.buttons,
                "sensors": ["temperature", "humidity"],
            },
            retain=True,
        )

    def status_payload(self) -> dict[str, Any]:
        self.rssi = max(-90.0, min(-30.0, self.rssi + random.uniform(-2, 2)))
        return {
            "ts_ms": self.ts_ms(),
            "uptime_s": int(time.monotonic() - self.boot),
            "wifi_rssi_dbm": round(self.rssi),
            "wifi_connected": True,
            "ip": "127.0.0.1",
            "fw_version": "fake",
            "msgs_sent": self.msgs_sent,
            "reconnects": self.reconnects,
            "buffered": self.buffered_last,
        }

    # ---- MQTT callbacks ---------------------------------------------------

    def _on_connect(self, client: mqtt.Client, _ud: Any, _flags: Any, reason: Any, _props: Any) -> None:
        print(f"[fake] connected to {self.host}:{self.port} ({reason})")
        client.subscribe("twin/gateway/cmd/led")
        self.hello()
        self.connected.set()

    def _on_message(self, _c: mqtt.Client, _ud: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            cmd = json.loads(msg.payload)
            self.v["cmd_led"].validate(cmd)
        except (ValueError, jsonschema.ValidationError) as e:
            print(f"[fake] rejected bad command on {msg.topic}: {e}")
            return
        if cmd["led"] not in self.led_state:
            print(f"[fake] ignoring command for unknown LED {cmd['led']}")
            return
        # A real board takes a few ms to drive the pin; delay so the UI's pending state is visible.
        def confirm() -> None:
            time.sleep(0.3)
            self.led_state[cmd["led"]] = cmd["on"]
            self.publish("led", "twin/gateway/led", {"ts_ms": self.ts_ms(), "led": cmd["led"], "on": cmd["on"], "cmd_id": cmd["cmd_id"]})

        threading.Thread(target=confirm, daemon=True).start()

    # ---- loops ------------------------------------------------------------

    def status_loop(self) -> None:
        while not self.stop.wait(STATUS_PERIOD_S):
            with self.lock:
                payload = self.status_payload()
                if self.online():
                    self.publish("status", "twin/gateway/status", payload)
                else:
                    payload["wifi_connected"] = False
                    self.buffer.append(payload)
                    print(f"[fake] offline, buffered status ({len(self.buffer)}/{BUFFER_MAX})")

    def ble_loop(self) -> None:
        while not self.stop.wait(BLE_PERIOD_S):
            if not self.online():
                continue
            sightings = []
            for t in self.tags:
                t["rssi"] = max(-95.0, min(-40.0, t["rssi"] + random.uniform(-4, 4)))
                sightings.append({"name": t["name"], "addr": t["addr"], "rssi_dbm": round(t["rssi"])})
            self.publish("ble", "twin/gateway/ble", {"ts_ms": self.ts_ms(), "sightings": sightings})

    def sensor_loop(self) -> None:
        temp, hum = 21.5, 45.0
        while not self.stop.wait(SENSOR_PERIOD_S):
            if not self.online():
                continue
            temp += random.uniform(-0.1, 0.1)
            hum += random.uniform(-0.3, 0.3)
            self.publish("sensor", "twin/gateway/sensor/temperature", {"ts_ms": self.ts_ms(), "value": round(temp, 2), "unit": "C"})
            self.publish("sensor", "twin/gateway/sensor/humidity", {"ts_ms": self.ts_ms(), "value": round(hum, 1), "unit": "%RH"})

    def button(self, name: str, state: str) -> None:
        self.publish("button", "twin/gateway/button", {"ts_ms": self.ts_ms(), "button": name, "state": state})

    def go_offline(self, seconds: float) -> None:
        print(f"[fake] simulating Wi-Fi drop for {seconds:.0f} s")
        self.offline_until = time.monotonic() + seconds
        self.client.disconnect()

        def back() -> None:
            time.sleep(seconds)
            with self.lock:
                self.reconnects += 1
                self.client.reconnect()
                time.sleep(0.5)
                n = len(self.buffer)
                while self.buffer:
                    self.publish("status", "twin/gateway/status", self.buffer.popleft())
                self.buffered_last = n
                print(f"[fake] reconnected, flushed {n} buffered status messages")

        threading.Thread(target=back, daemon=True).start()

    def run(self) -> None:
        print(BANNER)
        self.client.connect(self.host, self.port, keepalive=30)
        self.client.loop_start()
        if not self.connected.wait(10):
            sys.exit(f"[fake] could not connect to broker at {self.host}:{self.port}")
        threading.Thread(target=self.status_loop, daemon=True).start()
        threading.Thread(target=self.ble_loop, daemon=True).start()
        threading.Thread(target=self.sensor_loop, daemon=True).start()
        print(__doc__.split("Interactive commands")[1] if __doc__ else "")
        try:
            for line in sys.stdin:
                parts = line.strip().split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                if cmd == "q":
                    break
                if cmd in ("b0", "b1", "h0", "h1"):
                    name = f"BTN{cmd[1]}"
                    if name not in self.buttons:
                        print(f"[fake] {name} is not in this board's button list")
                        continue
                    if cmd[0] == "b":
                        self.button(name, "pressed")
                        time.sleep(0.15)
                        self.button(name, "released")
                    else:
                        self.btn_held[name] = not self.btn_held[name]
                        self.button(name, "pressed" if self.btn_held[name] else "released")
                elif cmd == "off":
                    self.go_offline(float(parts[1]) if len(parts) > 1 else 20.0)
                else:
                    print("commands: b0 b1 h0 h1 off <s> q")
        except KeyboardInterrupt:
            pass
        finally:
            self.stop.set()
            self.client.loop_stop()
            self.client.disconnect()
            print("[fake] stopped")


def main() -> None:
    ap = argparse.ArgumentParser(description="FAKE BOARD for TwinDock development")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    # Defaults match "Exposed in TwinDock" in HARDWARE.md.
    ap.add_argument("--leds", default="LED0,LED1")
    ap.add_argument("--buttons", default="BTN0,BTN1")
    ap.add_argument("--tags", default="TD-FL01,TD-FL02", help="fake BLE tag names (must start with TD-)")
    a = ap.parse_args()
    FakeBoard(a.host, a.port, a.leds.split(","), a.buttons.split(","), a.tags.split(",")).run()


if __name__ == "__main__":
    main()
