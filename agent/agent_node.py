import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END
from langgraph.types import Command

from agent.state import AgentState
from client import ALL_TOOLS
from config.logger_config import logger

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
"""

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.1,
)

llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ---------------------------------------------------------------------------
# 2. Agent Node Implementation
# ---------------------------------------------------------------------------
async def agent_node(state: AgentState) -> Command:
    """Agent analyzes query and routes directly using Command(goto=...)."""
    logger.info("agent_node | entered")
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
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
