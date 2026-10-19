from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body of POST /v1/chat/stream."""

    query: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(default="demo-user", min_length=1, max_length=64)
    session_id: str = Field(default="demo-session", min_length=1, max_length=64)
    stream: Literal[True] = Field(default=True)
    memory_top_k: int = Field(default=3, ge=1, le=10)
