from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question:  str
    thread_id: Optional[str] = Field(
        default=None,
        description="Session thread ID. Omit to start a new conversation.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Caller identity. Defaults to 'anonymous' when omitted.",
    )


class ResumeRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID returned by /ask when status='pending'.")
    approval:  str = Field(..., description="'yes' to approve the action, 'no' to reject.")


class HITLEvent(BaseModel):
    tool_name: str
    args:      Dict[str, Any]


class ChatResponse(BaseModel):
    status:     str                           # "done" | "pending"
    thread_id:  str
    answer:     Optional[str]      = None
    hitl_event: Optional[HITLEvent] = None