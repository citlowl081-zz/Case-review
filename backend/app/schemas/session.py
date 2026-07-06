"""Session-related request/response schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default="新对话", max_length=200)


class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
