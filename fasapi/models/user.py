"""
fasapi/models/user.py
---------------------
Pure Python dataclasses that mirror the DB rows.
No ORM — rows are mapped manually in route helpers.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id:         UUID
    email:      str
    hashed_pw:  str
    created_at: datetime


@dataclass
class UserThread:
    thread_id:    UUID
    user_id:      UUID
    thread_title: str
    created_at:   datetime
    updated_at:   datetime
