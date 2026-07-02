import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    posted_at: datetime | None
    views: int | None
    likes: int | None
    comments: int | None


class PostGenerateRequest(BaseModel):
    raw_input: str = Field(
        ..., min_length=3, description="Bullet points, a topic, a project update, or draft text to turn into a post"
    )
    tone_hint: str | None = Field(
        default=None, description="Optional extra steering, e.g. 'more casual' or 'announcement style'"
    )


# --- Strict schema the LLM must return when proposing hashtags ---
class HashtagSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hashtags: list[str] = Field(min_length=1, max_length=8)
