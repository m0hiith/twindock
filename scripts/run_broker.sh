#!/usr/bin/env bash
# Run Mosquitto with the TwinDock config. Docker is not required.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p broker/data
if ! command -v mosquitto >/dev/null 2>&1 && [ ! -x /opt/homebrew/sbin/mosquitto ]; then
  echo "mosquitto not found. Install with: brew install mosquitto" >&2
  exit 1
fi
MOSQ="$(command -v mosquitto || echo /opt/homebrew/sbin/mosquitto)"
echo "Broker on port 1883. Board should use one of these laptop IPs:"
ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null || true
exec "$MOSQ" -c broker/mosquitto.conf
