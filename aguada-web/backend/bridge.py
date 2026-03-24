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


FLAG_SENSOR_ERROR = 1 << 2


def _process_message(raw: dict) -> Optional[dict]:
    """Valida e enriquece uma mensagem do gateway. Retorna dict pronto para DB ou None."""
    try:
        # Só processa pacotes SENSOR
        if raw.get("type") != "SENSOR":
            return None

        node_id = raw.get("node_id", "").lower()
        sensor_id = int(raw.get("sensor_id", 0))
        distance_cm = raw.get("distance_cm")
        rssi = raw.get("rssi")
        vbat_raw = raw.get("vbat")
        seq = raw.get("seq", 0)
        # Timestamp sempre pelo servidor — gateway e nós não têm RTC confiável.
        ts = int(time.time())
        vbat = vbat_raw / 10.0 if vbat_raw is not None else None

        # Descarta leituras com erro de sensor
        flags = raw.get("flags", 0)
        if flags & FLAG_SENSOR_ERROR:
            logger.warning("FLAG_SENSOR_ERROR em node_id=%s sensor=%d — descartado", node_id, sensor_id)
            return None

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
            "out_of_range": calc["out_of_range"],
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
        allow_sim = os.getenv("BRIDGE_ALLOW_SIMULATION", "0").strip().lower() in {"1", "true", "yes", "on"}
        while True:
            try:
                import serial
                ser = serial.Serial(serial_port, 115200, timeout=2)
                logger.info("Serial aberto: %s", serial_port)
                self._send_settime(ser)
                self._read_loop(ser)
            except Exception as e:
                if allow_sim:
                    logger.warning("Serial indisponível (%s) — modo simulação habilitado por BRIDGE_ALLOW_SIMULATION", e)
                    self._sim_loop()
                    return
                logger.error(
                    "Serial indisponível (%s). Aguardando sensor real (simulação desativada). Nova tentativa em 5s.",
                    e,
                )
                time.sleep(5)

    def _send_settime(self, ser) -> None:
        """Sincroniza o timestamp do gateway com o servidor."""
        ts = int(time.time())
        cmd = json.dumps({"cmd": "SETTIME", "ts": ts}) + "\n"
        ser.write(cmd.encode())
        logger.info("SETTIME enviado ao gateway: ts=%d", ts)

    def _read_loop(self, ser) -> None:
        while True:
            try:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                logger.debug("Serial RX: %r", line)
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("JSON inválido do gateway: %r", line[:120])
                    continue
                # Reenvia SETTIME quando gateway reinicia
                if raw.get("type") == "GATEWAY_READY":
                    logger.info("GATEWAY_READY recebido — reenviando SETTIME")
                    self._send_settime(ser)
                self._handle(raw)
            except Exception as e:
                msg = str(e).lower()
                serial_drop_markers = (
                    "device reports readiness to read but returned no data",
                    "input/output error",
                    "device disconnected",
                    "port is closed",
                    "bad file descriptor",
                )
                if any(m in msg for m in serial_drop_markers):
                    logger.error("Serial desconectada durante leitura (%s). Reconectando...", e)
                    try:
                        ser.close()
                    except Exception:
                        pass
                    raise
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
                    "type": "SENSOR",
                    "node_id": info["node_id"],
                    "sensor_id": info["sensor_id"],
                    "distance_cm": round(distance, 1),
                    "rssi": random.randint(-80, -50),
                    "vbat": random.choice([32, 33, 34]),
                    "flags": 0,
                    "seq": random.randint(0, 65535),
                    "ts": ts,
                }
                self._handle(raw)
            time.sleep(30)

    def _handle(self, raw: dict) -> None:
        msg_type = raw.get("type", "?")
        if msg_type == "SENSOR":
            logger.info(
                "SENSOR recebido: node=%s sensor=%s dist=%s rssi=%s ts=%s",
                raw.get("node_id"), raw.get("sensor_id"),
                raw.get("distance_cm"), raw.get("rssi"), raw.get("ts"),
            )
        elif msg_type not in ("GATEWAY_READY", "GATEWAY_STATUS", "CMD_ACK"):
            logger.debug("Mensagem tipo=%s: %s", msg_type, raw)
        record = _process_message(raw)
        if record is None:
            if msg_type == "SENSOR":
                logger.warning(
                    "SENSOR descartado por _process_message: node=%s sensor=%s flags=%s",
                    raw.get("node_id"), raw.get("sensor_id"), raw.get("flags"),
                )
            return
        asyncio.run_coroutine_threadsafe(self._save_and_notify(record), self._loop)

    async def _save_and_notify(self, record: dict) -> None:
        import aiosqlite
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                await insert_reading(conn, record)
                await upsert_state(conn, record)
            logger.info(
                "Gravado: alias=%s dist=%.1f level=%.1f ts=%d",
                record["alias"], record.get("distance_cm") or 0,
                record.get("level_cm") or 0, record["ts"],
            )
        except Exception as e:
            logger.error("Erro ao gravar no DB: %s — registro: %s", e, record)
            return
        self.notify_cb(record)
        self._publish_mqtt(record)
