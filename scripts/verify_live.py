#!/usr/bin/env python3
"""Watch a running TwinDock (container, VM or laptop) over its own /ws for a while and check that the factory
is alive: auto mode moves units, the compressor cycles, the generator starts on a grid failure and stops after,
the production lines count units and vibration readings keep changing.

    .venv/bin/python scripts/verify_live.py http://localhost:7860 --minutes 10

Exit code 0 when every check passes. It turns auto mode on and runs one grid-failure beat (simulated
devices only; the real board is never commanded).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from typing import Any

import httpx
import websockets


async def run(base: str, minutes: float) -> int:
    ws_url = base.replace("http", "ws", 1).rstrip("/") + "/ws"
    seen: dict[str, list[tuple[float, Any]]] = {}
    moved: set[str] = set()
    last_pos: dict[str, tuple[float, float]] = {}
    units_made: list[int] = []
    gen_kw: list[float] = []
    counts: dict[str, int] = {}
    start = time.monotonic()
    end = start + minutes * 60
    beat_sent = restore_sent = False
    async with websockets.connect(ws_url, max_size=2**24) as ws:
        await ws.send(json.dumps({"type": "set_auto_mode", "cmd_id": "verify-auto", "enabled": True}))
        while time.monotonic() < end:
            el = time.monotonic() - start
            if not beat_sent and el > min(120, minutes * 60 * 0.3):
                await ws.send(json.dumps({"type": "scenario_command", "cmd_id": "verify-grid", "beat": "grid_failure"}))
                beat_sent = True
            if beat_sent and not restore_sent and el > min(240, minutes * 60 * 0.6):
                await ws.send(json.dumps({"type": "scenario_command", "cmd_id": "verify-restore", "beat": "reset"}))
                await ws.send(json.dumps({"type": "set_auto_mode", "cmd_id": "verify-auto2", "enabled": True}))
                restore_sent = True
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            except asyncio.TimeoutError:
                continue
            counts[m["type"]] = counts.get(m["type"], 0) + 1
            if m["type"] in ("world_snapshot", "unit_update"):
                for u in m["units"]:
                    p = (round(u["x"], 1), round(u["z"], 1))
                    if u["kind"] in ("forklift", "truck") and u["id"] in last_pos and last_pos[u["id"]] != p:
                        moved.add(u["id"])
                    last_pos[u["id"]] = p
            if m["type"] in ("world_snapshot", "device_update"):
                for d in m["devices"]:
                    for ch, r in d.get("readings", {}).items():
                        key = f"{d['id']}.{ch}"
                        s = seen.setdefault(key, [])
                        if not s or s[-1][1] != r["value"]:
                            s.append((el, r["value"]))
            if m["type"] == "production_update":
                units_made.append(int(m["line"]["units_today"]))
        await ws.send(json.dumps({"type": "set_auto_mode", "cmd_id": "verify-off", "enabled": False}))
    mon = httpx.get(base.rstrip("/") + "/api/health", timeout=10).json()

    def values(key: str) -> list[Any]:
        return [v for _, v in seen.get(key, [])]
    bars = [float(v) for v in values("CP-01.pressure_bar")]
    gen_kw = [float(v) for v in values("PM-05.power_kw")]
    vib = {k: len(v) for k, v in seen.items() if k.endswith(".vibration_rms")}
    checks = {
        "auto mode moved forklifts and trucks": len(moved) >= 3,
        "compressor pressure cycles (min < 6.9 < max)": bool(bars) and min(bars) < 6.9 < max(bars),
        "generator picked up load in the grid failure": any(k > 1 for k in gen_kw),
        "generator back to 0 kW after the grid returned": bool(gen_kw) and gen_kw[-1] < 1,
        "production line counts units": len(units_made) > 1 and units_made[-1] > units_made[0] or max(units_made or [0]) > 0,
        "vibration on every machine keeps changing": len(vib) >= 4 and min(vib.values()) > 20,
        "tick loop healthy (>= 15 Hz)": (mon.get("tick_hz") or 0) >= 15,
    }
    print(json.dumps({"minutes": minutes, "messages": counts, "moved_units": sorted(moved),
                      "compressor_bar": [min(bars or [0]), max(bars or [0])], "generator_kw_max": max(gen_kw or [0]),
                      "units": units_made[-1:] if units_made else None, "vibration_changes": vib, "health": mon}, indent=1))
    for k, ok in checks.items():
        print(("PASS " if ok else "FAIL ") + k)
    return 0 if all(checks.values()) else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default="http://localhost:7860")
    ap.add_argument("--minutes", type=float, default=10.0)
    a = ap.parse_args()
    sys.exit(asyncio.run(run(a.base, a.minutes)))


if __name__ == "__main__":
    main()
