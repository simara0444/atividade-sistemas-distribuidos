import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool: asyncpg.pool.Pool | None = None

async def connect_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

async def close_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None

async def fetchrow(query: str, *args):
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)

async def fetch(query: str, *args):
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute(query: str, *args):
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)
