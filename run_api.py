"""
run_api.py
----------
Entry point for running the FastAPI server locally on Windows.

On Windows, psycopg async requires SelectorEventLoop.
The event loop policy MUST be set BEFORE uvicorn starts its own loop.
This script does that correctly, then hands off to uvicorn.
"""
import sys
import asyncio
import selectors

# ── Fix for Windows: set SelectorEventLoop BEFORE uvicorn starts ──────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "fasapi.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="asyncio",   # force asyncio (SelectorEventLoop on Windows)
    )
