from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ResumeRequest(BaseModel):
    thread_id: str
    approval: str


class HITLEvent(BaseModel):
    tool_name: str
    args: dict


class ChatResponse(BaseModel):
    status: str
    thread_id: str
    answer: Optional[str] = None
    hitl_event: Optional[HITLEvent] = None