"""
fasapi/db/init_tables.py
------------------------
Creates application-level tables on startup (idempotent — safe to run every boot).
LangGraph's own tables (checkpoints, checkpoint_writes, checkpoint_blobs) are
created separately by checkpointer.setup() in app.py.
"""
from psycopg_pool import AsyncConnectionPool


CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    hashed_pw   TEXT        NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_USER_THREADS = """
CREATE TABLE IF NOT EXISTS user_threads (
    thread_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_title VARCHAR(255) DEFAULT 'New Conversation',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_threads_user_id ON user_threads(user_id);
"""

# Stores per-user GitHub PAT and Gmail OAuth token JSON.
# github_token  : GitHub Personal Access Token (plain text).
# gmail_token_json : Full Gmail OAuth token JSON string (contains refresh_token).
# Both are nullable — a NULL value means "not connected".
CREATE_USER_CREDENTIALS = """
CREATE TABLE IF NOT EXISTS user_credentials (
    user_id          UUID        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    github_token     TEXT,
    gmail_token_json TEXT,
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);
"""


async def init_tables(pool: AsyncConnectionPool) -> None:
    """Run CREATE TABLE IF NOT EXISTS for all app tables."""
    async with pool.connection() as conn:
        await conn.execute(CREATE_USERS)
        await conn.execute(CREATE_USER_THREADS)
        await conn.execute(CREATE_INDEX)
        await conn.execute(CREATE_USER_CREDENTIALS)
    print("DB tables verified / created.")
