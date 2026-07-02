from datetime import datetime

from pydantic import BaseModel


class PostingFrequencyPoint(BaseModel):
    period: str  # e.g. "2026-W12"
    post_count: int


class TopPost(BaseModel):
    content: str
    posted_at: datetime | None
    views: int | None
    likes: int | None
    comments: int | None


class CategoryBreakdownPoint(BaseModel):
    category: str
    count: int


class AnalyticsResponse(BaseModel):
    posting_frequency: list[PostingFrequencyPoint]
    top_posts: list[TopPost]
    category_breakdown: list[CategoryBreakdownPoint]
    total_posts: int
    total_messages: int
    avg_views: float | None
