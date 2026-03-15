#!/usr/bin/env python3
"""
Aguada Bridge v3.2
Reads JSON from gateway USB serial → calculates level/volume → publishes MQTT → HA Discovery.

Usage:
    python bridge.py [--port /dev/ttyACM0] [--baud 115200] [--mqtt localhost] [--mqtt-port 1883]
                     [--config reservoirs.yaml] [--offline-timeout 300]
"""

import argparse
import json
import logging
import sys
import time
import threading
from pathlib import Path

import serial
import paho.mqtt.client as mqtt
import yaml

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bridge")

# ── Config ────────────────────────────────────────────────────────────────────

def load_reservoir_config(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    # Index: (node_id_str, sensor_id_int) → config dict
    index = {}
    for node_id_str, sensors in data.get("reservoirs", {}).items():
        for s in sensors:
            key = (node_id_str.upper(), int(s["sensor_id"]))
            index[key] = s
    return index

# ── Calculations ──────────────────────────────────────────────────────────────

def calculate(distance_cm: int, cfg: dict) -> dict:
    level_max_cm     = cfg["level_max_cm"]
    volume_max_L     = cfg["volume_max_L"]
    sensor_offset_cm = cfg["sensor_offset_cm"]

    level_cm = level_max_cm - (distance_cm - sensor_offset_cm)
    level_cm = max(0, min(level_cm, level_max_cm))

    pct      = round((level_cm / level_max_cm) * 100, 1)
    volume_L = round((level_cm / level_max_cm) * volume_max_L)

    return {"level_cm": level_cm, "pct": pct, "volume_L": volume_L}

# ── MQTT helpers ──────────────────────────────────────────────────────────────

def mqtt_topic_state(node_id: str, sensor_id: int) -> str:
    return f"aguada/{node_id}/{sensor_id}/state"

def mqtt_topic_status(node_id: str) -> str:
    return f"aguada/{node_id}/status"

def mqtt_topic_balance(node_id: str, sensor_id: int) -> str:
    return f"aguada/{node_id}/{sensor_id}/balance"

def publish_discovery(client: mqtt.Client, node_id: str, sensor_id: int, cfg: dict):
    """Publish HA MQTT Discovery config for all entities of a sensor."""
    alias    = cfg.get("alias", f"{node_id}_{sensor_id}").lower()
    name_pfx = cfg.get("name", alias)
    uid_pfx  = f"aguada_{alias}"
    dev      = {"name": cfg.get("alias", alias), "identifiers": [f"aguada_{alias}"], "manufacturer": "Aguada"}
    state_tp = mqtt_topic_state(node_id, sensor_id)
    avail_tp = mqtt_topic_status(node_id)

    entities = [
        {
            "name": f"{name_pfx} - Nível",
            "uid":  f"{uid_pfx}_nivel",
            "oid":  f"aguada_{alias}_nivel",
            "vt":   "{{ value_json.level_cm }}",
            "uom":  "cm",
            "dc":   "distance",
            "icon": "mdi:water-level",
        },
        {
            "name": f"{name_pfx} - Volume %",
            "uid":  f"{uid_pfx}_pct",
            "oid":  f"aguada_{alias}_pct",
            "vt":   "{{ value_json.pct }}",
            "uom":  "%",
            "dc":   None,
            "icon": "mdi:percent",
        },
        {
            "name": f"{name_pfx} - Volume",
            "uid":  f"{uid_pfx}_volume",
            "oid":  f"aguada_{alias}_volume",
            "vt":   "{{ value_json.volume_L }}",
            "uom":  "L",
            "dc":   None,
            "icon": "mdi:water",
        },
        {
            "name": f"{name_pfx} - Distância",
            "uid":  f"{uid_pfx}_distancia",
            "oid":  f"aguada_{alias}_distancia",
            "vt":   "{{ value_json.distance_cm }}",
            "uom":  "cm",
            "dc":   "distance",
            "icon": "mdi:ruler",
        },
        {
            "name": f"{name_pfx} - RSSI",
            "uid":  f"{uid_pfx}_rssi",
            "oid":  f"aguada_{alias}_rssi",
            "vt":   "{{ value_json.rssi }}",
            "uom":  "dBm",
            "dc":   "signal_strength",
            "icon": "mdi:wifi",
        },
    ]

    for e in entities:
        payload = {
            "name":                e["name"],
            "unique_id":           e["uid"],
            "default_entity_id":   f"sensor.{e['oid']}",
            "state_topic":         state_tp,
            "value_template":      e["vt"],
            "unit_of_measurement": e["uom"],
            "device":              dev,
            "availability_topic":       avail_tp,
            "payload_available":        "online",
            "payload_not_available":    "offline",
        }
        if e["dc"]:
            payload["device_class"] = e["dc"]
        if e["icon"]:
            payload["icon"] = e["icon"]

        disc_topic = f"homeassistant/sensor/{e['uid']}/config"
        client.publish(disc_topic, json.dumps(payload), retain=True)
        log.debug("Discovery: %s", disc_topic)

# ── Online/offline tracking ───────────────────────────────────────────────────

class NodeTracker:
    def __init__(self, client: mqtt.Client, offline_timeout_s: int):
        self._client   = client
        self._timeout  = offline_timeout_s
        self._last_seen: dict[str, float] = {}  # node_id → time.time()
        self._online:   set[str]          = set()

    def seen(self, node_id: str):
        was_online = node_id in self._online
        self._last_seen[node_id] = time.time()
        self._online.add(node_id)
        if not was_online:
            self._client.publish(mqtt_topic_status(node_id), "online", retain=True)
            log.info("Node %s → online", node_id)

    def check_timeouts(self):
        now = time.time()
        for node_id, ts in list(self._last_seen.items()):
            if now - ts > self._timeout and node_id in self._online:
                self._online.discard(node_id)
                self._client.publish(mqtt_topic_status(node_id), "offline", retain=True)
                log.warning("Node %s → offline (no data for %ds)", node_id, self._timeout)

# ── Message handlers ──────────────────────────────────────────────────────────

class Bridge:
    def __init__(self, args):
        self.args      = args
        self.reservoirs = load_reservoir_config(args.config)
        log.info("Loaded %d reservoirs from %s", len(self.reservoirs), args.config)

        import socket as _socket, os as _os
        _cid = f"aguada-bridge-{_socket.gethostname()}-{_os.getpid()}"
        self.client  = mqtt.Client(client_id=_cid, clean_session=True,
                                   protocol=mqtt.MQTTv311)
        self.client.will_set("aguada/gateway/status", "offline", retain=True)
        if args.mqtt_user:
            self.client.username_pw_set(args.mqtt_user, args.mqtt_password)
        self.tracker = NodeTracker(self.client, args.offline_timeout)
        self._discovery_sent: set = set()

        # Subscribe to command topics
        self.client.on_connect    = self._on_mqtt_connect
        self.client.on_message    = self._on_mqtt_message
        self.client.on_disconnect = self._on_mqtt_disconnect

        self._serial: serial.Serial | None = None
        self._serial_lock = threading.Lock()

    # ── MQTT ─────────────────────────────────────────────────────────────────

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("MQTT connected")
            client.publish("aguada/gateway/status", "online", retain=True)
            client.subscribe("aguada/cmd/#")

            # Re-publish HA Discovery on every (re)connect to survive broker
            # restarts/retained cleanup without requiring node reboot (HELLO).
            for (node_id, sensor_id), cfg in self.reservoirs.items():
                publish_discovery(client, node_id, sensor_id, cfg)
                self._discovery_sent.add((node_id, sensor_id))
        else:
            log.error("MQTT connect failed rc=%d", rc)

    def _on_mqtt_disconnect(self, client, userdata, rc):
        log.warning("MQTT disconnected rc=%d, will reconnect", rc)

    def _on_mqtt_message(self, client, userdata, msg):
        """Commands from HA/server → forward to gateway via serial."""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload)
        except Exception:
            return

        if topic == "aguada/cmd/restart":
            self._serial_write(json.dumps({"cmd": "RESTART", "node_id": payload.get("node_id")}))
        elif topic == "aguada/cmd/config":
            self._serial_write(json.dumps({**payload, "cmd": "CONFIG"}))
        elif topic == "aguada/cmd/ota":
            log.warning("OTA via MQTT not yet implemented")

    def _serial_write(self, line: str):
        with self._serial_lock:
            if self._serial and self._serial.is_open:
                self._serial.write((line + "\n").encode())
                log.debug("→ serial: %s", line)

    # ── Message processing ────────────────────────────────────────────────────

    def _handle_sensor(self, msg: dict):
        node_id   = msg["node_id"].upper()
        sensor_id = int(msg["sensor_id"])
        key       = (node_id, sensor_id)

        self.tracker.seen(node_id)

        cfg = self.reservoirs.get(key)
        if not cfg:
            log.debug("No reservoir config for %s sensor %d", node_id, sensor_id)
            return

        distance_cm = msg.get("distance_cm", -1)
        if distance_cm < 0:
            log.warning("Sensor error: %s/%d", node_id, sensor_id)
            return

        calcs = calculate(distance_cm, cfg)

        payload = {
            "alias":       cfg.get("alias", ""),
            "distance_cm": distance_cm,
            "level_cm":    calcs["level_cm"],
            "pct":         calcs["pct"],
            "volume_L":    calcs["volume_L"],
            "rssi":        msg.get("rssi", 0),
            "vbat":        round(msg.get("vbat", -1) / 10.0, 1) if msg.get("vbat", -1) != -1 else None,
            "seq":         msg.get("seq", 0),
            "ts":          msg.get("ts", int(time.time())),
        }

        self.client.publish(mqtt_topic_state(node_id, sensor_id), json.dumps(payload), retain=True)
        log.info("%-6s dist=%3dcm  level=%3dcm  pct=%5.1f%%  vol=%dL",
                 cfg.get("alias", key), distance_cm, calcs["level_cm"],
                 calcs["pct"], calcs["volume_L"])

    def _handle_heartbeat(self, msg: dict):
        node_id = msg["node_id"].upper()
        sensor_id = int(msg.get("sensor_id", 0))
        self.tracker.seen(node_id)
        log.debug("HEARTBEAT %s/%d seq=%s dist=%s", node_id, sensor_id, 
                  msg.get("seq"), msg.get("distance_cm"))
        
        # Se heartbeat inclui distância, atualizar estado (mantém HA atualizado)
        if "distance_cm" in msg and sensor_id > 0:
            distance_cm = msg["distance_cm"]
            if distance_cm > 0:  # Se distância válida
                key = (node_id, sensor_id)
                cfg = self.reservoirs.get(key)
                if cfg:
                    calcs = calculate(distance_cm, cfg)
                    payload = {
                        "alias":       cfg.get("alias", ""),
                        "distance_cm": distance_cm,
                        "level_cm":    calcs["level_cm"],
                        "pct":         calcs["pct"],
                        "volume_L":    calcs["volume_L"],
                        "rssi":        msg.get("rssi", 0),
                        "vbat":        None,
                        "seq":         msg.get("seq", 0),
                        "ts":          msg.get("ts", int(time.time())),
                    }
                    self.client.publish(mqtt_topic_state(node_id, sensor_id), 
                                       json.dumps(payload), retain=True)
                    log.debug("HEARTBEAT update: %s dist=%dcm", cfg.get("alias"), distance_cm)

    def _handle_hello(self, msg: dict):
        node_id = msg["node_id"].upper()
        self.tracker.seen(node_id)
        log.info("HELLO %s num_sensors=%s fw=%s",
                 node_id, msg.get("num_sensors"), msg.get("fw_version"))

        # Publish HA Discovery for all sensors of this node
        num = int(msg.get("num_sensors", 0))
        for sid in range(1, num + 1):
            key = (node_id, sid)
            cfg = self.reservoirs.get(key)
            if cfg and key not in self._discovery_sent:
                publish_discovery(self.client, node_id, sid, cfg)
                self._discovery_sent.add(key)

    def _handle_gateway_ready(self, msg: dict):
        log.info("Gateway ready: mac=%s fw=%s", msg.get("mac"), msg.get("fw"))
        # Send current time to gateway
        self._serial_write(json.dumps({"cmd": "SETTIME", "ts": int(time.time())}))

    def dispatch(self, line: str):
        try:
            msg = json.loads(line)
        except Exception:
            log.debug("Non-JSON line: %s", line[:80])
            return

        t = msg.get("type", "")
        if   t == "SENSOR":         self._handle_sensor(msg)
        elif t == "HEARTBEAT":      self._handle_heartbeat(msg)
        elif t == "HELLO":          self._handle_hello(msg)
        elif t == "GATEWAY_READY":  self._handle_gateway_ready(msg)
        else:
            log.debug("Unknown type: %s", t)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        # Connect MQTT
        self.client.connect(self.args.mqtt, self.args.mqtt_port, keepalive=60)
        self.client.loop_start()

        # Open serial (opening ACM resets the ESP32-C3; wait for boot)
        log.info("Opening %s @ %d baud", self.args.port, self.args.baud)
        ser = serial.Serial(self.args.port, self.args.baud, timeout=1)
        self._serial = ser
        log.info("Waiting 3s for gateway boot...")
        time.sleep(3)

        log.info("Bridge running. Ctrl+C to stop.")
        last_timeout_check = time.time()

        try:
            while True:
                try:
                    line = ser.readline().decode(errors="replace").strip()
                except serial.SerialException as e:
                    log.error("Serial error: %s", e)
                    time.sleep(2)
                    continue

                if line:
                    log.debug("← %s", line)
                    self.dispatch(line)

                # Check offline timeouts every 30s
                now = time.time()
                if now - last_timeout_check > 30:
                    self.tracker.check_timeouts()
                    last_timeout_check = now

        except KeyboardInterrupt:
            log.info("Stopping.")
        finally:
            ser.close()
            self.client.loop_stop()
            self.client.disconnect()

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Aguada Bridge v3.2")
    parser.add_argument("--port",            default="/dev/ttyACM0")
    parser.add_argument("--baud",            default=115200, type=int)
    parser.add_argument("--mqtt",            default="localhost")
    parser.add_argument("--mqtt-port",       default=1883, type=int)
    parser.add_argument("--config",          default=str(Path(__file__).parent / "reservoirs.yaml"))
    parser.add_argument("--mqtt-user",       default="")
    parser.add_argument("--mqtt-password",   default="")
    parser.add_argument("--offline-timeout", default=300, type=int,
                        help="Seconds without data before node is marked offline")
    parser.add_argument("--debug",           action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    Bridge(args).run()

if __name__ == "__main__":
    main()
