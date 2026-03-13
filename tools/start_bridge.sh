#!/usr/bin/env bash
# Starts the Aguada bridge connected to the Mosquitto broker at 192.168.0.177.
# Usage: ./start_bridge.sh [--port /dev/ttyACM2] [--debug]

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── MQTT broker ───────────────────────────────────────────────────────────────
MQTT_HOST="192.168.0.177"
MQTT_PORT="1883"
MQTT_USER="aguada"
MQTT_PASS="aguadagtw01"

# ── Detect gateway port (by serial MAC 80:F1:B2:50:31:34) ────────────────────
GATEWAY_PORT=""
for p in /dev/ttyACM*; do
    serial=$(udevadm info "$p" 2>/dev/null | grep ID_SERIAL_SHORT | cut -d= -f2)
    if [[ "$serial" == "80:F1:B2:50:31:34" ]]; then
        GATEWAY_PORT="$p"
        break
    fi
done

if [[ -z "$GATEWAY_PORT" ]]; then
    echo "[warn] Gateway not found by serial, using /dev/ttyACM0"
    GATEWAY_PORT="/dev/ttyACM0"
fi
echo "[start] Gateway on $GATEWAY_PORT"

# ── Parse overrides ───────────────────────────────────────────────────────────
PORT="$GATEWAY_PORT"
EXTRA_ARGS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)     PORT="$2"; shift 2 ;;
        --debug)    EXTRA_ARGS="--debug"; shift ;;
        *)          shift ;;
    esac
done

# ── Start bridge ──────────────────────────────────────────────────────────────
# Kill any stale bridge instances
pkill -f "bridge.py" 2>/dev/null && sleep 1 || true

echo "[start] Connecting to MQTT $MQTT_HOST:$MQTT_PORT as $MQTT_USER"
exec python3 "$SCRIPT_DIR/bridge.py" \
    --port "$PORT" \
    --mqtt "$MQTT_HOST" \
    --mqtt-port "$MQTT_PORT" \
    --mqtt-user "$MQTT_USER" \
    --mqtt-password "$MQTT_PASS" \
    $EXTRA_ARGS
