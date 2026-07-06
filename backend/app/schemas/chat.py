"""Chat-related request/response schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")


class Citation(BaseModel):
    doc_name: str = Field(..., description="来源文档名")
    chunk_text: str = Field(..., description="引用原文片段")
    page: Optional[int] = Field(default=None, description="页码")
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID")


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str  # 'user' | 'assistant'
    content: str
    citations: list[Citation] = []
    feedback: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


class MessageFeedbackRequest(BaseModel):
    feedback: int = Field(..., ge=-1, le=1, description="1=点赞, -1=点踩")


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
