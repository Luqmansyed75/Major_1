"""
fasapi/schemas/thread_schema.py
--------------------------------
Pydantic models for the /threads endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    thread_title: str = Field(
        default="New Conversation",
        description="Optional display title for the conversation.",
    )


class ThreadOut(BaseModel):
    thread_id:    UUID
    thread_title: str
    created_at:   datetime
    updated_at:   datetime


class ThreadListResponse(BaseModel):
    threads: list[ThreadOut]
