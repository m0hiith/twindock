from conftest import Harness


def test_btn1_selects_next_forklift_for_everyone(h: Harness) -> None:
    h.board_online()
    h.press("BTN1", 2000)
    sel = h.of_type("selection_changed")[-1]
    assert sel == {"type": "selection_changed", "seq": sel["seq"], "selected_unit_id": "FL-01", "by": "BTN1"}
    assert h.ws[-1].to is None or any(o.to is None for o in h.ws if o.msg["type"] == "selection_changed")
    h.press("BTN1", 3000)
    h.press("BTN1", 4000)
    h.press("BTN1", 5000)
    h.press("BTN1", 6000)
    assert [s["selected_unit_id"] for s in h.of_type("selection_changed")] == ["FL-01", "FL-02", "FL-03", "FL-04", "FL-01"]


def test_btn0_runs_next_task_of_selected_forklift(h: Harness) -> None:
    h.board_online()
    h.press("BTN1", 2000)  # FL-01, plan: pick at RACK_A1, then load at DOCK_1
    h.press("BTN0", 3000)
    fl = h.world.entities["FL-01"]
    assert fl.action == "pick" and fl.target == "RACK_A1" and fl.source == "manual"
    assert [s.action for s in fl.plan] == ["load"]
    h.run(25)
    h.press("BTN0", 30000)
    assert fl.action == "load" and fl.target == "DOCK_1"
    h.run(30)
    assert "PL-01" in (h.world.entities["TR-01"].cargo or [])


def test_btn0_while_busy_or_without_selection_does_nothing(h: Harness) -> None:
    h.board_online()
    h.press("BTN0", 2000)
    assert "no forklift selected" in h.of_type("event")[-1]["text"]
    h.press("BTN1", 3000)
    h.press("BTN0", 4000)
    h.press("BTN0", 4500)
    assert "busy" in h.of_type("event")[-1]["text"]


def test_long_press_is_not_a_short_press(h: Harness) -> None:
    h.board_online()
    h.press("BTN1", 2000, held_ms=2000)
    assert h.of_type("selection_changed") == []
    assert h.engine.gw.buttons["BTN1"].state == "released"


def test_led0_follows_bay1_rule(h: Harness) -> None:
    h.board_online()
    assert h.mqtt[-1].payload["led"] == "LED0" and h.mqtt[-1].payload["on"] is True  # TR-01 docked at Bay 1
    gw = h.engine.gw
    assert gw.leds["LED0"].pending is not None and gw.leds["LED0"].on is None  # not on until confirmed
    cmd_id = h.mqtt[-1].payload["cmd_id"]
    h.mqtt_in("twin/gateway/led", {"ts_ms": 1100, "led": "LED0", "on": True, "cmd_id": cmd_id})
    assert gw.leds["LED0"].on is True and gw.leds["LED0"].pending is None
    h.client({"type": "move_unit", "cmd_id": "d1", "unit_id": "TR-01", "target_node": "GATE_IN"})
    assert h.mqtt[-1].payload == {"led": "LED0", "on": False, "cmd_id": h.mqtt[-1].payload["cmd_id"]}


def test_led0_cannot_be_commanded_by_clients(h: Harness) -> None:
    h.board_online()
    h.client({"type": "led_command", "cmd_id": "l1", "led": "LED0", "on": False})
    ack = h.last_ack()
    assert not ack["ok"] and "automatic" in ack["reason"]


def test_led1_pending_until_board_confirms(h: Harness) -> None:
    h.board_online()
    n = len(h.mqtt)
    h.client({"type": "led_command", "cmd_id": "l2", "led": "LED1", "on": True})
    assert h.last_ack()["ok"]
    assert len(h.mqtt) == n + 1 and h.mqtt[-1].topic == "twin/gateway/cmd/led"
    st = h.engine.gw.leds["LED1"]
    assert st.on is None and st.pending is not None and st.pending.on is True
    h.mqtt_in("twin/gateway/led", {"ts_ms": 2000, "led": "LED1", "on": True, "cmd_id": h.mqtt[-1].payload["cmd_id"]})
    assert st.on is True and st.pending is None


