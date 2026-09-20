import asyncio
import selectors
import sys

from dotenv import load_dotenv
load_dotenv()  # Must be first — loads env vars before any LangChain import

# psycopg async requires SelectorEventLoop on Windows
# (default ProactorEventLoop is incompatible with psycopg)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from client.mcp_client import load_all_tools_async
import client.mcp_client as mcp_client
from agent.graph import build_graph

# DB pool + table init
from fasapi.db.connection import init_pool, close_pool
from fasapi.db.init_tables import init_tables


# Routers
from fasapi.routes.chat_route import router as chat_router
from fasapi.routes.auth_route import router as auth_router
from fasapi.routes.thread_route import router as thread_router

from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver




@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup order:
      1. Init shared async DB pool (for auth / thread routes)
      2. Create users + user_threads tables if they don't exist
      3. Load MCP tools
      4. Open LangGraph AsyncPostgresStore + AsyncPostgresSaver
      5. Build + compile the graph
    """
    # ── 1. DB pool ────────────────────────────────────────────────────────────
    pool = await init_pool()
    app.state.pool = pool

    # ── 2. App tables ─────────────────────────────────────────────────────────
    await init_tables(pool)

    # ── 3. MCP tools ──────────────────────────────────────────────────────────
    print("Loading MCP tools...")
    tools = await load_all_tools_async()
    mcp_client.ALL_TOOLS.extend(tools)

    # ── 4 & 5. LangGraph store + checkpointer + graph ─────────────────────────
    # Import DB_URI here — after init_pool() has resolved it from the environment
    import fasapi.db.connection as _db_conn
    _db_uri = _db_conn.DB_URI

    async with AsyncPostgresStore.from_conn_string(_db_uri) as store:
        async with AsyncPostgresSaver.from_conn_string(_db_uri) as checkpointer:
            await store.setup()
            await checkpointer.setup()

            graph = build_graph(
                tools=tools,
                store=store,
                checkpointer=checkpointer,
            )
            app.state.graph = graph

            print(f"Graph ready with {len(tools)} tools.")
            yield  # ← app serves requests HERE; all connections stay open
            print("Shutting down...")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    await close_pool()



app = FastAPI(
    title="Major1 Agent API",
    description=(
        "LangGraph-powered conversational agent with Human-in-the-Loop (HITL) "
        "support and JWT user authentication.\n\n"
        "## Auth Flow\n"
        "1. **POST /auth/register** — create an account, receive a Bearer token.\n"
        "2. **POST /auth/login** — exchange credentials for a Bearer token.\n"
        "3. Click **Authorize** (🔒) in Swagger and paste the token.\n\n"
        "## Conversation Flow\n"
        "1. **POST /threads** — create a thread, get back a `thread_id`.\n"
        "2. **POST /chat/ask** — send a question with that `thread_id`.\n"
        "3. **POST /chat/resume** — approve / reject a HITL action.\n"
        "4. **GET /threads** — list all your past conversations.\n"
        "5. **DELETE /threads/{thread_id}** — remove a conversation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Swagger UI and local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router,   prefix="/auth",    tags=["Auth"])
app.include_router(thread_router, prefix="/threads", tags=["Threads"])
app.include_router(chat_router,   prefix="/chat",    tags=["Chat"])
