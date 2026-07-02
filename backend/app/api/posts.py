import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.core.sse import sse_event
from app.database import get_db
from app.models.draft import DraftType, GeneratedDraft
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.post import PostGenerateRequest
from app.services.embeddings import retrieve_similar_posts
from app.services.post_generator import stream_post_generation, suggest_hashtags
from app.services.post_variants import generate_variants_concurrent

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/generate")
async def generate_post(
    payload: PostGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    style_examples = await retrieve_similar_posts(db, user_id=current_user.id, query_text=payload.raw_input, top_k=3)

    async def event_generator():
        full_text = ""
        try:
            yield sse_event(
                "style_examples_used",
                {"count": len(style_examples), "examples": [p.content[:120] for p in style_examples]},
            )
            async for chunk in stream_post_generation(
                raw_input=payload.raw_input,
                tone_hint=payload.tone_hint,
                style_examples=style_examples,
            ):
                full_text += chunk
                yield sse_event("token", {"text": chunk})

            hashtags = await suggest_hashtags(full_text)
            draft = GeneratedDraft(
                user_id=current_user.id,
                message_id=None,
                draft_type=DraftType.POST.value,
                content=full_text,
            )
            db.add(draft)
            await db.commit()
            await db.refresh(draft)
            yield sse_event("done", {"full_text": full_text, "hashtags": hashtags, "draft_id": str(draft.id)})
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", {"message": f"Generation failed: {exc}"})

    return EventSourceResponse(event_generator())


@router.post("/variants")
async def generate_post_variants(
    payload: PostGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Feature: Post Variant Generator.

    Generates professional / casual / storytelling variants concurrently
    using asyncio.gather (total latency ~1x rather than 3x). Streams
    variant_done events as each finishes, then a final all_done event.
    Each variant is also persisted as a GeneratedDraft so the user can
    come back to any of them later.
    """
    style_examples = await retrieve_similar_posts(db, user_id=current_user.id, query_text=payload.raw_input, top_k=3)

    async def event_generator():
        try:
            yield sse_event("style_examples_used", {"count": len(style_examples)})

            async for evt in generate_variants_concurrent(payload.raw_input, style_examples):
                if evt["event"] == "variant_done":
                    draft = GeneratedDraft(
                        user_id=current_user.id,
                        message_id=None,
                        draft_type=DraftType.POST.value,
                        content=evt["text"],
                    )
                    db.add(draft)
                    await db.flush()
                    yield sse_event(
                        "variant_done",
                        {"index": evt["index"], "name": evt["name"], "text": evt["text"], "draft_id": str(draft.id)},
                    )
                else:
                    await db.commit()
                    yield sse_event("all_done", {})
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", {"message": f"Variant generation failed: {exc}"})

    return EventSourceResponse(event_generator())


@router.get("/drafts", response_model=ApiResponse[list[dict]])
async def list_post_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GeneratedDraft)
        .where(GeneratedDraft.user_id == current_user.id, GeneratedDraft.draft_type == DraftType.POST.value)
        .order_by(GeneratedDraft.created_at.desc())
        .limit(50)
    )
    drafts = result.scalars().all()
    return ApiResponse.ok(
        [{"id": str(d.id), "content": d.content, "created_at": d.created_at.isoformat()} for d in drafts]
    )
