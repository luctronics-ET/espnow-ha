# tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
import aiosqlite
from backend.db import init_db

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    async with aiosqlite.connect(db_path) as conn:
        await init_db(conn)
        yield conn
