"""
fasapi/db/connection.py
-----------------------
Manages a single shared async psycopg connection pool for the whole app.

Usage in routes:
    async with get_conn() as conn:
        await conn.execute(...)
"""
import os
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool

# Populated once during app lifespan startup (see app.py)
_pool: AsyncConnectionPool | None = None


def get_db_uri() -> str:
    """
    Read DATABASE_URL at call time (not at import time).
    This ensures Render's environment variables are already injected
    by the time this is called during FastAPI startup.

    Cloud providers (Render, Supabase, Neon) may give 'postgres://' —
    psycopg requires 'postgresql://', so we normalise it here.
    """
    raw = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable",
    )
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)
    return raw


# DB_URI is resolved at startup (not import time) — used by app.py for LangGraph
DB_URI: str = ""


async def init_pool() -> AsyncConnectionPool:
    """Create and open the connection pool. Called once at startup."""
    global _pool, DB_URI
    DB_URI = get_db_uri()
    _pool = AsyncConnectionPool(conninfo=DB_URI, open=False)
    await _pool.open()
    return _pool


async def close_pool() -> None:
    """Gracefully close the pool. Called at shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> AsyncConnectionPool:
    """Return the live pool (raises if not yet initialised)."""
    if _pool is None:
        raise RuntimeError("DB pool not initialised — call init_pool() first.")
    return _pool


@asynccontextmanager
async def get_conn():
    """Async context-manager that yields a single connection from the pool."""
    async with get_pool().connection() as conn:
        yield conn
