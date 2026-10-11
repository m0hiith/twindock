"""Loads the JSON Schemas in /shared and validates messages against them.

The schemas are the single definition of every message. The pydantic models in models.py mirror
them for typed access; incoming messages are checked here first so a schema change can never be
silently bypassed by a lenient model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
from referencing import Registry, Resource

from .fastcheck import Check, compile_schema

# Repo layout (and the container's /app): <repo>/shared/schemas.
SHARED = Path(__file__).resolve().parents[2] / "shared" / "schemas"

MQTT_SCHEMAS = {
    "hello": "gateway_hello",
    "status": "gateway_status",
    "button": "gateway_button",
    "led": "gateway_led",
    "ble": "gateway_ble",
    "sensor": "gateway_sensor",
    "cmd_led": "gateway_cmd_led",
    "site_cmd": "site_cmd",
}
CLIENT_TYPES = ("move_unit", "select_unit", "led_command", "set_auto_mode", "machine_command", "ack_alert",
                "scenario_command", "safety_command", "set_sim_speed", "control_decision")
SERVER_TYPES = ("world_snapshot", "unit_update", "gateway_update", "selection_changed", "command_ack", "event",
                "ble_tracks", "device_update", "production_update", "safety_update", "alerts_update", "sim_clock", "control_update")


@lru_cache(maxsize=1)
def _registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    by_path: dict[str, dict[str, Any]] = {}
    resources = []
    for f in sorted(SHARED.glob("*/*.json")):
        schema = json.loads(f.read_text())
        by_path[f"{f.parent.name}/{f.stem}"] = schema
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources), by_path


# Compiled yes/no checks (fastcheck.py) for the validators below, by id(): a valid message skips the slow walk.
_FAST: dict[int, Check] = {}


def _with_fast(v: jsonschema.Draft202012Validator, schema: dict[str, Any]) -> jsonschema.Draft202012Validator:
    _, by_path = _registry()
    chk = compile_schema(schema, {s["$id"]: s for s in by_path.values()}, "twindock/ws/defs.json")
    if chk is not None:
        _FAST[id(v)] = chk
    return v


@lru_cache(maxsize=None)
def validator(name: str) -> jsonschema.Draft202012Validator:
    """name is "mqtt/gateway_status", "ws/move_unit", ..."""
    registry, by_path = _registry()
    return _with_fast(jsonschema.Draft202012Validator(by_path[name], registry=registry), by_path[name])


@lru_cache(maxsize=None)
def def_validator(name: str) -> jsonschema.Draft202012Validator:
    """Validator for one entry of ws/defs.json, e.g. "site" or "device"."""
    registry, _ = _registry()
    schema = {"$ref": f"twindock/ws/defs.json#/$defs/{name}"}
    return _with_fast(jsonschema.Draft202012Validator(schema, registry=registry), schema)


def mqtt_validator(kind: str) -> jsonschema.Draft202012Validator:
    return validator(f"mqtt/{MQTT_SCHEMAS[kind]}")


def first_error(v: jsonschema.Draft202012Validator, data: Any) -> str | None:
    """Short description of the first schema violation, or None if valid."""
    fast = _FAST.get(id(v))
    if fast is not None and fast(data):
        return None  # only "valid" is trusted from the compiled check; errors always come from jsonschema
    err = jsonschema.exceptions.best_match(v.iter_errors(data))
    if err is None:
        return None
    where = "/".join(str(p) for p in err.absolute_path)
    return f"{where}: {err.message}" if where else err.message
