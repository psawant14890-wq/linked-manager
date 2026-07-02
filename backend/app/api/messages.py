import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.core.sse import sse_event
from app.database import get_db
from app.models.draft import DraftType, GeneratedDraft
from app.models.message import Message, MessageCategory
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.message import DraftReplyRequest, MessageRead
from app.services.classifier import classify_message, compute_priority_score
from app.services.reply_generator import stream_reply_draft

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=ApiResponse[list[MessageRead]])
async def list_messages(
    category: str | None = Query(default=None),
    min_priority: float | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Message).where(Message.user_id == current_user.id)
    if category:
        stmt = stmt.where(Message.category == category)
    if min_priority is not None:
        stmt = stmt.where(Message.priority_score >= min_priority)
    stmt = stmt.order_by(Message.priority_score.desc().nulls_last(), Message.received_at.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    messages = result.scalars().all()
    return ApiResponse.ok([MessageRead.model_validate(m) for m in messages])


@router.post("/{message_id}/classify", response_model=ApiResponse[MessageRead])
async def classify_single_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Classifies (or re-classifies) a single message. The bulk import flow
    calls this same service function in a background batch job in
    production; this endpoint exists so the frontend can also trigger or
    retry classification for one message at a time (e.g. after it was
    flagged needs_review).
    """
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == current_user.id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    classification = await classify_message(sender_name=message.sender_name, content=message.content)

    if classification is None:
        message.category = MessageCategory.NEEDS_REVIEW.value
        message.priority_score = compute_priority_score(MessageCategory.NEEDS_REVIEW, 0.5)
        message.summary = "Could not auto-classify this message -- please review manually."
    else:
        category_enum = MessageCategory(classification.category.value)
        message.category = category_enum.value
        message.priority_score = compute_priority_score(category_enum, classification.relevance_score)
        message.summary = classification.summary

    await db.commit()
    await db.refresh(message)
    return ApiResponse.ok(MessageRead.model_validate(message))


@router.post("/{message_id}/draft-reply")
async def draft_reply(
    message_id: str,
    payload: DraftReplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Feature 4 -- streams a reply draft via SSE. The draft is also
    persisted to generated_drafts once streaming completes so it shows
    up in history. Never sends anything -- this only ever produces text
    for the user to copy.
    """
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == current_user.id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    async def event_generator():
        full_text = ""
        try:
            async for chunk in stream_reply_draft(
                message_sender=message.sender_name,
                message_content=message.content,
                bio_context=payload.bio_context,
            ):
                full_text += chunk
                yield sse_event("token", {"text": chunk})

            draft = GeneratedDraft(
                user_id=current_user.id,
                message_id=message.id,
                draft_type=DraftType.REPLY.value,
                content=full_text,
            )
            db.add(draft)
            await db.commit()
            await db.refresh(draft)

            yield sse_event("done", {"full_text": full_text, "draft_id": str(draft.id)})
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", {"message": f"Generation failed: {exc}"})

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Feature: Follow-up flagging
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone  # noqa: E402 -- appended block


@router.get("/follow-ups", response_model=ApiResponse[list[MessageRead]])
async def list_follow_ups(
    days: int = 3,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns messages that:
      1. Have at least one AI-generated reply draft (user took action but
         hasn't marked it as done)
      2. Have not been marked is_actioned=True
      3. Were received more than `days` days ago

    The intent: surface recruiter/collaboration messages you drafted a reply
    for but haven't sent yet, so nothing falls through the cracks.
    """
    from app.models.draft import DraftType, GeneratedDraft  # avoid circular at module level

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Sub-select: message IDs that have a reply draft
    drafted_ids_stmt = (
        select(GeneratedDraft.message_id)
        .where(
            GeneratedDraft.user_id == current_user.id,
            GeneratedDraft.draft_type == DraftType.REPLY.value,
            GeneratedDraft.message_id.is_not(None),
        )
        .distinct()
    )

    stmt = (
        select(Message)
        .where(
            Message.user_id == current_user.id,
            Message.is_actioned.is_(False),
            Message.id.in_(drafted_ids_stmt),
            Message.received_at <= cutoff,
        )
        .order_by(Message.priority_score.desc().nulls_last())
        .limit(50)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()
    return ApiResponse.ok([MessageRead.model_validate(m) for m in messages])


@router.post("/{message_id}/mark-actioned", response_model=ApiResponse[MessageRead])
async def mark_actioned(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks a message as actioned so it leaves the follow-up list."""
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == current_user.id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    message.is_actioned = True
    message.actioned_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(message)
    return ApiResponse.ok(MessageRead.model_validate(message))
