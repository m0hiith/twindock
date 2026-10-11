#!/usr/bin/env python3
"""Reproduce why the hosted (serverless) deploy shows no factory data while localhost works.

    .venv/bin/python scripts/repro_serverless.py

Runs the backend the way a production deploy does (one worker, no broker, embedded simulator) in three ways:

1. long-running: one process kept alive, sampled after 20 s (what localhost and a container do);
2. cold start per request: a fresh process for every request (what a serverless platform may do);
3. frozen between requests: one process paused with SIGSTOP between requests (what a serverless
   platform does to an idle instance: no CPU, so the tick loop and the simulator don't run).

Prints, for each, how many SIM devices are online and whether the compressor, generator, line and
machines have data. See docs/deploy_diagnosis.md for the explanation.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "bin" / "python"
ENV = {**os.environ, "TWINDOCK_MQTT": "0", "TWINDOCK_SIM": "embedded"}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def start() -> tuple[subprocess.Popen[bytes], str]:
    port = free_port()
    p = subprocess.Popen([str(PY), "-m", "uvicorn", "twindock.main:app", "--app-dir", "backend", "--host", "127.0.0.1",
                          "--port", str(port), "--workers", "1", "--log-level", "warning"],
                         cwd=ROOT, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            httpx.get(base + "/api/health", timeout=0.5)
            return p, base
        except httpx.HTTPError:
            time.sleep(0.1)
    raise RuntimeError("backend did not start")


def sample(base: str) -> dict[str, Any]:
    snap = httpx.get(base + "/api/snapshot", timeout=5).json()
    mon = httpx.get(base + "/api/monitor", timeout=5).json()
    devs = {d["id"]: d for d in snap["devices"]}
    sim = [d for d in devs.values() if d["source"] == "sim"]
    cp = devs.get("CP-01", {}).get("readings", {}).get("pressure_bar")
    machines = [u for u in snap["units"] if u["kind"] == "machine"]
    return {"sim_online": sum(d["status"] == "online" for d in sim), "sim_total": len(sim),
            "compressor_bar": cp["value"] if cp and devs["CP-01"]["status"] == "online" else None,
            "generator_state": mon["power"].get("generator_state"),
            "machines_with_data": sum(u["state"] != "no_data" for u in machines), "machines": len(machines)}


def stop(p: subprocess.Popen[bytes]) -> None:
    p.send_signal(signal.SIGCONT)
    p.terminate()
    p.wait(5)


def main() -> None:
    print("1. long-running process (localhost / container)")
    p, base = start()
    time.sleep(20)
    print("   after 20 s:", json.dumps(sample(base)))
    stop(p)

    print("2. cold start per request (a fresh instance answers each request)")
    for i in range(3):
        p, base = start()
        print(f"   request {i + 1}:", json.dumps(sample(base)))
        stop(p)

    print("3. one instance, frozen between requests (no CPU while idle)")
    p, base = start()
    time.sleep(3)
    print("   request 1 (3 s after start):", json.dumps(sample(base)))
    p.send_signal(signal.SIGSTOP)
    time.sleep(30)
    p.send_signal(signal.SIGCONT)
    print("   request 2 (after 30 s frozen):", json.dumps(sample(base)))
    stop(p)


if __name__ == "__main__":
    sys.exit(main())
