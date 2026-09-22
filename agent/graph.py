import sys
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.state import AgentState
from agent.agent_node import agent_node, GITHUB_TOOLS, GMAIL_TOOLS
from agent.hitl_node import hitl_review_node
from agent.pii_node import pii_redaction_node
from agent.remember_node import chat_creates_memory_node


# ---------------------------------------------------------------------------
# Custom ToolNode — injects per-user credentials into tool call arguments
# before forwarding to the actual MCP tool subprocess.
# ---------------------------------------------------------------------------
class CredentialInjectingToolNode(ToolNode):
    """
    Wraps LangGraph's standard ToolNode.

    Before each tool call is executed, this node reads the user's
    github_token and gmail_token_json from config["configurable"]
    (placed there by agent_node after fetching from the DB) and
    silently injects them as keyword arguments.

    The LLM never sees or generates the credential values — it only
    decides which tool to call and with what query arguments.
    """

    async def ainvoke(self, input: dict, config: RunnableConfig | None = None, **kwargs):
        configurable = (config or {}).get("configurable", {}) if isinstance(config, dict) else {}

        github_token     = configurable.get("github_token", "")
        gmail_token_json = configurable.get("gmail_token_json", "")
        user_id          = configurable.get("user_id", "")

        # Fallback: if credentials not yet populated in configurable (e.g. resuming from HITL), load from DB
        if user_id and (not github_token or not gmail_token_json):
            try:
                from agent.agent_node import _load_user_credentials
                creds = await _load_user_credentials(user_id)
                github_token     = github_token or creds.get("github_token", "")
                gmail_token_json = gmail_token_json or creds.get("gmail_token_json", "")
            except Exception:
                pass

        # Inject credentials into the last AI message's tool_calls in-place
        messages = input.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                # Build a new list of tool_calls with credentials injected
                patched_calls = []
                for tc in last_msg.tool_calls:
                    tool_name = tc["name"]
                    new_args  = dict(tc["args"])   # shallow copy

                    if tool_name in GITHUB_TOOLS and github_token:
                        new_args.setdefault("github_token", github_token)

                    if tool_name in GMAIL_TOOLS and gmail_token_json:
                        new_args.setdefault("gmail_token_json", gmail_token_json)

                    patched_calls.append({**tc, "args": new_args})

                # Replace the tool_calls on the message copy
                last_msg = last_msg.model_copy(update={"tool_calls": patched_calls})
                input = {**input, "messages": messages[:-1] + [last_msg]}

        return await super().ainvoke(input, config, **kwargs)


# ---------------------------------------------------------------------------
# graph is None until build_graph() is called (by main.py or FastAPI lifespan)
# ---------------------------------------------------------------------------
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
    workflow.add_node("tools",         CredentialInjectingToolNode(tools))  # custom node
    workflow.add_node("hitl_review",   hitl_review_node)
    workflow.add_node("pii_redaction", pii_redaction_node)

    workflow.add_edge(START,   "remember")
    workflow.add_edge("tools", "pii_redaction")

    # Short-term memory postgres checkpointer
    # Long-term memory is handled by the PostgresStore passed in.

    graph = workflow.compile(checkpointer=checkpointer, store=store)
    return graph