"""Device kits: hardware/kits/<kit_id>.json, served to /wiring/:kit_id and /kits.

Read on every request (the files are small) so edits show up on reload without a backend restart.
Sensor readings are not merged in here: the page reads them from gateway_update.
`validate_kit` holds the electrical and bill-of-materials checks that JSON Schema can't express;
tests run it over every kit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract import first_error, validator

# Repo layout (and the container's /app): <repo>/hardware/kits.
KITS_DIR = Path(__file__).resolve().parents[2] / "hardware" / "kits"
FL01_KIT = "fl01_sensor_pack"


class WiringInvalid(Exception):
    pass


class KitNotFound(Exception):
    pass


def kit_ids() -> list[str]:
    return sorted(p.stem for p in KITS_DIR.glob("*.json"))


def load_kit(kit_id: str) -> dict[str, Any]:
    f = KITS_DIR / f"{kit_id}.json"
    if not kit_id.replace("_", "").isalnum() or not f.is_file():
        raise KitNotFound(kit_id)
    data: dict[str, Any] = json.loads(f.read_text())
    err = first_error(validator("hardware/wiring"), data)
    if err:
        raise WiringInvalid(f"hardware/kits/{kit_id}.json does not match its schema: {err}")
    if data["kit"]["id"] != kit_id:
        raise WiringInvalid(f"hardware/kits/{kit_id}.json: kit.id is {data['kit']['id']!r}, must match the file name")
    return data


def load_wiring() -> dict[str, Any]:
    """The FL-01 sensor pack (the original /api/wiring)."""
    return load_kit(FL01_KIT)


def load_kits() -> list[dict[str, Any]]:
    return [load_kit(i) for i in kit_ids()]


def kit_summary(k: dict[str, Any], devices: list[str] | None = None) -> dict[str, Any]:
    bom = k["bom"]
    cost = [b["unit_cost_usd"] * b["quantity"] for b in bom if b["unit_cost_usd"] is not None]
    return {
        **k["kit"],
        "board": k["board"],
        "part_count": sum(b["quantity"] for b in bom),
        "bom_lines": len(bom),
        "bom_cost_usd": round(sum(cost), 2) if cost else None,
        "bom_cost_complete": len(cost) == len(bom),
        "devices": devices or [],
    }


# Signals that several parts may legitimately share on one pin/net.
_SHARED = {"SDA", "SCL", "INT", "GND", "3V3", "5V", "VIN", "SCK", "MOSI", "MISO", "TX", "RX", "RS485_A", "RS485_B", "ONEWIRE"}


def _shared(signal: str) -> bool:
    """A net several parts may sit on: buses, power, a 1-Wire line, or an analog node (AIN_*: e.g. a shunt and the ADC
    input on the same 4-20 mA node). Anything else on one pin twice means two outputs fighting."""
    return signal in _SHARED or signal.startswith("AIN_")


def _addr(p: dict[str, Any]) -> str | None:
    return p.get("runtime_address") or p.get("address")


def validate_kit(k: dict[str, Any]) -> list[str]:
    """Every problem in one kit (empty list = fine). Schema validity is checked separately."""
    errs: list[str] = []
    parts = {p["id"]: p for p in k["parts"]}
    buses = {b["id"]: b for b in k["buses"]}
    if len(parts) != len(k["parts"]):
        errs.append("duplicate part id")

    # Pins exist; each pin name is unique per part.
    pins: set[str] = set()
    for p in k["parts"]:
        names = [x["name"] for x in p["pins"]]
        if len(set(names)) != len(names):
            errs.append(f"{p['id']}: duplicate pin name")
        pins |= {f"{p['id']}.{n}" for n in names}
        if p["bus"] and p["bus"] not in buses:
            errs.append(f"{p['id']}: unknown bus {p['bus']}")
        if p["supplied_from"] and p["supplied_from"] not in buses:
            errs.append(f"{p['id']}: unknown supply {p['supplied_from']}")
    for c in k["connections"]:
        for ref in (c["from"], c["to"]):
            if ref not in pins:
                errs.append(f"{c['id']}: unknown pin {ref}")
        if c.get("bus") and c["bus"] not in buses:
            errs.append(f"{c['id']}: unknown bus {c['bus']}")
    if len({c["id"] for c in k["connections"]}) != len(k["connections"]):
        errs.append("duplicate connection id")

    # No pin driven twice: a pin carries one signal, and only bus/ground/power style signals may fan out.
    used: dict[str, list[dict[str, Any]]] = {}
    for c in k["connections"]:
        for ref in (c["from"], c["to"]):
            used.setdefault(ref, []).append(c)
    for ref, cs in used.items():
        if len(cs) > 1:
            if len({c["signal"] for c in cs}) > 1:
                errs.append(f"{ref}: used for different signals ({', '.join(sorted({c['signal'] for c in cs}))})")
            elif not _shared(cs[0]["signal"]):
                errs.append(f"{ref}: signal {cs[0]['signal']} wired {len(cs)} times (pin driven twice)")
    gpio_signal: dict[str, set[str]] = {}
    for p in k["parts"]:
        for x in p["pins"]:
            if x.get("gpio") and f"{p['id']}.{x['name']}" in used:
                gpio_signal.setdefault(f"{p['id']}:{x['gpio']}", set()).add(x["signal"])
    for key, sig in gpio_signal.items():
        if len(sig) > 1:
            errs.append(f"{key}: one GPIO assigned to several functions ({', '.join(sorted(sig))})")

    # I2C address clashes per bus (runtime address when the firmware moves the part).
    by_bus: dict[str, dict[str, str]] = {}
    for p in k["parts"]:
        a = _addr(p)
        if a and p["bus"]:
            seen = by_bus.setdefault(p["bus"], {})
            if a in seen:
                errs.append(f"bus {p['bus']}: address {a} used by {seen[a]} and {p['id']}")
            seen[a] = p["id"]
    for p in k["parts"]:
        if p.get("runtime_address") and not any(s["address"] == p["runtime_address"] for s in k["boot_sequence"] if "address" in s):
            errs.append(f"{p['id']}: runtime_address {p['runtime_address']} is not set by any boot_sequence step")

    # Voltage: each part's supply rail must sit inside the part's allowed range.
    for p in k["parts"]:
        rail = buses.get(p["supplied_from"]) if p["supplied_from"] else None
        if rail and rail["voltage_v"] is not None and p.get("supply"):
            v, s = rail["voltage_v"], p["supply"]
            if not s["min_v"] <= v <= s["max_v"]:
                errs.append(f"{p['id']}: rail {rail['id']} is {v} V, part allows {s['min_v']}-{s['max_v']} V")

    # Bill of materials <-> wiring, both directions.
    covered: dict[str, str] = {}
    for b in k["bom"]:
        for pid in b["covers"]:
            if pid not in parts:
                errs.append(f"bom {b['id']}: covers unknown part {pid}")
            elif pid in covered:
                errs.append(f"part {pid} is covered by bom lines {covered[pid]} and {b['id']}")
            covered[pid] = b["id"]
        if b["source"] != "unverified" and not b["link"]:
            errs.append(f"bom {b['id']}: source {b['source']} needs a link")
    errs += [f"part {pid} is not in the bill of materials" for pid in parts if pid not in covered]
    if len({b["id"] for b in k["bom"]}) != len(k["bom"]):
        errs.append("duplicate bom id")

    if k["kit"]["status"] == "built" and k["kit"]["id"] != FL01_KIT:
        errs.append("only the FL-01 sensor pack may have status 'built'")
    return errs
