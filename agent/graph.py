import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from client.mcp_client import GMAIL_TOOLS

# ---------------------------------------------------------------------------
# 1. Configuration & LLM Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are an intelligent enterprise AI assistant for Live Rag - Eval.
You have direct access to the user's Gmail via MCP tools (search_emails, read_email, list_unread_emails).

Guidelines:
1. When asked about emails, messages, schedules, senders, or communication updates, USE the appropriate tool to retrieve facts before answering.
2. If you need to read the full body of a message found during search, call `read_email` with its message_id.
3. For general knowledge, greetings, or questions not involving emails, respond directly without calling tools.
4. When answering with retrieved email data, clearly state the sender, subject, date, and key content.
"""

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.1,
)

# Bind MCP tools to LLM
llm_with_tools = llm.bind_tools(GMAIL_TOOLS)


# ---------------------------------------------------------------------------
# 2. Define Graph Nodes
# ---------------------------------------------------------------------------
def agent_node(state: AgentState) -> dict:
    """Agent decision node: analyzes query and either calls tools or responds."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# 3. Build Workflow Graph (Agent <-> Tools Loop with Memory)
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(GMAIL_TOOLS))

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
    print("=" * 60)
    print("  Live Rag - Eval: Agent connected to Gmail MCP Server")
    print("=" * 60)
    
    config = {"configurable": {"thread_id": "test-session-1"}}

    # Quick automated check
    test_query = "Check my latest unread emails and summarize what they are about."
    print(f"\n[User Query]: {test_query}\n")
    print("Agent is thinking and querying MCP tools...\n")

    events = graph.stream(
        {"messages": [HumanMessage(content=test_query)]},
        config=config,
        stream_mode="values"
    )

    for event in events:
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai" and last_msg.content:
                print(f"[Agent]:\n{last_msg.content}\n")
