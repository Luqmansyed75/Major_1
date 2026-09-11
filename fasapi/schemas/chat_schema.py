from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[str] = None      # Session thread ID from frontend


class ResumeRequest(BaseModel):
    thread_id: str                       # Paused thread ID
    approval: str                        # "yes" or "no"


class HITLEvent(BaseModel):
    tool_name: str
    args: dict


class ChatResponse(BaseModel):
    status: str                          # "done" | "pending"
    thread_id: str
    answer: Optional[str] = None
    hitl_event: Optional[HITLEvent] = None