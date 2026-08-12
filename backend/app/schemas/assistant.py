from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    tool_calls_made: int


class ConversationRead(BaseModel):
    id: str
    title: str
    agent_id: str
    created_at: str


class MessageRead(BaseModel):
    role: str
    content: Any
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    agent_id: str
    created_at: str
    messages: List[MessageRead]

