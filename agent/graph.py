import asyncio
import json
import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from agent.state import AgentState
from client.mcp_client import ALL_TOOLS

# ---------------------------------------------------------------------------
# 1. Configuration & LLM Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Tools that require human approval before execution
HIGH_RISK_TOOLS = {"send_email"}

SYSTEM_PROMPT = """You are an intelligent enterprise AI assistant for Live Rag - Eval.
You have direct access to enterprise tools via Model Context Protocol (MCP):
- Gmail: search_emails, read_email, list_unread_emails, send_email
- GitHub: search_repositories, get_repository, list_issues, get_issue, list_pull_requests, get_file_content, list_commits

Guidelines:
1. When asked about emails, messages, or communication updates, USE Gmail tools.
2. When asked about GitHub repositories, code, issues, PRs, or commits, USE GitHub tools.
3. When asked to send an email, call send_email with to, subject, and body.
4. For general knowledge or greetings, respond directly without calling tools.
5. When answering with retrieved data, provide clear summaries citing relevant IDs and context.
"""

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.1,
)

llm_with_tools = llm.bind_tools(ALL_TOOLS)

# ---------------------------------------------------------------------------
# 1. Nodes (Routing + State Update combined via Command)
# ---------------------------------------------------------------------------
async def agent_node(state: AgentState) -> Command:
    """Agent analyzes query and routes directly using Command(goto=...)."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    # 1. No tool calls -> Route to END
    if not hasattr(response, "tool_calls") or not response.tool_calls:
        return Command(
            update={"messages": [response]},
            goto=END
        )
    # 2. High-risk tool call -> Route directly to 'hitl_review'
    if response.tool_calls[0]["name"] in HIGH_RISK_TOOLS:
        return Command(
            update={"messages": [response]},
            goto="hitl_review"
        )
    # 3. Low-risk tool call -> Route directly to 'tools'
    return Command(
        update={"messages": [response]},
        goto="tools"
    )
async def hitl_review_node(state: AgentState) -> Command:
    """HITL node: pauses for approval, then routes to 'tools' or back to 'agent'."""
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    # Freeze graph for human decision
    user_decision = interrupt({
        "tool_name": tool_call["name"],
        "args": tool_call["args"],
    })
    # If REJECTED -> Inject ToolMessage and route back to 'agent'
    if str(user_decision).lower() not in ("yes", "approve", "y"):
        rejection_msg = ToolMessage(
            tool_call_id=tool_call["id"],
            name=tool_call["name"],
            content=f"Action '{tool_call['name']}' was REJECTED by the user."
        )
        return Command(
            update={"messages": [rejection_msg]},
            goto="agent"
        )
    # If APPROVED -> Route directly to 'tools' to execute
    return Command(goto="tools")
# ---------------------------------------------------------------------------
# 2. Add Nodes and Edges
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)
# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(ALL_TOOLS))
workflow.add_node("hitl_review", hitl_review_node)
# Look how simple the edges become:
workflow.add_edge(START, "agent")
workflow.add_edge("tools", "agent")

# Compile with checkpointer (mandatory for interrupt support)
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
