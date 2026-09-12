import sys
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig


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
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

# graph is None until build_graph() is called (by main.py or FastAPI lifespan)
graph = None


def build_graph(tools: list):
    """Build and compile the LangGraph graph with the given MCP tools."""
    store = InMemoryStore()

    user_id = "u1"

    # Store user details as a single blob (simple for teaching)
    # You can also split into multiple records; this keeps it easy.P
    user_details = ("user", user_id, "details")

    store.put(user_details, "profile_1", {"data": "Name: Nitish"})
    store.put(user_details, "profile_2", {"data": "Profession: Teaches AI on YouTube"})
    store.put(user_details, "preference_1", {"data": "Prefers concise answers"})
    store.put(user_details, "preference_2", {"data": "Likes examples in Python"})
    store.put(user_details, "project_1", {"data": "Building MCP servers (Python-based project)"})
        
    global graph

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("hitl_review", hitl_review_node)
    workflow.add_node("pii_redaction", pii_redaction_node)

    workflow.add_edge(START, "agent")
    workflow.add_edge("tools", "pii_redaction")

    memory = MemorySaver()
    
    graph = workflow.compile(checkpointer=memory, store=store)
    return graph