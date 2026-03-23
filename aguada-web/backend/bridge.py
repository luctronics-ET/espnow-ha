# backend/bridge.py
"""
Bridge serial → SQLite + WebSocket notify.
Roda como thread daemon iniciada pelo FastAPI startup.
"""
import asyncio
import json
import logging
import os
import random
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import yaml

from .calc import calc_level
from .db import insert_reading, upsert_state

logger = logging.getLogger("bridge")

# Carrega reservoirs.yaml uma vez
_yaml_path = Path(__file__).parent / "reservoirs.yaml"
_raw = yaml.safe_load(_yaml_path.read_text())["reservoirs"]

# Índice: (node_id_lower, sensor_id) → dict de parâmetros
RESERVOIR_INDEX: dict[tuple[str, int], dict] = {}
for _node_id, _sensors in _raw.items():
    for _s in _sensors:
        RESERVOIR_INDEX[(_node_id.lower(), _s["sensor_id"])] = _s


def _process_message(raw: dict) -> Optional[dict]:
    """Valida e enriquece uma mensagem do gateway. Retorna dict pronto para DB ou None."""
    try:
        node_id = raw.get("node", "").lower()
        sensor_id = int(raw.get("sensor", 0))
        distance_cm = raw.get("dist")
        rssi = raw.get("rssi")
        vbat_raw = raw.get("vbat")
        seq = raw.get("seq", 0)
        ts = raw.get("ts") or int(time.time())
        vbat = vbat_raw / 10.0 if vbat_raw is not None else None

        params = RESERVOIR_INDEX.get((node_id, sensor_id))
        if params is None:
            logger.warning("node_id=%s sensor=%d não encontrado no reservoirs.yaml", node_id, sensor_id)
            return None

        calc = calc_level(
            distance_cm=distance_cm,
            level_max_cm=params["level_max_cm"],
            sensor_offset_cm=params["sensor_offset_cm"],
            volume_max_l=params["volume_max_l"],
        )

        return {
            "ts": ts,
            "node_id": node_id,
            "sensor_id": sensor_id,
            "alias": params["alias"],
            "distance_cm": distance_cm,
            "level_cm": calc["level_cm"],
            "volume_l": calc["volume_l"],
            "pct": calc["pct"],
            "rssi": rssi,
            "vbat": vbat,
            "seq": seq,
            "name": params["name"],
            "level_max_cm": params["level_max_cm"],
            "volume_max_l": params["volume_max_l"],
        }
    except Exception as e:
        logger.error("Erro ao processar mensagem: %s — %s", raw, e)
        return None


class Bridge:
    def __init__(self, db_path: str, notify_cb: Callable[[dict], None]):
        self.db_path = db_path
        self.notify_cb = notify_cb
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._mqtt_client = None
        self._init_mqtt()

    def _init_mqtt(self) -> None:
        host = os.getenv("MQTT_HOST", "")
        if not host:
            return
        import paho.mqtt.client as mqtt
        self._mqtt_client = mqtt.Client()
        user = os.getenv("MQTT_USER", "")
        pwd = os.getenv("MQTT_PASS", "")
        if user:
            self._mqtt_client.username_pw_set(user, pwd)
        port = int(os.getenv("MQTT_PORT", "1883"))
        self._mqtt_client.connect_async(host, port)
        self._mqtt_client.loop_start()
        logger.info("MQTT configurado: %s:%d", host, port)

    def _publish_mqtt(self, record: dict) -> None:
        if not self._mqtt_client:
            return
        alias = record["alias"]
        node_id = record["node_id"]
        sensor_id = record["sensor_id"]
        payload = json.dumps({
            "alias": alias,
            "distance_cm": record.get("distance_cm"),
            "level_cm": record.get("level_cm"),
            "pct": record.get("pct"),
            "volume_l": record.get("volume_l"),
            "rssi": record.get("rssi"),
            "vbat": record.get("vbat"),
            "seq": record.get("seq"),
            "ts": record.get("ts"),
        })
        topic = f"aguada/{node_id}/{sensor_id}/state"
        try:
            self._mqtt_client.publish(topic, payload, retain=True)
        except Exception as e:
            logger.warning("MQTT publish error: %s", e)

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        serial_port = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
        self._thread = threading.Thread(
            target=self._run, args=(serial_port,), daemon=True, name="bridge"
        )
        self._thread.start()
        logger.info("Bridge iniciado (porta=%s)", serial_port)

    def _run(self, serial_port: str) -> None:
        try:
            import serial
            ser = serial.Serial(serial_port, 115200, timeout=2)
            logger.info("Serial aberto: %s", serial_port)
            self._read_loop(ser)
        except Exception as e:
            logger.warning("Serial indisponível (%s) — modo simulação", e)
            self._sim_loop()

    def _read_loop(self, ser) -> None:
        while True:
            try:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                raw = json.loads(line)
                self._handle(raw)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error("Erro no read_loop: %s", e)
                time.sleep(1)

    def _sim_loop(self) -> None:
        """Gera leituras sintéticas para todos os reservatórios a cada 30s."""
        logger.info("Modo simulação ativo")
        # Estado simulado por alias
        aliases_params = {}
        for (node_id, sensor_id), params in RESERVOIR_INDEX.items():
            alias = params["alias"]
            aliases_params[alias] = {"node_id": node_id, "sensor_id": sensor_id, "params": params}

        state = {alias: 60.0 for alias in aliases_params}

        while True:
            ts = int(time.time())
            for alias, info in aliases_params.items():
                params = info["params"]
                state[alias] = max(5.0, min(100.0, state[alias] + random.uniform(-2, 1)))
                pct = state[alias]
                level = pct / 100 * params["level_max_cm"]
                distance = params["level_max_cm"] - level + params["sensor_offset_cm"]
                raw = {
                    "node": info["node_id"],
                    "sensor": info["sensor_id"],
                    "dist": round(distance, 1),
                    "rssi": random.randint(-80, -50),
                    "vbat": random.choice([32, 33, 34]),
                    "seq": random.randint(0, 65535),
                    "ts": ts,
                }
                self._handle(raw)
            time.sleep(30)

    def _handle(self, raw: dict) -> None:
        record = _process_message(raw)
        if record is None:
            return
        asyncio.run_coroutine_threadsafe(self._save_and_notify(record), self._loop)

    async def _save_and_notify(self, record: dict) -> None:
        import aiosqlite
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await insert_reading(conn, record)
            await upsert_state(conn, record)
        self.notify_cb(record)
        self._publish_mqtt(record)
