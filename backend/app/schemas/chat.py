"""
Pydantic v2 schemas for AI chat endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message sent to the AI assistant."""

    message: str = Field(..., min_length=1, max_length=8000)
    context_type: Optional[str] = Field(
        None,
        description="Optional context scope: project | run | defect | general",
    )
    context_id: Optional[uuid.UUID] = Field(
        None, description="ID of the context object (project_id, run_id, etc.)"
    )
    session_id: Optional[str] = Field(None, description="Conversation session ID")


class ChatHistoryItem(BaseModel):
    """A single turn in the conversation history."""

    role: str                     # "user" | "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response returned from the AI assistant."""

    message: str
    session_id: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    context_references: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="References to relevant test cases, results, or defects",
    )


class ChatHistoryResponse(BaseModel):
    """Paginated conversation history."""

    session_id: str
    history: List[ChatHistoryItem]
    total: int
