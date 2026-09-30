"""
fasapi/routes/chat_route.py
----------------------------
Chat endpoints:

    POST /chat/ask             — send a message to the agent
    POST /chat/resume          — approve / reject a HITL action
    GET  /chat/history/{thread_id} — load past messages from the checkpointer
"""
import uuid
import io
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from fasapi.core.deps import get_current_user
from fasapi.schemas.chat_schema import (
    ChatRequest, ChatResponse, ResumeRequest, HITLEvent,
)
from config.logger_config import logger

router = APIRouter()


def _extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract readable text from uploaded files (PDF, text, code, csv, json, md, etc.)."""
    lower_name = filename.lower()
    logger.info(f"[_extract_text_from_file] Processing '{filename}' ({len(file_bytes)} bytes)")

    # 1. PDF documents
    if lower_name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            num_pages = len(reader.pages)
            logger.info(f"[_extract_text_from_file] PDF has {num_pages} pages")
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"--- Page {i + 1} ---\n{text.strip()}")
            if pages:
                extracted = "\n\n".join(pages)
                logger.info(f"[_extract_text_from_file] Extracted {len(extracted)} characters from PDF")
                logger.info(f"[_extract_text_from_file] Sample preview:\n{extracted[:300]}...")
                return extracted
            logger.warning(f"[_extract_text_from_file] PDF '{filename}' has {num_pages} pages, but no selectable text was found.")
            return "[PDF file uploaded, but no selectable text was found. It may be a scanned image.]"
        except Exception as e:
            logger.error(f"[_extract_text_from_file] Error extracting PDF text: {e}", exc_info=True)
            return f"[Error extracting text from PDF: {e}]"

    # 2. Standard text / code files
    try:
        extracted = file_bytes.decode("utf-8")
        logger.info(f"[_extract_text_from_file] Decoded UTF-8 text ({len(extracted)} chars)")
        return extracted
    except UnicodeDecodeError:
        try:
            extracted = file_bytes.decode("latin-1")
            logger.info(f"[_extract_text_from_file] Decoded Latin-1 text ({len(extracted)} chars)")
            return extracted
        except Exception as e:
            logger.error(f"[_extract_text_from_file] Could not decode text: {e}")
            return f"[Binary file: could not decode text ({e})]"


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
    summary="Send a message to the agent (with optional file upload)",
    description=(
        "Submit a user question with an optional attached file. "
        "Supports both `application/json` (standard chat payload) and "
        "`multipart/form-data` (when attaching a file). "
        "Pass `thread_id` to continue an existing conversation; omit it to start a fresh session. "
        "The returned `thread_id` must be supplied to every subsequent `/ask` or `/resume` "
        "call for the same session."
    ),
)
async def chat_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user),   # always from JWT — never anonymous
):
    graph = request.app.state.graph

    content_type = request.headers.get("content-type", "").lower()
    question: str = ""
    thread_id: Optional[str] = None
    file: Optional[UploadFile] = None

    logger.info(f"[chat_endpoint] Incoming request | content_type={content_type}")

    if "multipart/form-data" in content_type:
        form = await request.form()
        question = str(form.get("question") or "").strip()
        raw_thread_id = form.get("thread_id")
        if raw_thread_id and isinstance(raw_thread_id, str) and raw_thread_id.strip():
            thread_id = raw_thread_id.strip()
        raw_file = form.get("file")
        if hasattr(raw_file, "filename") and raw_file.filename:
            file = raw_file
            logger.info(f"[chat_endpoint] Multipart file detected: filename='{file.filename}'")
        else:
            logger.info("[chat_endpoint] Multipart request received, but no file attached.")
    else:
        try:
            body = await request.json()
            question = str(body.get("question") or "").strip()
            thread_id = body.get("thread_id")
            if thread_id and isinstance(thread_id, str):
                thread_id = thread_id.strip() or None
            logger.info("[chat_endpoint] JSON request received.")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")

    if not question and not file:
        raise HTTPException(status_code=422, detail="Either a question or an attached file must be provided.")

    attached_text = ""
    if file and file.filename:
        file_bytes = await file.read()
        filename = file.filename
        size_kb = round(len(file_bytes) / 1024, 1)

        logger.info(f"[chat_endpoint] Extracting content from '{filename}' ({size_kb} KB)...")
        extracted = _extract_text_from_file(filename, file_bytes)
        logger.info(f"[chat_endpoint] Content extracted successfully ({len(extracted)} chars).")

        attached_text = (
            f"[Attached File: {filename} ({size_kb} KB)]\n"
            f"--- File Content ---\n"
            f"{extracted}\n"
            f"--------------------\n\n"
        )

    if attached_text:
        if question:
            final_prompt = f"{attached_text}User Question: {question}"
        else:
            final_prompt = f"{attached_text}Please analyze, summarize, and explain the contents of this attached file."
    else:
        final_prompt = question

    logger.info(f"[chat_endpoint] Final prompt length: {len(final_prompt)} chars")
    logger.info(f"[chat_endpoint] Final prompt head preview:\n{final_prompt[:350]}...\n")

    thread_id = thread_id or str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id":   user_id,        # verified JWT identity
        },
        "run_name": "live-rag-eval-agent",
        "metadata": {
            "project": "Live_rag_eval",
            "env":     "development",
        },
    }

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=final_prompt)]},
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
async def resume_endpoint(
    request: Request,
    payload: ResumeRequest,
    user_id: str = Depends(get_current_user),
):
    graph = request.app.state.graph

    config = {
        "configurable": {
            "thread_id": payload.thread_id,
            "user_id":   user_id,
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
async def load_conversation(
    thread_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
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