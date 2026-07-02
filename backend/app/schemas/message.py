import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageCategoryEnum(str, Enum):
    SPAM = "spam"
    GENUINE = "genuine"
    RECRUITER = "recruiter"
    COLLABORATION = "collaboration"
    GENERAL = "general"


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_name: str
    content: str
    category: str | None
    priority_score: float | None
    summary: str | None
    received_at: datetime | None
    imported_at: datetime


class MessageListParams(BaseModel):
    category: MessageCategoryEnum | None = None
    min_priority: float | None = None
    limit: int = Field(default=50, le=200)
    offset: int = 0


# --- Strict schema the LLM must return for classification ---
# This is the contract enforced on every GPT-4o classification call.
# If the model's output doesn't validate against this, classifier.py
# retries once with a stricter reminder, then falls back to NEEDS_REVIEW.
class MessageClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: MessageCategoryEnum
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM's judgment of how relevant/important this message is within its category",
    )
    summary: str = Field(max_length=140, description="One-line summary of the message")
    reasoning: str = Field(max_length=280, description="Brief justification for the category chosen")


class DraftReplyRequest(BaseModel):
    bio_context: str = Field(
        ..., description="User's self-description used to tailor the reply, e.g. role + what they're open to"
    )
