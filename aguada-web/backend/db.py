# backend/db.py
"""Acesso ao SQLite — schema, inserts, queries. Sem lógica de negócio."""
import time
import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    node_id     TEXT    NOT NULL,
    sensor_id   INTEGER NOT NULL,
    alias       TEXT    NOT NULL,
    distance_cm REAL,
    level_cm    REAL,
    volume_l    REAL,
    pct         REAL,
    rssi        INTEGER,
    vbat        REAL,
    seq         INTEGER
);
CREATE INDEX IF NOT EXISTS idx_readings_ts    ON readings(ts DESC);
CREATE INDEX IF NOT EXISTS idx_readings_alias ON readings(alias, ts DESC);

CREATE TABLE IF NOT EXISTS reservoir_state (
    alias        TEXT PRIMARY KEY,
    node_id      TEXT,
    sensor_id    INTEGER,
    name         TEXT,
    ts           INTEGER,
    level_cm     REAL,
    volume_l     REAL,
    pct          REAL,
    level_max_cm REAL,
    volume_max_l REAL,
    rssi         INTEGER,
    online       INTEGER DEFAULT 1
);
"""

async def init_db(conn: aiosqlite.Connection) -> None:
    await conn.executescript(SCHEMA)
    await conn.commit()
    conn.row_factory = aiosqlite.Row


async def insert_reading(conn: aiosqlite.Connection, r: dict) -> None:
    await conn.execute(
        """INSERT INTO readings
           (ts, node_id, sensor_id, alias, distance_cm, level_cm, volume_l, pct, rssi, vbat, seq)
           VALUES (:ts, :node_id, :sensor_id, :alias, :distance_cm, :level_cm, :volume_l,
                   :pct, :rssi, :vbat, :seq)""",
        r,
    )
    await conn.commit()


async def upsert_state(conn: aiosqlite.Connection, s: dict) -> None:
    await conn.execute(
        """INSERT INTO reservoir_state
           (alias, node_id, sensor_id, name, ts, level_cm, volume_l, pct,
            level_max_cm, volume_max_l, rssi)
           VALUES (:alias, :node_id, :sensor_id, :name, :ts, :level_cm, :volume_l, :pct,
                   :level_max_cm, :volume_max_l, :rssi)
           ON CONFLICT(alias) DO UPDATE SET
               node_id=excluded.node_id, sensor_id=excluded.sensor_id,
               name=excluded.name,
               ts=excluded.ts, level_cm=excluded.level_cm, volume_l=excluded.volume_l,
               pct=excluded.pct, rssi=excluded.rssi,
               level_max_cm=excluded.level_max_cm, volume_max_l=excluded.volume_max_l""",
        s,
    )
    await conn.commit()


async def get_all_states(conn: aiosqlite.Connection) -> list[dict]:
    now = int(time.time())
    async with conn.execute("SELECT * FROM reservoir_state") as cur:
        rows = await cur.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["online"] = (now - (d["ts"] or 0)) < 600
        result.append(d)
    return result


async def get_history(
    conn: aiosqlite.Connection, alias: str, since_ts: int
) -> list[dict]:
    async with conn.execute(
        "SELECT ts, level_cm, volume_l, pct FROM readings WHERE alias=? AND ts>=? ORDER BY ts ASC",
        (alias, since_ts),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_readings_for_date(
    conn: aiosqlite.Connection, alias: str, date_str: str
) -> list[dict]:
    """Retorna todas as leituras de um alias em um dia (YYYY-MM-DD, fuso local do servidor)."""
    import datetime
    day = datetime.date.fromisoformat(date_str)
    ts_start = int(datetime.datetime(day.year, day.month, day.day, 0, 0, 0).timestamp())
    ts_end = ts_start + 86400
    async with conn.execute(
        "SELECT ts, volume_l, level_cm, pct FROM readings WHERE alias=? AND ts>=? AND ts<? ORDER BY ts ASC",
        (alias, ts_start, ts_end),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
