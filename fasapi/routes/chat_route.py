import uuid
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from fasapi.schemas.chat_schema import (
    ChatRequest, ChatResponse, ResumeRequest, HITLEvent
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Shared helper - called after every graph.ainvoke()
# Checks if graph paused (pending) or finished (done)
# ---------------------------------------------------------------------------
async def _resolve(graph, result, config: dict, thread_id: str) -> ChatResponse:
    state = await graph.aget_state(config)

    # Graph hit a HITL interrupt - pause and return preview to frontend
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
                    )
                )

    # Graph finished - return final answer
    final_msg = result["messages"][-1]
    answer = final_msg.content if hasattr(final_msg, "content") else ""
    return ChatResponse(status="done", thread_id=thread_id, answer=answer)


# ---------------------------------------------------------------------------
# POST /ask - user sends a question
# ---------------------------------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def chat_endpoint(request: Request, payload: ChatRequest):
    graph = request.app.state.graph          # safely fetched from app.state
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=payload.question)]},
        config=config,
    )

    return await _resolve(graph, result, config, thread_id)


# ---------------------------------------------------------------------------
# POST /resume - user clicks Approve / Reject on the frontend modal
# ---------------------------------------------------------------------------
@router.post("/resume", response_model=ChatResponse)
async def resume_endpoint(request: Request, payload: ResumeRequest):
    graph = request.app.state.graph          # safely fetched from app.state
    config = {"configurable": {"thread_id": payload.thread_id}}

    result = await graph.ainvoke(
        Command(resume=payload.approval),
        config=config,
    )

    return await _resolve(graph, result, config, payload.thread_id)
