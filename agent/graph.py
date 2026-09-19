import sys
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.state import AgentState
from agent.agent_node import agent_node
from agent.hitl_node import hitl_review_node
from agent.pii_node import pii_redaction_node
from agent.remember_node import chat_creates_memory_node




# graph is None until build_graph() is called (by main.py or FastAPI lifespan)
graph = None


def build_graph(tools: list, store, checkpointer) -> StateGraph:
    """Build and compile the LangGraph graph with the given MCP tools.

    Accepts an already-open PostgresStore so the connection remains alive
    for the entire application session (managed by the caller via `with`).
    """
    global graph

    # Build the workflow graph.
    workflow = StateGraph(AgentState)

    workflow.add_node("remember",      chat_creates_memory_node)
    workflow.add_node("agent",         agent_node)
    workflow.add_node("tools",         ToolNode(tools))
    workflow.add_node("hitl_review",   hitl_review_node)
    workflow.add_node("pii_redaction", pii_redaction_node)

    workflow.add_edge(START,   "remember")
    workflow.add_edge("tools", "pii_redaction")

    # Short-term memory postgres checkpointer
    # Long-term memory is handled by the PostgresStore passed in.

    graph = workflow.compile(checkpointer=checkpointer, store=store)
    return graph