import asyncio
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_SERVERS = {
    "gmail": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "server.gmail_server"],
    },
    "github": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "server.github_server"],
    },
}


async def load_all_tools_async():
    """Async version - safe to call from a running event loop (e.g. FastAPI lifespan)."""
    client = MultiServerMCPClient(MCP_SERVERS)
    return await client.get_tools()


# def load_all_tools():
#     """Sync version - only safe to call before any event loop is running (e.g. main.py)."""
#     client = MultiServerMCPClient(MCP_SERVERS)
#     return asyncio.run(client.get_tools())


# Populated at startup by FastAPI lifespan (or directly by main.py via load_all_tools)
ALL_TOOLS: list = []