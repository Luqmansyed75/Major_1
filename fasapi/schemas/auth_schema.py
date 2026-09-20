"""
fasapi/schemas/auth_schema.py
-----------------------------
Pydantic models for the /auth endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email:    str = Field(..., description="Valid email address.")
    password: str = Field(..., min_length=4, description="Minimum 8 characters.")


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class UserOut(BaseModel):
    id:         UUID
    email:      str
    created_at: datetime
