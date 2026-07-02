from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.message import Message
from app.models.post import Post
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, CategoryBreakdownPoint, PostingFrequencyPoint, TopPost
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=ApiResponse[AnalyticsResponse])
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    posts_result = await db.execute(
        select(Post).where(Post.user_id == current_user.id).order_by(Post.posted_at.asc())
    )
    posts = posts_result.scalars().all()

    # Posting frequency by ISO week
    freq_buckets: dict[str, int] = defaultdict(int)
    for p in posts:
        if p.posted_at:
            key = f"{p.posted_at.isocalendar().year}-W{p.posted_at.isocalendar().week:02d}"
            freq_buckets[key] += 1
    posting_frequency = [
        PostingFrequencyPoint(period=k, post_count=v) for k, v in sorted(freq_buckets.items())
    ]

    # Top posts by views (falls back gracefully if engagement data wasn't in the export)
    posts_with_views = [p for p in posts if p.views is not None]
    top_sorted = sorted(posts_with_views, key=lambda p: p.views or 0, reverse=True)[:5]
    top_posts = [
        TopPost(content=p.content[:200], posted_at=p.posted_at, views=p.views, likes=p.likes, comments=p.comments)
        for p in top_sorted
    ]

    # Category breakdown of received messages
    cat_result = await db.execute(
        select(Message.category, func.count(Message.id))
        .where(Message.user_id == current_user.id)
        .group_by(Message.category)
    )
    category_breakdown = [
        CategoryBreakdownPoint(category=cat or "uncategorized", count=count) for cat, count in cat_result.all()
    ]

    total_messages_result = await db.execute(
        select(func.count(Message.id)).where(Message.user_id == current_user.id)
    )
    total_messages = total_messages_result.scalar_one()

    avg_views = (
        sum(p.views for p in posts_with_views) / len(posts_with_views) if posts_with_views else None
    )

    return ApiResponse.ok(
        AnalyticsResponse(
            posting_frequency=posting_frequency,
            top_posts=top_posts,
            category_breakdown=category_breakdown,
            total_posts=len(posts),
            total_messages=total_messages,
            avg_views=avg_views,
        )
    )
