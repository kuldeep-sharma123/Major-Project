"""
Chat API Router
Endpoints for conversational interaction with the AI Testing Assistant.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.test_run import TestRun
from app.schemas.chat import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatMessage,
    ChatResponse,
)
from app.services.ai_service import ai_service

router = APIRouter(prefix="/chat")

# In-memory session history store
_SESSION_HISTORIES: Dict[str, List[ChatHistoryItem]] = {}


@router.post("", response_model=ChatResponse)
async def chat_with_agent(payload: ChatMessage, db: AsyncSession = Depends(get_db)):
    """
    Interact with the autonomous testing assistant.
    Examples:
    - 'Test OrangeHRM'
    - 'Analyze the recent failure'
    - 'How many tests passed today?'
    """
    session_id = payload.session_id or str(uuid.uuid4())

    # Build system context
    projects_stmt = select(Project).limit(5)
    p_res = await db.execute(projects_stmt)
    projects = p_res.scalars().all()

    runs_stmt = select(TestRun).order_by(TestRun.created_at.desc()).limit(5)
    r_res = await db.execute(runs_stmt)
    recent_runs = r_res.scalars().all()

    context = {
        "total_projects": len(projects),
        "recent_runs": [
            {
                "id": str(r.id),
                "status": r.status,
                "passed": r.passed,
                "failed": r.failed,
            }
            for r in recent_runs
        ],
    }

    # Retrieve history
    history = _SESSION_HISTORIES.setdefault(session_id, [])
    history_dicts = [{"role": h.role, "content": h.content} for h in history]

    # Call AI service
    ai_reply = await ai_service.chat_response(
        message=payload.message,
        context=context,
        history=history_dicts,
    )

    now = datetime.utcnow()
    # Save conversation turns
    history.append(
        ChatHistoryItem(role="user", content=payload.message, timestamp=now)
    )
    history.append(
        ChatHistoryItem(role="assistant", content=ai_reply, timestamp=now)
    )

    return ChatResponse(
        message=ai_reply,
        session_id=session_id,
        timestamp=now,
        tokens_used=180,
        model_used=ai_service.llm.__class__.__name__,
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Retrieve chat history for a given session."""
    history = _SESSION_HISTORIES.get(session_id, [])
    return ChatHistoryResponse(
        session_id=session_id,
        history=history,
        total=len(history),
    )

