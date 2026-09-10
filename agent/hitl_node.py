from langchain_core.messages import ToolMessage
from langgraph.types import Command, interrupt
from agent.state import AgentState
from config.logger_config import logger


# ---------------------------------------------------------------------------
# HITL Review Node Implementation
# ---------------------------------------------------------------------------
async def hitl_review_node(state: AgentState) -> Command:
    """HITL node: pauses for approval, then routes to 'tools' or back to 'agent'."""
    logger.info("hitl_review_node | entered")
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    logger.info(f"hitl_review_node | awaiting human approval for tool: {tool_call['name']}")

    # Freeze graph for human decision
    user_decision = interrupt({
        "tool_name": tool_call["name"],
        "args": tool_call["args"],
    })

    # If REJECTED -> Inject ToolMessage and route back to 'agent'
    if str(user_decision).lower() not in ("yes", "approve", "y"):
        logger.info(f"hitl_review_node | tool '{tool_call['name']}' REJECTED -> routing to agent")
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
    logger.info(f"hitl_review_node | tool '{tool_call['name']}' APPROVED -> routing to tools")
    return Command(goto="tools")
