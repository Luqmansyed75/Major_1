import asyncio
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


# ---------------------------------------------------------------------------
# MCP Server Registry
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Tool Discovery
# ---------------------------------------------------------------------------
def load_all_tools():
    """Discovers and returns LangChain tools from all registered MCP servers."""
    client = MultiServerMCPClient(MCP_SERVERS)
    return asyncio.run(client.get_tools())


ALL_TOOLS = load_all_tools()
