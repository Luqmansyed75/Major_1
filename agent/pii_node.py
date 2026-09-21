import re
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from agent.state import AgentState
from config.logger_config import logger

# ---------------------------------------------------------------------------
# PII Patterns for Redaction
# ---------------------------------------------------------------------------
PII_PATTERNS = [
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]"),
    (r"(?<!\w)(\+?[\d]{1,4}[\s\-.()\d]{6,14}\d)(?![\w\-T])",  "[REDACTED_PHONE]"),
    (r"(?i)(ghp_|sk-|AIza|Bearer )[A-Za-z0-9\-_]{10,}",  "[REDACTED_API_KEY]"),
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",  "[REDACTED_CARD]"),
    (r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",                        "[REDACTED_PAN]"),
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b",                        "[REDACTED_AADHAAR]"),
]


# ---------------------------------------------------------------------------
# PII Redaction Node Implementation
# ---------------------------------------------------------------------------
def pii_redaction_node(state: AgentState) -> Command:
    """Scans the latest ToolMessage content and redacts PII before the LLM sees it."""
    logger.info("pii_redaction_node | entered")
    last_message = state["messages"][-1]

    # Only process ToolMessages
    if not isinstance(last_message, ToolMessage):
        logger.info("pii_redaction_node | last message is not a ToolMessage -> routing to agent")
        return Command(goto="agent")

    # content can be a list of blocks (from MCP) or a plain string — normalise to str
    raw_content = last_message.content
    if isinstance(raw_content, list):
        raw_content = " ".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in raw_content
        )

    redacted_content = raw_content
    for pattern, label in PII_PATTERNS:
        redacted_content = re.sub(pattern, label, redacted_content)

    logger.info(f"pii_redaction_node | PII redaction applied on tool message: {last_message.name}")

    cleaned_message = ToolMessage(
        id=last_message.id,                    # Same id -> add_messages replaces in-place
        tool_call_id=last_message.tool_call_id,
        name=last_message.name,
        content=redacted_content,
    )

    logger.info("pii_redaction_node | routing to agent")
    return Command(
        update={"messages": [cleaned_message]},
        goto="agent",
    )
