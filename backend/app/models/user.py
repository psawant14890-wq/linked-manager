import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Free-text context the user supplies so reply drafts sound like them,
    # e.g. "Backend engineer open to senior roles, not interested in sales pitches."
    bio_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    posts: Mapped[list["Post"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    connections: Mapped[list["Connection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    drafts: Mapped[list["GeneratedDraft"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list["WeeklyReport"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    import_logs: Mapped[list["ImportLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
