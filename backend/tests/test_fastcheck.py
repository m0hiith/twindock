"""The compiled schema check (fastcheck.py) must agree with jsonschema on every message, valid or not."""

from __future__ import annotations

import copy
import json
import random
from typing import Any

from conftest import Harness

from twindock import contract
from twindock.embedded_sim import EmbeddedSim

ODD_VALUES: list[Any] = [None, -1, 0, 1.5, -0.5, "", "x" * 300, True, False, [], {}, [1, 2], "LED9", 10**12]


def mutations(msg: Any, rng: random.Random, n: int) -> list[Any]:
    """Copies of msg with one change each: a key dropped or added, or one leaf value swapped for an odd one."""
    paths: list[list[Any]] = []

    def walk(x: Any, path: list[Any]) -> None:
        paths.append(path)
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, path + [k])
        elif isinstance(x, list):
            for i, v in enumerate(x[:3]):
                walk(v, path + [i])
    walk(msg, [])
    out = []
    for _ in range(n):
        m = copy.deepcopy(msg)
        path = rng.choice(paths)
        parent: Any = m
        for p in path[:-1]:
            parent = parent[p]
        r = rng.random()
        if not path:
            out.append(rng.choice(ODD_VALUES))
            continue
        if isinstance(parent, dict) and r < 0.25:
            parent.pop(path[-1], None)
        elif isinstance(parent, dict) and r < 0.35:
            parent["zz_extra"] = 1
        else:
            parent[path[-1]] = rng.choice(ODD_VALUES)
        out.append(m)
    return out


def agree(name: str, v: Any, data: Any) -> None:
    fast = contract._FAST[id(v)](data)
    slow = v.is_valid(data)
    assert fast == slow, f"{name}: fastcheck says {fast}, jsonschema says {slow} for {json.dumps(data)[:400]}"


def test_fastcheck_agrees_with_jsonschema() -> None:
    h = Harness()
    inbound: list[tuple[str, dict[str, Any]]] = []
    real = h.engine.on_mqtt

    def spy(topic: str, payload: bytes, retained: bool = False) -> None:
        if payload:
            inbound.append((topic, json.loads(payload)))
        real(topic, payload, retained)
    h.engine.on_mqtt = spy  # type: ignore[method-assign]
    sim = EmbeddedSim(h.engine, seed=3)
    sim.start()
    h.board_online()
    h.engine.on_connect("client-1")
    h.client({"type": "set_auto_mode", "cmd_id": "a1", "enabled": True})
    h.client({"type": "select_unit", "cmd_id": "a2", "unit_id": "FL-01"})
    for _ in range(240):  # one simulated minute
        sim.step(0.25)
        h.run(0.25, dt=0.25)
    rng = random.Random(5)
    by_schema: dict[str, list[Any]] = {}
    for o in h.ws:
        by_schema.setdefault(f"ws/{o.msg['type']}", []).append(o.msg)
    for topic, data in inbound:
        if topic.startswith("twin/gateway/"):
            kind = topic.removeprefix("twin/gateway/").split("/")[0]
            by_schema.setdefault(f"mqtt/{contract.MQTT_SCHEMAS[kind]}", []).append(data)
            continue
        ch = topic.rsplit("/", 1)[1]
        by_schema.setdefault({"hello": "mqtt/site_hello", "status": "mqtt/site_status"}.get(ch, "mqtt/site_reading"), []).append(data)
    assert len(by_schema) >= 14, sorted(by_schema)
    checked = 0
    for name, msgs in by_schema.items():
        v = contract.validator(name)
        for m in rng.sample(msgs, min(len(msgs), 25)):
            agree(name, v, m)
            for bad in mutations(m, rng, 12):
                agree(name, v, bad)
                checked += 1
    assert checked > 2000


def test_every_schema_compiles() -> None:
    for f in sorted(contract.SHARED.glob("*/*.json")):
        v = contract.validator(f"{f.parent.name}/{f.stem}")
        assert id(v) in contract._FAST, f"{f} uses a keyword fastcheck.py doesn't know; add it there"
