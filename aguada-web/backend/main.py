# backend/main.py
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import FileResponse

from .bridge import Bridge
from .db import init_db, get_all_states, get_history, get_readings_for_date
from .calc import calc_consumption_events, decimate_readings
from .report import generate_daily_report_pdf

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = str(DATA_DIR / "aguada.db")
REPORTS_DIR = DATA_DIR / "reports"


class WSManager:
    def __init__(self):
        self._clients: list[WebSocket] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    def broadcast(self, data: dict):
        """Chamado pela bridge thread — agenda envio no loop asyncio principal."""
        if self._loop is None:
            return
        msg = json.dumps({"type": "reading", "data": data})
        self._loop.call_soon_threadsafe(
            lambda: asyncio.ensure_future(self._send_all(msg), loop=self._loop)
        )

    async def _send_all(self, msg: str):
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_snapshot(self, ws: WebSocket):
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            states = await get_all_states(conn)
        await ws.send_text(json.dumps({"type": "snapshot", "data": states}))


ws_manager = WSManager()
bridge: Optional[Bridge] = None
scheduler: Optional[AsyncIOScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bridge, scheduler
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as conn:
        await init_db(conn)

    loop = asyncio.get_running_loop()
    ws_manager.set_loop(loop)

    bridge = Bridge(db_path=DB_PATH, notify_cb=ws_manager.broadcast)
    bridge.start(loop)

    scheduler = AsyncIOScheduler(timezone=os.getenv("TZ", "America/Sao_Paulo"))
    scheduler.add_job(_daily_report_job, "cron", hour=6, minute=0)
    scheduler.start()

    yield

    scheduler.shutdown()


async def _daily_report_job():
    import datetime
    date_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    out_path = REPORTS_DIR / f"{date_str}.pdf"
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await generate_daily_report_pdf(conn, date_str, str(out_path))
    logger.info("Relatório diário gerado: %s", out_path)


app = FastAPI(title="Aguada Web", lifespan=lifespan)


@app.get("/api/reservoirs")
async def get_reservoirs():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        return await get_all_states(conn)


@app.get("/api/history/{alias}")
async def get_history_route(alias: str, period: str = "24h"):
    periods = {"24h": 86400, "7d": 7 * 86400, "30d": 30 * 86400}
    seconds = periods.get(period)
    if seconds is None:
        raise HTTPException(400, "period deve ser 24h, 7d ou 30d")
    since = int(time.time()) - seconds
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await get_history(conn, alias=alias.upper(), since_ts=since)
    return decimate_readings(rows, max_points=500)


@app.get("/api/consumption")
async def get_consumption(
    alias: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    if alias is None or date is None:
        raise HTTPException(400, "alias e date são obrigatórios")
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        readings = await get_readings_for_date(conn, alias=alias.upper(), date_str=date)
    if not readings:
        return {"date": date, "alias": alias.upper(), "summary": {}, "events": []}

    events = calc_consumption_events(readings, date=date)
    consumed = sum(abs(e["delta_l"]) for e in events if e["type"] == "consumption")
    supplied = sum(e["delta_l"] for e in events if e["type"] == "supply")
    return {
        "date": date,
        "alias": alias.upper(),
        "summary": {
            "consumed_l": round(consumed, 1),
            "supplied_l": round(supplied, 1),
            "balance_l": round(supplied - consumed, 1),
        },
        "events": events,
    }


@app.get("/api/report/daily")
async def get_report_data(date: str = Query(...)):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        states = await get_all_states(conn)
        report_data = []
        for s in states:
            alias = s["alias"]
            readings = await get_readings_for_date(conn, alias=alias, date_str=date)
            events = calc_consumption_events(readings, date=date) if readings else []
            report_data.append({**s, "events": events, "readings_count": len(readings)})
    return {"date": date, "reservoirs": report_data}


@app.get("/api/report/daily.pdf")
async def get_report_pdf(date: str = Query(...)):
    out_path = REPORTS_DIR / f"{date}.pdf"
    if not out_path.exists():
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            await generate_daily_report_pdf(conn, date, str(out_path))
    if not out_path.exists():
        raise HTTPException(404, "Relatório não disponível para esta data")
    return FileResponse(str(out_path), media_type="application/pdf",
                        filename=f"aguada-{date}.pdf")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws_manager.send_snapshot(ws)
    ws_manager._clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
