import sys
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.state import AgentState
from client.mcp_client import ALL_TOOLS
from agent.agent_node import agent_node
from agent.hitl_node import hitl_review_node
from agent.pii_node import pii_redaction_node

# ---------------------------------------------------------------------------
# Graph Definition & Flow Wiring
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(ALL_TOOLS))
workflow.add_node("hitl_review", hitl_review_node)
workflow.add_node("pii_redaction", pii_redaction_node)

# Flow Wiring
workflow.add_edge(START, "agent")
workflow.add_edge("tools", "pii_redaction")  # tools -> pii_redaction -> agent
# (agent and hitl_review route dynamically via Command(goto=...) internally)

# Compile with checkpointer (mandatory for interrupt / HITL support)
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
