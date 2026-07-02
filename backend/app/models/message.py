import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MessageCategory(str, enum.Enum):
    SPAM = "spam"
    GENUINE = "genuine"
    RECRUITER = "recruiter"
    COLLABORATION = "collaboration"
    GENERAL = "general"
    NEEDS_REVIEW = "needs_review"  # classifier failed twice -> flagged for a human


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(String(280), nullable=True)

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Follow-up flagging: set True when the user manually marks a message
    # as actioned (replied, declined, saved elsewhere).  The /messages/follow-ups
    # endpoint surfaces messages that have a draft but is_actioned=False and
    # are older than follow_up_threshold_days.
    is_actioned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="messages")
