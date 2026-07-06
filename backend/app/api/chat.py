"""Chat routes — SSE streaming Q&A, message history, feedback."""
import json
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db, async_session_factory
from app.core.deps import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.schemas.chat import (
    ChatRequest,
    Citation,
    MessageResponse,
    MessageFeedbackRequest,
    MessageListResponse,
)
from app.rag.chain import rag_qa_stream
from app.rag.vector_store import get_store_stats

router = APIRouter()


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话的所有消息."""
    # Verify session ownership
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    msg_list = []
    for m in messages:
        try:
            citations_data = json.loads(m.citations) if isinstance(m.citations, str) else (m.citations if isinstance(m.citations, list) else [])
        except (json.JSONDecodeError, TypeError):
            citations_data = []
        citations = [Citation(**c) if isinstance(c, dict) else c for c in citations_data]
        msg_list.append(
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                citations=citations,
                feedback=m.feedback,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
        )

    return MessageListResponse(messages=msg_list, total=len(msg_list))


@router.post("/sessions/{session_id}/stream")
async def chat_stream(
    session_id: str,
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式问答接口."""
    # Verify session ownership
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # Check knowledge base is not empty
    stats = get_store_stats()
    if stats["total_vectors"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="知识库为空，请先上传文档",
        )

    # Get chat history for context
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(20)
    )
    history_messages = result.scalars().all()
    chat_history = [
        {"role": m.role, "content": m.content} for m in history_messages
    ]

    # Save user message
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # Update session title based on first message
    if len(history_messages) == 0:
        session.title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        await db.flush()

    async def event_generator():
        full_response = ""
        citations = []

        try:
            async for event in rag_qa_stream(req.message, chat_history):
                if event["type"] == "citations":
                    citations = event["citations"]
                    yield f"data: {json.dumps({'type': 'citations', 'citations': citations}, ensure_ascii=False)}\n\n"

                elif event["type"] == "token":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'token', 'content': event['content']}, ensure_ascii=False)}\n\n"

                elif event["type"] == "done":
                    # 保存助手消息到数据库
                    async with async_session_factory() as save_db:
                        try:
                            assistant_msg = Message(
                                session_id=session_id,
                                role="assistant",
                                content=full_response or event.get("full_response", ""),
                                citations=citations,
                            )
                            save_db.add(assistant_msg)
                            await save_db.commit()
                        except Exception as e:
                            await save_db.rollback()
                            logger.error(f"保存助手消息失败 (session={session_id}): {e}")

                    yield f"data: {json.dumps({'type': 'done', 'message_id': str(user_msg.id)}, ensure_ascii=False)}\n\n"

                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/feedback/{message_id}")
async def submit_feedback(
    session_id: str,
    message_id: str,
    req: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对消息提交反馈（点赞/点踩）."""
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.session_id == session_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")

    message.feedback = req.feedback
    await db.flush()
    return {"message": "反馈已提交"}