def test_led_pending_times_out(h: Harness) -> None:
    h.board_online()
    h.client({"type": "led_command", "cmd_id": "l3", "led": "LED1", "on": True})
    for t in range(4):  # keep the board online while we wait
        h.run(1.5)
        h.mqtt_in("twin/gateway/status", {"ts_ms": 2000 + t * 1500})
    assert h.engine.gw.leds["LED1"].pending is None
    assert h.engine.gw.leds["LED1"].on is None
    assert any("no confirmation" in e["text"] for e in h.of_type("event"))


def test_led_command_rejected_without_board(h: Harness) -> None:
    h.client({"type": "led_command", "cmd_id": "l4", "led": "LED1", "on": True})
    assert h.last_ack()["reason"] == "Waiting for device"


def test_board_goes_stale_after_15s(h: Harness) -> None:
    h.board_online()
    assert h.engine.gw.online
    h.run(14)
    assert h.engine.gw.online
    h.run(1.5)
    assert not h.engine.gw.online
    assert h.world.entities["GW-01"].state == "offline"
    assert h.of_type("gateway_update")[-1]["gateway"]["online"] is False
    h.client({"type": "led_command", "cmd_id": "l5", "led": "LED1", "on": True})
    assert h.last_ack()["reason"] == "Board is offline"


def test_nothing_is_defaulted_before_device_messages(h: Harness) -> None:
    snap = h.engine.snapshot().model_dump(mode="json")["gateway"]
    assert snap == {"online": False, "fake": False, "last_seen_ms": None, "hello": None, "status": None,
                    "buttons": {}, "leds": {}, "ble": None, "sensors": {}}


def test_replayed_status_does_not_replace_current(h: Harness) -> None:
    h.board_online()
    h.mqtt_in("twin/gateway/status", {"ts_ms": 9000, "uptime_s": 9, "wifi_rssi_dbm": -45})
    h.mqtt_in("twin/gateway/status", {"ts_ms": 4000, "uptime_s": 4, "wifi_rssi_dbm": -80, "replay": True})
    assert h.engine.gw.status is not None and h.engine.gw.status.data["ts_ms"] == 9000
    assert h.engine.gw.replays_received == 1


def test_unlisted_hardware_is_dropped(h: Harness) -> None:
    h.engine.set_mqtt_connected(True)
    h.mqtt_in("twin/gateway/hello", {"board": "BRD2605A", "radio_board": "", "fw_version": "1", "leds": ["LED0", "LED1", "LED2"],
                                     "buttons": ["BTN0"], "sensors": ["temperature", "pressure"]})
    gw = h.engine.gw
    assert list(gw.leds) == ["LED0", "LED1"]
    assert gw.sensors_available == ["temperature"]
    h.mqtt_in("twin/gateway/sensor/pressure", {"ts_ms": 1, "value": 1013, "unit": "hPa"})
    h.mqtt_in("twin/gateway/button", {"ts_ms": 1, "button": "BTN1", "state": "pressed"})
    assert gw.sensors == {} and gw.buttons == {}
    h.mqtt_in("twin/gateway/sensor/temperature", {"ts_ms": 2, "value": 22.4, "unit": "C"})
    assert gw.sensors["temperature"].data["value"] == 22.4


def test_invalid_device_payload_is_dropped(h: Harness) -> None:
    h.board_online()
    before = h.engine.gw.status
    h.mqtt_in("twin/gateway/status", {"ts_ms": 5000, "wifi_rssi_dbm": "strong"})
    assert h.engine.gw.status is before
    assert "Dropped invalid" in h.of_type("event")[-1]["text"]


def test_fake_board_is_flagged(h: Harness) -> None:
    h.board_online(fake=True)
    assert h.of_type("gateway_update")[-1]["gateway"]["fake"] is True


def test_own_commands_echoed_back_are_ignored(h: Harness) -> None:
    h.board_online()
    n = len(h.ws)
    h.mqtt_in("twin/gateway/cmd/led", {"led": "LED1", "on": True, "cmd_id": "L1"})
    assert len(h.ws) == n
