#!/usr/bin/env bash
set -u

VENV_PY="/home/luc/Dev/espnow-ha/.venv/bin/python"
BRIDGE="/home/luc/Dev/espnow-ha/tools/bridge.py"
BROKER="/home/luc/Dev/espnow-ha/tools/mqtt_broker.py"
GATEWAY_SERIAL="80:F1:B2:50:31:34"
SERIAL_PORT=""
REMOTE_HOST="192.168.0.177"
REMOTE_PORT="1883"
MQTT_USER="aguada"
MQTT_PASS="aguadagtw01"

BRIDGE_LOG="/tmp/bridge_debug.log"
BROKER_LOG="/tmp/local_mqtt.log"
SWITCH_LOG="/tmp/bridge_autoswitch.log"

detect_gateway_port() {
  # 1) First, try matching by known USB serial (most reliable)
  for p in /dev/ttyACM* /dev/ttyUSB*; do
    [[ -e "$p" ]] || continue
    serial=$(udevadm info "$p" 2>/dev/null | grep ID_SERIAL_SHORT | cut -d= -f2 || true)
    if [[ "$serial" == "$GATEWAY_SERIAL" ]]; then
      echo "$p"
      return 0
    fi
  done

  # 2) Fallback: pick first available ACM/USB device
  for p in /dev/ttyACM* /dev/ttyUSB*; do
    [[ -e "$p" ]] || continue
    echo "$p"
    return 0
  done

  echo ""
  return 1
}

is_remote_up() {
  python3 - <<PY
import socket
s=socket.socket(); s.settimeout(2)
try:
    s.connect(("$REMOTE_HOST", int($REMOTE_PORT)))
    print("UP")
except Exception:
    print("DOWN")
finally:
    s.close()
PY
}

start_local_broker_if_needed() {
  if ! pgrep -f "mqtt_broker.py --host 127.0.0.1 --port $REMOTE_PORT" >/dev/null 2>&1; then
    nohup "$VENV_PY" "$BROKER" --host 127.0.0.1 --port "$REMOTE_PORT" > "$BROKER_LOG" 2>&1 &
    echo "[$(date '+%F %T')] local broker started pid=$!" >> "$SWITCH_LOG"
  fi
}

stop_local_broker_if_running() {
  if pgrep -f "mqtt_broker.py --host 127.0.0.1 --port $REMOTE_PORT" >/dev/null 2>&1; then
    pkill -f "mqtt_broker.py --host 127.0.0.1 --port $REMOTE_PORT" || true
    echo "[$(date '+%F %T')] local broker stopped" >> "$SWITCH_LOG"
  fi
}

ensure_bridge_target() {
  local target_host="$1"

  if [[ -z "$SERIAL_PORT" ]] || [[ ! -e "$SERIAL_PORT" ]]; then
    SERIAL_PORT="$(detect_gateway_port)"
    if [[ -z "$SERIAL_PORT" ]]; then
      echo "[$(date '+%F %T')] gateway serial not found; will retry" >> "$SWITCH_LOG"
      return 0
    fi
    echo "[$(date '+%F %T')] gateway port detected: $SERIAL_PORT" >> "$SWITCH_LOG"
  fi

  if pgrep -f "bridge.py --port $SERIAL_PORT --mqtt $target_host --mqtt-port $REMOTE_PORT" >/dev/null 2>&1; then
    return 0
  fi

  pkill -f "python.*bridge.py --port $SERIAL_PORT" || true
  sleep 1

  nohup "$VENV_PY" "$BRIDGE" \
    --port "$SERIAL_PORT" \
    --mqtt "$target_host" \
    --mqtt-port "$REMOTE_PORT" \
    --mqtt-user "$MQTT_USER" \
    --mqtt-password "$MQTT_PASS" \
    --debug > "$BRIDGE_LOG" 2>&1 &

  echo "[$(date '+%F %T')] bridge started pid=$! target=$target_host" >> "$SWITCH_LOG"
}

mkdir -p /tmp

SERIAL_PORT="$(detect_gateway_port)"
if [[ -n "$SERIAL_PORT" ]]; then
  echo "[$(date '+%F %T')] initial gateway port: $SERIAL_PORT" >> "$SWITCH_LOG"
else
  echo "[$(date '+%F %T')] initial gateway port: not found" >> "$SWITCH_LOG"
fi

echo "[$(date '+%F %T')] autoswitch supervisor started" >> "$SWITCH_LOG"

while true; do
  state="$(is_remote_up)"
  if [[ "$state" == "UP" ]]; then
    ensure_bridge_target "$REMOTE_HOST"
    stop_local_broker_if_running
  else
    start_local_broker_if_needed
    ensure_bridge_target "127.0.0.1"
  fi

  sleep 20
done
