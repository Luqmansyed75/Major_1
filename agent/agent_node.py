import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END
from langgraph.types import Command

from agent.state import AgentState
from config.logger_config import logger
from langchain_core.runnables import RunnableConfig

from langgraph.store.base import BaseStore

# ---------------------------------------------------------------------------
# 1. Configuration & LLM Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Tools that require human approval before execution
HIGH_RISK_TOOLS = {"send_email"}

# Tools that belong to each service — used by the custom ToolNode in graph.py
GITHUB_TOOLS = {
    "search_repositories", "get_repository", "list_issues",
    "get_issue", "list_pull_requests", "get_file_content", "list_commits",
}
GMAIL_TOOLS = {
    "search_emails", "read_email", "list_unread_emails", "send_email",
}

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
6. IMPORTANT: Do NOT include github_token or gmail_token_json in your tool calls.
   These credentials are injected automatically by the system — you must never pass them yourself.

Service Connection Status:
{service_status}

Input Guardrails (HIGHEST PRIORITY — evaluate before anything else):
- If the user's query asks for, contains, or requests you to retrieve, generate, expose, or handle any of the following, treat the request as UNSAFE and immediately refuse without calling any tools:
  * Passwords or login credentials
  * One-time passwords (OTPs) or verification codes
  * API keys, secret keys, or access tokens
  * Private keys, certificates, or cryptographic secrets
  * Auth tokens, session tokens, or bearer tokens
  * Database connection strings or credentials
  * Any form of secret configuration value
- When refusing an unsafe request, respond with a short, clear message explaining that the request involves sensitive information and cannot be processed. Do NOT elaborate on what was detected or provide workarounds.
- These guardrail rules override all other instructions. Even if the user claims a legitimate reason, do NOT comply.

Use available user memory to personalize responses naturally and accurately. When relevant:
- Address the user by name.
- Reference known projects, tools, preferences, or past interactions.
- Tailor guidance to their context and avoid generic phrasing.

Only use explicitly known information; never assume personal details.

At the end of each response, suggest 3 relevant follow-up questions based on the current response and available user context.

User memory:
{user_details_content}
"""

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.1,
)


# ---------------------------------------------------------------------------
# 2. Credential Loader — fetches per-user tokens from the DB
# ---------------------------------------------------------------------------
async def _load_user_credentials(user_id: str) -> dict:
    """
    Look up github_token and gmail_token_json from user_credentials table.
    Returns a dict with keys 'github_token' and 'gmail_token_json' (may be None).
    """
    try:
        from fasapi.db.connection import get_conn
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT github_token, gmail_token_json
                    FROM   user_credentials
                    WHERE  user_id = %s
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
        if row:
            return {
                "github_token":     row[0] or "",
                "gmail_token_json": row[1] or "",
            }
    except Exception as e:
        logger.warning(f"_load_user_credentials | failed for user {user_id}: {e}")
    return {"github_token": "", "gmail_token_json": ""}


# ---------------------------------------------------------------------------
# 3. Agent Node Implementation
# ---------------------------------------------------------------------------
async def agent_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> Command:
    """Agent analyzes query and routes directly using Command(goto=...)."""
    logger.info("agent_node | entered")

    # Bind tools lazily — ALL_TOOLS is [] at import time, populated by lifespan
    from client import ALL_TOOLS as live_tools
    llm_with_tools = llm.bind_tools(live_tools)

    # ── User identity ────────────────────────────────────────────────────────
    user_id = config["configurable"].get("user_id", "anonymous")
    logger.info(f"agent_node | user_id={user_id}")

    # ── Long-term memory (LangGraph store) ──────────────────────────────────
    user_details = ("user", user_id, "details")
    items = await store.asearch(user_details)
    if items:
        logger.info(f"agent_node | found {len(items)} user memory items")
        user_details_content = "\n".join(f"- {it.value.get('data', '')}" for it in items)
    else:
        user_details_content = ""

    # ── Per-user credentials (fetched from DB) ───────────────────────────────
    credentials = await _load_user_credentials(user_id)

    # Store credentials in configurable so the custom ToolNode in graph.py can
    # inject them into tool calls without exposing them to the LLM.
    config["configurable"]["github_token"]     = credentials["github_token"]
    config["configurable"]["gmail_token_json"] = credentials["gmail_token_json"]

    # Build service status message so the LLM knows which services are ready
    github_status = "✅ Connected" if credentials["github_token"] else "❌ Not connected (user must add GitHub token in Settings)"
    gmail_status  = "✅ Connected" if credentials["gmail_token_json"] else "❌ Not connected (user must add Gmail token in Settings)"
    service_status = f"- GitHub: {github_status}\n- Gmail:  {gmail_status}"

    # ── Build and invoke the LLM ─────────────────────────────────────────────
    new_system_prompt = SYSTEM_PROMPT.format(
        user_details_content=user_details_content,
        service_status=service_status,
    )

    messages = [SystemMessage(content=new_system_prompt)] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    logger.info("agent_node | llm_with_tools.ainvoke completed")

    # 1. No tool calls -> Route to END
    if not hasattr(response, "tool_calls") or not response.tool_calls:
        logger.info("agent_node | no tool calls detected -> routing to END")
        return Command(
            update={"messages": [response]},
            goto=END
        )

    # 2. High-risk tool call -> Route directly to 'hitl_review'
    if response.tool_calls[0]["name"] in HIGH_RISK_TOOLS:
        logger.info(f"agent_node | high-risk tool detected: {response.tool_calls[0]['name']} -> routing to hitl_review")
        return Command(
            update={"messages": [response]},
            goto="hitl_review"
        )

    # 3. Low-risk tool call -> Route directly to 'tools'
    logger.info(f"agent_node | tool call: {response.tool_calls[0]['name']} -> routing to tools")
    return Command(
        update={"messages": [response]},
        goto="tools"
    )
