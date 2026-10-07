#!/usr/bin/env bash
# Run the TwinDock backend (FastAPI + MQTT bridge) on port 8000.
# Env: TWINDOCK_MQTT_HOST (default 127.0.0.1), TWINDOCK_MQTT_PORT (1883), TWINDOCK_MQTT=0 to run without a broker.
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/uvicorn twindock.main:app --app-dir backend --host 0.0.0.0 --port 8000 "$@"
