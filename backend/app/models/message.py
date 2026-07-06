"""Message model — individual Q&A turns within a session."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON  # Will fallback to TEXT in SQLite
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[str] = mapped_column(Text, default="[]")
    # citations stored as JSON string: [{"doc_name": "...", "chunk_text": "...", "page": 1}]
    feedback: Mapped[int] = mapped_column(Integer, nullable=True)  # 1=thumbs up, -1=thumbs down
    token_count: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="messages")
