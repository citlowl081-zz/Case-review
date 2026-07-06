"""Session routes — CRUD for chat sessions."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
)

router = APIRouter()


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有会话（按更新时间倒序）."""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
    )
    sessions = result.scalars().all()

    session_list = []
    for s in sessions:
        count_result = await db.execute(
            select(func.count(Message.id)).where(Message.session_id == s.id)
        )
        msg_count = count_result.scalar() or 0
        session_list.append(
            SessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at.isoformat() if s.created_at else "",
                updated_at=s.updated_at.isoformat() if s.updated_at else "",
                message_count=msg_count,
            )
        )

    return SessionListResponse(sessions=session_list, total=len(session_list))


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    req: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新会话."""
    session = Session(user_id=current_user.id, title=req.title or "新对话")
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        message_count=0,
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    req: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重命名会话."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    session.title = req.title
    await db.flush()

    count_result = await db.execute(
        select(func.count(Message.id)).where(Message.session_id == session.id)
    )
    msg_count = count_result.scalar() or 0

    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        message_count=msg_count,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（级联删除所有消息）."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    await db.delete(session)
    await db.flush()
    return {"message": "会话已删除"}
