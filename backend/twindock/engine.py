"""The backend's single source of truth: world + gateway + shared selection + auto mode.

All inputs (client intents, MQTT messages, ticks) go through Engine methods, which mutate state
and append outgoing messages to self.out. The async layer (main.py) only moves bytes: it feeds
inputs in and sends whatever is in self.out. That keeps every rule testable without sockets.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import TypeAdapter

from . import planner
from .ble_tracker import BleConfig, BleTracker, ZoneChange
from .contract import CLIENT_TYPES, first_error, mqtt_validator, validator
from .gateway import GatewayStore
from .graph import Graph
from .hardware import (EXPOSED_BUTTONS, LED_CONFIRM_TIMEOUT_MS, RULE_LED_RETRY_MS, RULE_LEDS,
                       SHORT_PRESS_MAX_MS)
from .models import (BleTracks, ButtonState, ClientMessage, CommandAck, Event, GatewayUpdate, Layout, LedCommand,
                     MoveUnit, PendingLed, RawMqtt, SelectionChanged, SelectUnit, SetAutoMode, Timed,
                     UnitUpdate, WorldSnapshot)
from .world import World

TOPIC_PREFIX = "twin/gateway/"
CMD_LED_TOPIC = "twin/gateway/cmd/led"
AUTO_PERIOD_S = 1.0  # auto mode re-plans once a second; faster adds nothing visible


@dataclass
class WsOut:
    to: str | None  # client id, or None for everyone
    msg: dict[str, Any]


@dataclass
class MqttOut:
    topic: str
    payload: dict[str, Any]


def wall_ms() -> int:
    return int(time.time() * 1000)


_client_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


class Engine:
    def __init__(self, layout: Layout, clock: Callable[[], int] = wall_ms, ble_config: BleConfig | None = None) -> None:
        self.layout = layout
        self.clock = clock
        graph = Graph(layout)
        self.world = World(layout, graph)
        forklift_nodes = {n.id for n in layout.nodes if "forklift" in n.kinds}
        self.ble = BleTracker(ble_config if ble_config is not None else BleConfig.load(valid_nodes=forklift_nodes))
        self._device_goal: dict[str, str] = {}   # forklift -> zone node its tag says it is in
        self._device_sent: dict[str, str] = {}   # forklift -> goal already turned into a move
        self.gw = GatewayStore()
        self.selected: str | None = None
        self.auto_mode = False
        self.mqtt_connected = False
        self.out: list[WsOut | MqttOut] = []
        self._seq = 0
        self._last_wire: dict[str, dict[str, Any]] = {}
        self._auto_acc = 0.0
        self._truck_cargo: dict[str, int] = {}
        self._led_cmd_counter = 0
        self._rule_retry_after: dict[str, int] = {}
        self._auto_mode_dirty = False

    # ------------------------------------------------------------------ output helpers

    def drain(self) -> list[WsOut | MqttOut]:
        out, self.out = self.out, []
        return out

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _send(self, msg: Any, to: str | None = None) -> None:
        self.out.append(WsOut(to, msg.model_dump(mode="json")))

    def event(self, level: str, text: str, source: str = "system", unit_id: str | None = None,
              to: str | None = None) -> None:
        self._send(Event(seq=self._next_seq(), server_ts_ms=self.clock(), level=level,  # type: ignore[arg-type]
                         source=source, text=text, unit_id=unit_id), to)

    def _ack(self, to: str, cmd_id: str, command: str, ok: bool, reason: str | None = None,
             path: list[str] | None = None) -> None:
        self._send(CommandAck(cmd_id=cmd_id, command=command, ok=ok, reason=reason, path=path), to)  # type: ignore[arg-type]

    def _gateway_update(self, raw: RawMqtt | None = None) -> None:
        self._send(GatewayUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), gateway=self.gw.wire(), raw=raw))

    def _all_units(self) -> list[Any]:
        return [self.world.to_unit(e) for e in self.world.entities.values()]

    def snapshot(self) -> WorldSnapshot:
        units = self._all_units()
        self._last_wire = {u.id: u.model_dump(mode="json") for u in units}
        return WorldSnapshot(seq=self._next_seq(), server_ts_ms=self.clock(), layout_version=self.layout.version,
                             auto_mode=self.auto_mode, selected_unit_id=self.selected, units=units,
                             gateway=self.gw.wire())

    def _flush_units(self) -> None:
        changed = []
        for u in self._all_units():
            d = u.model_dump(mode="json")
            if self._last_wire.get(u.id) != d:
                self._last_wire[u.id] = d
                changed.append(u)
        if changed or self._auto_mode_dirty:
            self._send(UnitUpdate(seq=self._next_seq(), server_ts_ms=self.clock(), units=changed,
                                  auto_mode=self.auto_mode if self._auto_mode_dirty else None))
            self._auto_mode_dirty = False

    def _drain_world_events(self) -> None:
        for level, text, unit_id in self.world.events:
            self.event(level, text, "system", unit_id)
        self.world.events.clear()

    # ------------------------------------------------------------------ lifecycle

    def on_connect(self, client_id: str) -> None:
        self._send(self.snapshot(), client_id)
        self._send_ble_tracks(client_id)

    def reset(self) -> None:
        """Restore the seed world. Gateway state is real device data and is kept."""
        self.world.reset()
        # Every forklift is back at its seed spot and manual; tags re-acquire after stable_s.
        self.ble.forget_zones()
        self._device_goal.clear()
        self._device_sent.clear()
        self.selected = None
        self.auto_mode = False
        self._truck_cargo.clear()
        self._send(self.snapshot())
        self.event("info", "World reset to the seed layout")
        self._sync_rule_leds()

    def set_mqtt_connected(self, connected: bool) -> None:
        if connected == self.mqtt_connected:
            return
        self.mqtt_connected = connected
        self.event("info" if connected else "warn",
                   "Connected to the MQTT broker" if connected else "Lost the MQTT broker, reconnecting", "gateway")
        if connected:
            self._sync_rule_leds()

    def tick(self, dt: float) -> None:
        w = self.world
        w.tick(dt)
        planner.track_idle(w, self._truck_cargo)
        if self.auto_mode:
            self._auto_acc += dt
            if self._auto_acc >= AUTO_PERIOD_S:
                self._auto_acc = 0.0
                for note in planner.auto_step(w):
                    self.event("info", note, "auto")
        else:
            for u in w.entities.values():
                if u.source == "auto" and not u.moving and not u.busy and u.action is None:
                    u.source = "manual"

        now = self.clock()
        lost = self.ble.expire(now)
        for t in lost:
            self._release_device(t.unit_id, f"Tag {t.name} not seen for {self.ble.config.lost_after_s:g} s")
        if lost:
            self._send_ble_tracks()
        for uid, goal in self._device_goal.items():
            if self._device_sent.get(uid) != goal:
                self._drive_device(uid)  # was busy finishing a pick or load when the zone changed
        if self.gw.refresh_online(now):
            self._on_online_changed()
        for name, st in self.gw.leds.items():
            if st.pending and now - st.pending.sent_ms > LED_CONFIRM_TIMEOUT_MS:
                st.pending = None
                if name in RULE_LEDS:
                    self._rule_retry_after[name] = now + RULE_LED_RETRY_MS
                self.event("warn", f"{name}: no confirmation from the board within "
                           f"{LED_CONFIRM_TIMEOUT_MS // 1000} s", "gateway")
                self._gateway_update()
        self._sync_rule_leds()
        self._drain_world_events()
        self._flush_units()

    def _on_online_changed(self) -> None:
        self.world.gateway_state = "online" if self.gw.online else ("offline" if self.gw.last_status_ms else "waiting")
        self.world.entities[self.layout.gateway.id].state = self.world.gateway_state
        if self.gw.online:
            self.event("info", "Board online", "gateway")
            self._rule_retry_after.clear()
            self._gateway_update()
            self._sync_rule_leds()  # the board may have rebooted with the LED off
            return
        else:
            self.event("warn", "Board offline: no status for 15 s", "gateway")
        self._gateway_update()

    # ------------------------------------------------------------------ LEDs

    def _send_led(self, led: str, on: bool) -> None:
        # Server-generated id: short (fits the firmware's buffer, schema max 36) and never client text.
        self._led_cmd_counter += 1
        cmd_id = f"L{self._led_cmd_counter:06d}"
        payload = {"led": led, "on": on, "cmd_id": cmd_id}
        err = first_error(mqtt_validator("cmd_led"), payload)
        assert err is None, err
        self.out.append(MqttOut(CMD_LED_TOPIC, payload))
        self.gw.leds[led].pending = PendingLed(cmd_id=cmd_id, on=on, sent_ms=self.clock())
        self._gateway_update()

    def _sync_rule_leds(self) -> None:
        """LED0 follows Bay 1. Sends a command only when the confirmed state differs."""
        if "LED0" not in self.gw.leds or not self.gw.online or not self.mqtt_connected:
            return
        if self.clock() < self._rule_retry_after.get("LED0", 0):
            return
        desired = self.world.bay1_occupied()
        st = self.gw.leds["LED0"]
        if st.pending is not None:
            if st.pending.on == desired:
                return
        elif st.on == desired:
            return
        self._send_led("LED0", desired)

    # ------------------------------------------------------------------ MQTT in

    def on_mqtt(self, topic: str, payload: bytes, retained: bool = False) -> None:
        if not topic.startswith(TOPIC_PREFIX) or topic.startswith(TOPIC_PREFIX + "cmd/"):
            return  # our own commands echo back through the twin/gateway/# subscription
        rest = topic[len(TOPIC_PREFIX):]
        sensor_name = None
        if rest.startswith("sensor/"):
            kind, sensor_name = "sensor", rest[len("sensor/"):]
        elif rest in ("hello", "status", "button", "led", "ble"):
            kind = rest
        else:
            self.event("warn", f"Ignored unknown topic {topic}", "gateway")
            return
        now = self.clock()
        if not payload:
            if kind == "hello":  # retained hello cleared (mosquitto_pub -r -n)
                self.gw.hello = None
                self.gw.leds, self.gw.buttons, self.gw.sensors = {}, {}, {}
                self._gateway_update(RawMqtt(topic=topic, payload=None, received_ms=now))
            return
        try:
            data = json.loads(payload)
        except ValueError:
            self.event("warn", f"Dropped {topic}: not JSON", "gateway")
            return
        err = first_error(mqtt_validator(kind), data)
        if err:
            self.event("warn", f"Dropped invalid {topic}: {err}", "gateway")
            return
        if kind != "hello" and self.gw.hello is None:
            self.event("warn", f"Dropped {topic}: no hello from the board yet", "gateway")
            return

        self.gw.last_seen_ms = now
        if kind == "hello":
            ignored = self.gw.set_hello(data, now, retained)
            if ignored:
                self.event("warn", f"Board reports {', '.join(ignored)}, not in HARDWARE.md; ignored", "gateway")
        elif kind == "status":
            if data.get("replay"):
                self.gw.replays_received += 1
            else:
                self.gw.status = Timed(data=data, received_ms=now)
            self.gw.last_status_ms = now
            if self.gw.refresh_online(now):
                self._on_online_changed()
        elif kind == "button":
            name = data["button"]
            if name not in self.gw.buttons_available:
                self.event("warn", f"Dropped {name}: not an exposed button", "gateway")
                return
            prev = self.gw.buttons.get(name)
            self.gw.buttons[name] = ButtonState(state=data["state"], received_ms=now, ts_ms=data["ts_ms"])
            if data["state"] == "released" and prev is not None and prev.state == "pressed":
                held = data["ts_ms"] - prev.ts_ms  # both board clock, so network jitter doesn't count
                if 0 <= held <= SHORT_PRESS_MAX_MS:
                    self._gateway_update(RawMqtt(topic=topic, payload=data, received_ms=now))
                    self.on_short_press(name)
                    self._sync_rule_leds()
                    self._drain_world_events()
                    self._flush_units()
                    return
        elif kind == "led":
            name = data["led"]
            st = self.gw.leds.get(name)
            if st is None:
                self.event("warn", f"Dropped {name}: not an exposed LED", "gateway")
                return
            st.on, st.received_ms = data["on"], now
            p = st.pending
            if p and (data.get("cmd_id") == p.cmd_id or (data.get("cmd_id") is None and data["on"] == p.on)):
                st.pending = None
        elif kind == "ble":
            self.gw.ble = Timed(data=data, received_ms=now)
            self._apply_ble(self.ble.update(data["sightings"], now))
            self._send_ble_tracks()
        elif kind == "sensor":
            assert sensor_name is not None
            if sensor_name not in self.gw.sensors_available:
                self.event("warn", f"Dropped sensor {sensor_name}: not in hello or HARDWARE.md", "gateway")
                return
            self.gw.sensors[sensor_name] = Timed(data=data, received_ms=now)

        self._gateway_update(RawMqtt(topic=topic, payload=data, received_ms=now))
        if kind == "hello":
            self._sync_rule_leds()

    # ------------------------------------------------------------------ BLE tags -> live forklifts

    def _send_ble_tracks(self, to: str | None = None) -> None:
        self._send(BleTracks(seq=self._next_seq(), server_ts_ms=self.clock(), **self.ble.wire()), to)

    def _apply_ble(self, changes: list[ZoneChange]) -> None:
        w = self.world
        for c in changes:
            u = w.entities.get(c.unit_id or "")
            if u is None or u.kind != "forklift":
                if c.first:
                    self.event("warn", f"Tag {c.tag} has no matching forklift", "gateway")
                continue
            if c.zone is None:
                if u.source == "device":
                    self.event("info", f"{u.id}: tag {c.tag} is beyond the calibrated zones, holding position",
                               "gateway", u.id)
                continue
            label = w.node_label(c.zone)
            if u.source != "device":
                u.source = "device"  # from now on only the tag moves it, even if it is mid-pick
                self.event("info", f"{u.id} is now tracked by tag {c.tag} ({label})", "gateway", u.id)
            else:
                self.event("info", f"{u.id}: tag {c.tag} moved to {label}", "gateway", u.id)
            self._device_goal[u.id] = c.zone
            self._drive_device(u.id)

    def _drive_device(self, uid: str) -> None:
        u = self.world.entities[uid]
        goal = self._device_goal[uid]
        if u.busy:
            return  # finish the pallet handling first; tick() retries
        self._device_sent[uid] = goal
        if u.target == goal or (u.node == goal and not u.moving):
            return
        r = self.world.command(uid, goal, "goto", source="device")
        if not r.ok:
            self.event("warn", f"{uid}: can't follow tag to {self.world.node_label(goal)}: {r.reason}", "gateway", uid)

    def _release_device(self, uid: str | None, why: str) -> None:
        u = self.world.entities.get(uid or "")
        self._device_goal.pop(uid or "", None)
        self._device_sent.pop(uid or "", None)
        if u is not None and u.source == "device":
            u.source = "manual"
            self.event("warn", f"{why}; {u.id} is back under manual control", "gateway", u.id)

    # ------------------------------------------------------------------ physical buttons

    def on_short_press(self, button: str) -> None:
        assert button in EXPOSED_BUTTONS
        w = self.world
        forklifts = sorted(f.id for f in w.of_kind("forklift"))
        if button == "BTN1":
            if self.selected in forklifts:
                nxt = forklifts[(forklifts.index(self.selected) + 1) % len(forklifts)]
            else:
                nxt = forklifts[0]
            self.selected = nxt
            self._send(SelectionChanged(seq=self._next_seq(), selected_unit_id=nxt, by="BTN1"))
            self.event("info", f"Selected {nxt}", "BTN1", nxt)
            return
        # BTN0: the selected forklift runs the next step of its task list.
        if self.selected not in forklifts:
            self.event("warn", "BTN0: no forklift selected (press BTN1 to select one)", "BTN0")
            return
        f = w.entities[self.selected or ""]
        if f.source == "device":
            self.event("warn", f"BTN0: {f.id} is tracked by the board", "BTN0", f.id)
            return
        if f.moving or f.busy:
            self.event("warn", f"BTN0: {f.id} is busy ({f.state})", "BTN0", f.id)
            return
        ok, text = planner.run_next_step(w, f, "manual")
        self.event("info" if ok else "warn", text, "BTN0", f.id)

    # ------------------------------------------------------------------ client intents

    def handle_client(self, client_id: str, text: str) -> None:
        try:
            data = json.loads(text)
        except ValueError:
            self.event("error", "Message is not JSON", client_id, to=client_id)
            return
        mtype = data.get("type") if isinstance(data, dict) else None
        if mtype not in CLIENT_TYPES:
            self.event("error", f"Unknown message type {mtype!r}", client_id, to=client_id)
            return
        err = first_error(validator(f"ws/{mtype}"), data)
        if err:
            cmd_id = data.get("cmd_id")
            if isinstance(cmd_id, str) and 0 < len(cmd_id) <= 64:
                self._ack(client_id, cmd_id, mtype, False, f"Invalid message: {err}")
            else:
                self.event("error", f"Invalid {mtype}: {err}", client_id, to=client_id)
            return
        msg = _client_adapter.validate_python(data)
        if isinstance(msg, MoveUnit):
            self._move(client_id, msg)
        elif isinstance(msg, SelectUnit):
            self._select(client_id, msg)
        elif isinstance(msg, LedCommand):
            self._led_command(client_id, msg)
        elif isinstance(msg, SetAutoMode):
            self.auto_mode = msg.enabled
            self._auto_mode_dirty = True
            self._ack(client_id, msg.cmd_id, "set_auto_mode", True)
            self.event("info", f"Auto mode {'on' if msg.enabled else 'off'}", client_id)
        self._sync_rule_leds()
        self._drain_world_events()
        self._flush_units()

    def _move(self, client_id: str, m: MoveUnit) -> None:
        r = self.world.command(m.unit_id, m.target_node, m.action, m.pallet_id, source="manual", dry_run=m.dry_run)
        self._ack(client_id, m.cmd_id, "move_unit", r.ok, r.reason, r.path)

    def _select(self, client_id: str, m: SelectUnit) -> None:
        if m.unit_id is not None and m.unit_id not in self.world.entities:
            self._ack(client_id, m.cmd_id, "select_unit", False, f"Unknown unit {m.unit_id}")
            return
        self._ack(client_id, m.cmd_id, "select_unit", True)
        if m.unit_id != self.selected:
            self.selected = m.unit_id
            self._send(SelectionChanged(seq=self._next_seq(), selected_unit_id=m.unit_id, by=client_id))

    def _led_command(self, client_id: str, m: LedCommand) -> None:
        def reject(reason: str) -> None:
            self._ack(client_id, m.cmd_id, "led_command", False, reason)
        if self.gw.hello is None:
            return reject("Waiting for device")
        if m.led not in self.gw.leds:
            return reject(f"{m.led} is not on this board")
        if m.led in RULE_LEDS:
            return reject(f"{m.led} is automatic: {RULE_LEDS[m.led]}")
        if not self.mqtt_connected:
            return reject("Not connected to the MQTT broker")
        if not self.gw.online:
            return reject("Board is offline")
        self._send_led(m.led, m.on)
        self._ack(client_id, m.cmd_id, "led_command", True)
