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

# Repo layout: <repo>/shared/schemas. A Vercel deploy only bundles backend/, so its build step
# copies the schemas to backend/shared/schemas (see vercel.json); that copy is git-ignored.
_HERE = Path(__file__).resolve()
SHARED = next(
    (p for p in (_HERE.parents[2] / "shared" / "schemas", _HERE.parents[1] / "shared" / "schemas") if p.is_dir()),
    _HERE.parents[2] / "shared" / "schemas",
)

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
CLIENT_TYPES = ("move_unit", "select_unit", "led_command", "set_auto_mode", "machine_command")
SERVER_TYPES = ("world_snapshot", "unit_update", "gateway_update", "selection_changed", "command_ack", "event",
                "ble_tracks", "device_update", "production_update", "safety_update")


@lru_cache(maxsize=1)
def _registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    by_path: dict[str, dict[str, Any]] = {}
    resources = []
    for f in sorted(SHARED.glob("*/*.json")):
        schema = json.loads(f.read_text())
        by_path[f"{f.parent.name}/{f.stem}"] = schema
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources), by_path


@lru_cache(maxsize=None)
def validator(name: str) -> jsonschema.Draft202012Validator:
    """name is "mqtt/gateway_status", "ws/move_unit", ..."""
    registry, by_path = _registry()
    return jsonschema.Draft202012Validator(by_path[name], registry=registry)


@lru_cache(maxsize=None)
def def_validator(name: str) -> jsonschema.Draft202012Validator:
    """Validator for one entry of ws/defs.json, e.g. "site" or "device"."""
    registry, _ = _registry()
    return jsonschema.Draft202012Validator({"$ref": f"twindock/ws/defs.json#/$defs/{name}"}, registry=registry)


def mqtt_validator(kind: str) -> jsonschema.Draft202012Validator:
    return validator(f"mqtt/{MQTT_SCHEMAS[kind]}")


def first_error(v: jsonschema.Draft202012Validator, data: Any) -> str | None:
    """Short description of the first schema violation, or None if valid."""
    err = jsonschema.exceptions.best_match(v.iter_errors(data))
    if err is None:
        return None
    where = "/".join(str(p) for p in err.absolute_path)
    return f"{where}: {err.message}" if where else err.message
