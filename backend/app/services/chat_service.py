"""Chat service — business logic for chat operations."""
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.message import Message
from app.schemas.chat import Citation


async def get_chat_history(
    session_id: str, db: AsyncSession, limit: int = 20
) -> List[dict]:
    """Get recent chat history for context."""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]


async def save_message(
    session_id: str,
    role: str,
    content: str,
    citations: List[Citation] = None,
    db: AsyncSession = None,
) -> Message:
    """Save a message to the database."""
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        citations=[c.model_dump() if hasattr(c, 'model_dump') else c for c in (citations or [])],
    )
    if db:
        db.add(message)
        await db.flush()
    return message
