"""
fasapi/routes/chat_route.py
----------------------------
Chat endpoints:

    POST /chat/ask             — send a message to the agent
    POST /chat/resume          — approve / reject a HITL action
    GET  /chat/history/{thread_id} — load past messages from the checkpointer
"""
import uuid
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from fasapi.schemas.chat_schema import (
    ChatRequest, ChatResponse, ResumeRequest, HITLEvent,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Shared helper — called after every graph.ainvoke()
# Returns a pending response if the graph hit a HITL interrupt,
# or a done response with the final assistant answer.
# ---------------------------------------------------------------------------
async def _resolve(graph, result, config: dict, thread_id: str) -> ChatResponse:
    state = await graph.aget_state(config)

    # Graph hit a HITL interrupt — pause and return preview to frontend
    if state.tasks and any(task.interrupts for task in state.tasks):
        for task in state.tasks:
            for intr in task.interrupts:
                data = intr.value
                return ChatResponse(
                    status="pending",
                    thread_id=thread_id,
                    hitl_event=HITLEvent(
                        tool_name=data.get("tool_name", "unknown"),
                        args=data.get("args", {}),
                    ),
                )

    # Graph finished — return final answer
    final_msg = result["messages"][-1]
    answer = final_msg.content if hasattr(final_msg, "content") else ""
    return ChatResponse(status="done", thread_id=thread_id, answer=answer)


# ---------------------------------------------------------------------------
# POST /chat/ask
# ---------------------------------------------------------------------------
@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Send a message to the agent",
    description=(
        "Submit a user question.  Pass `thread_id` to continue an existing "
        "conversation; omit it to start a fresh session.  The returned "
        "`thread_id` must be supplied to every subsequent `/ask` or `/resume` "
        "call for the same session."
    ),
)
async def chat_endpoint(request: Request, payload: ChatRequest):
    graph = request.app.state.graph

    thread_id = payload.thread_id or str(uuid.uuid4())
    user_id   = payload.user_id   or "anonymous"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id":   user_id,
        },
        "run_name": "live-rag-eval-agent",
        "metadata": {
            "project": "Live_rag_eval",
            "env":     "development",
        },
    }

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=payload.question)]},
        config=config,
    )

    return await _resolve(graph, result, config, thread_id)


# ---------------------------------------------------------------------------
# POST /chat/resume
# ---------------------------------------------------------------------------
@router.post(
    "/resume",
    response_model=ChatResponse,
    summary="Approve or reject a pending HITL action",
    description=(
        "Resume a paused graph thread.  Send `thread_id` (returned by `/ask` "
        "when `status == 'pending'`) together with `approval` ('yes' or 'no')."
    ),
)
async def resume_endpoint(request: Request, payload: ResumeRequest):
    graph = request.app.state.graph

    config = {
        "configurable": {
            "thread_id": payload.thread_id,
        },
        "run_name": "live-rag-eval-agent",
        "metadata": {
            "project": "Live_rag_eval",
            "env":     "development",
        },
    }

    result = await graph.ainvoke(
        Command(resume=payload.approval),
        config=config,
    )

    return await _resolve(graph, result, config, payload.thread_id)


# ---------------------------------------------------------------------------
# GET /chat/history/{thread_id}
# Reads saved messages from the LangGraph checkpointer for a given thread.
# ---------------------------------------------------------------------------
@router.get(
    "/history/{thread_id}",
    summary="Load conversation history",
    description=(
        "Reads the LangGraph checkpointer state for the given `thread_id` and "
        "returns the full message history as a list of {role, content} objects."
    ),
)
async def load_conversation(thread_id: str, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    messages = state.values.get("messages", [])
    history = []
    for m in messages:
        if isinstance(m, HumanMessage):
            # Always include user messages
            history.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            # Only include AI messages that have actual text (not pure tool-call messages)
            content = m.content
            if isinstance(content, list):
                # Extract text blocks from multimodal content
                text = " ".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = content or ""
            if text.strip():
                history.append({"role": "assistant", "content": text.strip()})
        # ToolMessage is intentionally skipped — it's raw API JSON, not chat output
    return history