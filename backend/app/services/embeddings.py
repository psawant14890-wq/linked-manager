"""
Feature 3 support -- "RAG-lite" style retrieval.

Whenever the user generates a new post, we embed their raw input, then
pull the 2-3 most similar posts *from their own history* via pgvector
cosine distance. Those retrieved posts become few-shot examples that
anchor GPT-4o's tone/voice to how this specific person actually writes,
rather than generic LinkedIn-influencer voice.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_client import embed_text, embed_texts
from app.models.post import Post


async def embed_and_attach(db: AsyncSession, posts: list[Post]) -> None:
    """
    Batch-embeds a list of newly-imported Post rows and sets their
    embedding column in place. Called once at the end of the import
    pipeline for all posts pulled from Shares.csv.
    """
    if not posts:
        return
    vectors = await embed_texts([p.content for p in posts])
    for post, vector in zip(posts, vectors, strict=True):
        post.embedding = vector
    await db.flush()


async def retrieve_similar_posts(db: AsyncSession, *, user_id: uuid.UUID, query_text: str, top_k: int = 3) -> list[Post]:
    """
    Embeds `query_text` (the user's raw post input) and returns the
    top_k most similar past posts by this user, using pgvector's
    cosine-distance operator (`<=>`). Posts without an embedding (e.g.
    if OpenAI was unreachable during import) are excluded automatically
    since NULL embeddings don't participate in the distance ordering.
    """
    query_vector = await embed_text(query_text)

    stmt = (
        select(Post)
        .where(Post.user_id == user_id, Post.embedding.is_not(None))
        .order_by(Post.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
