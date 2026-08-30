import asyncio
import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from client.mcp_client import ALL_TOOLS

# ---------------------------------------------------------------------------
# 1. Configuration & LLM Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are an intelligent enterprise AI assistant for Live Rag - Eval.
You have direct access to enterprise tools via Model Context Protocol (MCP):
- Gmail: search_emails, read_email, list_unread_emails
- GitHub: search_repositories, list_issues, get_issue, list_pull_requests, get_file_content

Guidelines:
1. When asked about emails, messages, or communication updates, USE Gmail tools to retrieve real-time data.
2. When asked about GitHub repositories, code, open issues, PRs, or file contents, USE GitHub tools to retrieve facts.
3. If you need to read the full body of an email or issue, call `read_email` or `get_issue` with its identifier.
4. For general knowledge, greetings, or questions not requiring external data, respond directly without calling tools.
5. When answering with retrieved data, provide clear, well-structured summaries citing relevant IDs, senders/authors, and key context.
"""

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.1,
)

# Bind all MCP tools to LLM
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ---------------------------------------------------------------------------
# 2. Define Graph Nodes (async for MCP tool compatibility)
# ---------------------------------------------------------------------------
async def agent_node(state: AgentState) -> dict:
    """Agent decision node: analyzes query and either calls tools or responds."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# 3. Build Workflow Graph (Agent <-> Tools Loop with Memory)
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(ALL_TOOLS))

# Add edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Compile with in-memory checkpointer for multi-turn conversation support
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)


# ---------------------------------------------------------------------------
# 4. Interactive Test CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    async def _test():
        print("=" * 60)
        print("  Live Rag - Eval: Agent connected to Gmail & GitHub MCP Servers")
        print("=" * 60)

        config = {"configurable": {"thread_id": "test-session-1"}}

        test_query = "Search for repositories by Luqmansyed75"
        print(f"\n[User Query]: {test_query}\n")
        print("Agent is thinking and querying MCP tools...\n")

        async for event in graph.astream(
            {"messages": [HumanMessage(content=test_query)]},
            config=config,
            stream_mode="values",
        ):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai" and last_msg.content:
                    print(f"[Agent]:\n{last_msg.content}\n")

    asyncio.run(_test())

