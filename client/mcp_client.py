import asyncio
import os
import sys
from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _run_mcp_tool(tool_name: str, tool_args: dict) -> str:
    """Executes a tool on the Gmail MCP server over stdio transport."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server.gmail_server"],
        env={**os.environ},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            output = [item.text for item in result.content if hasattr(item, "text")]
            return "\n".join(output) if output else "No response from tool."


def call_mcp_tool_sync(tool_name: str, tool_args: dict) -> str:
    """Synchronous wrapper for MCP tool execution."""
    return asyncio.run(_run_mcp_tool(tool_name, tool_args))


# ---------------------------------------------------------------------------
# LangChain-compatible Tools bridging to Gmail MCP Server
# ---------------------------------------------------------------------------
@tool
def search_emails(query: str, max_results: int = 5) -> str:
    """Search emails in Gmail by keyword, sender, subject, or query syntax (e.g. 'from:mentor', 'project update', 'is:unread')."""
    return call_mcp_tool_sync("search_emails", {"query": query, "max_results": max_results})


@tool
def read_email(message_id: str) -> str:
    """Read the full details and body content of a specific email by its message ID."""
    return call_mcp_tool_sync("read_email", {"message_id": message_id})


@tool
def list_unread_emails(max_results: int = 5) -> str:
    """List recent unread emails from the inbox."""
    return call_mcp_tool_sync("list_unread_emails", {"max_results": max_results})


GMAIL_TOOLS = [search_emails, read_email, list_unread_emails]
