import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    NEW = "new"
    INTERESTED = "interested"
    APPLIED = "applied"
    DECLINED = "declined"


class JobOpportunity(Base):
    """
    Structured record extracted from a recruiter message by GPT-4o.
    One message can produce at most one JobOpportunity row; the extraction
    is idempotent -- re-running it on the same message upserts this row.
    """

    __tablename__ = "job_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, unique=True, index=True
    )

    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)   # remote / hybrid / onsite
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)   # raw string from message

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.NEW.value, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)   # user's own free-text notes

    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User")
    message: Mapped["Message"] = relationship("Message")
