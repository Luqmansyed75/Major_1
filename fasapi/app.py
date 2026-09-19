import asyncio
import selectors
import sys

from dotenv import load_dotenv
load_dotenv()  # Must be first — loads env vars before any LangChain import

# psycopg async requires SelectorEventLoop on Windows
# (default ProactorEventLoop is incompatible with psycopg)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.DefaultEventLoopPolicy()
    )
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from client.mcp_client import load_all_tools_async
import client.mcp_client as mcp_client
from agent.graph import build_graph
from fasapi.routes.chat_route import router
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load MCP tools and build the LangGraph once at startup."""
    print("Loading MCP tools...")
    tools = await load_all_tools_async()

    # Populate the shared ALL_TOOLS list so agent_node picks them up lazily
    mcp_client.ALL_TOOLS.extend(tools)

    async with AsyncPostgresStore.from_conn_string(DB_URI) as store:
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:

            # Create required PostgreSQL tables
            await store.setup()
            await checkpointer.setup()

            # Build and compile the graph
            # NOTE: checkpointer must be passed BEFORE graph is compiled
            graph = build_graph(
                tools=tools,
                store=store,
                checkpointer=checkpointer,
            )

            # Store graph on app.state so routes access it via request.app.state.graph
            app.state.graph = graph

            print(f"Graph ready with {len(tools)} tools.")
            yield  # ← app serves requests HERE; DB connections stay open
            print("Shutting down...")


app = FastAPI(
    title="Major1 Agent API",
    description=(
        "LangGraph-powered conversational agent with Human-in-the-Loop (HITL) "
        "support.\n\n"
        "## Workflow\n"
        "1. **POST /chat/ask** — send a question, get an answer or a HITL prompt.\n"
        "2. **POST /chat/resume** — approve or reject the HITL action and get "
        "the final answer.\n\n"
        "Use the `thread_id` returned by `/ask` to keep messages in the same "
        "conversation session."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the local UI / Swagger UI to call the API without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/chat", tags=["Chat"])
