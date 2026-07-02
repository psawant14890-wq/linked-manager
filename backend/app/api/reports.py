from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.core.sse import sse_event
from app.database import get_db
from app.models.message import Message
from app.models.post import Post
from app.models.report import WeeklyReport
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.draft import WeeklyReportGenerateRequest, WeeklyReportRead
from app.services.report_generator import stream_weekly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/weekly")
async def generate_weekly_report(
    payload: WeeklyReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Feature 6 -- on-demand, streamed weekly activity report."""
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=payload.period_days)

    messages_result = await db.execute(
        select(Message).where(
            Message.user_id == current_user.id,
            Message.received_at >= period_start,
            Message.received_at <= period_end,
        )
    )
    messages = messages_result.scalars().all()
    category_counts = Counter(m.category or "uncategorized" for m in messages)
    high_priority_count = sum(1 for m in messages if (m.priority_score or 0) >= 55)

    posts_result = await db.execute(
        select(Post).where(
            Post.user_id == current_user.id,
            Post.posted_at >= period_start,
            Post.posted_at <= period_end,
        )
    )
    posts = posts_result.scalars().all()
    posts_with_views = [p for p in posts if p.views is not None]
    avg_views = sum(p.views for p in posts_with_views) / len(posts_with_views) if posts_with_views else None
    top_post = max(posts_with_views, key=lambda p: p.views or 0) if posts_with_views else None

    async def event_generator():
        full_text = ""
        try:
            async for chunk in stream_weekly_report(
                period_start=period_start,
                period_end=period_end,
                message_count=len(messages),
                high_priority_count=high_priority_count,
                category_counts=dict(category_counts),
                posts_published=len(posts),
                avg_views=avg_views,
                top_post_excerpt=top_post.content[:150] if top_post else None,
            ):
                full_text += chunk
                yield sse_event("token", {"text": chunk})

            report = WeeklyReport(
                user_id=current_user.id,
                period_start=period_start,
                period_end=period_end,
                content=full_text,
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            yield sse_event("done", {"full_text": full_text, "report_id": str(report.id)})
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", {"message": f"Report generation failed: {exc}"})

    return EventSourceResponse(event_generator())


@router.get("", response_model=ApiResponse[list[WeeklyReportRead]])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.user_id == current_user.id).order_by(WeeklyReport.generated_at.desc())
    )
    reports = result.scalars().all()
    return ApiResponse.ok([WeeklyReportRead.model_validate(r) for r in reports])
