from contextlib import asynccontextmanager
from fastapi import FastAPI

from client.mcp_client import load_all_tools_async
import client.mcp_client as mcp_client
from agent.graph import build_graph
from fasapi.routes.chat_route import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load MCP tools and build the graph once at startup."""
    print("Loading MCP tools...")
    tools = await load_all_tools_async()

    # Populate the shared ALL_TOOLS list so agent_node picks them up lazily
    mcp_client.ALL_TOOLS.extend(tools)

    # Also store compiled graph on app.state
    app.state.graph = build_graph(tools)
    print(f"Graph ready with {len(tools)} tools.")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Major1 Agent API",
    description="LangGraph agent with HITL support over FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/chat", tags=["Chat"])
