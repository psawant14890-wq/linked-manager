"""
Feature: Connection Semantic Search

Embeds the text "name · title at company" for each connection on import,
then lets the user search their network in natural language:
"find me a connection at Google in ML" or "who do I know in fintech in London?"

The embedding captures both role semantics and company names, so the search
handles paraphrases, synonyms, and implied meanings rather than exact keyword
matching over name/company/title columns.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_client import embed_text, embed_texts
from app.models.connection import Connection


def _connection_text(conn: Connection) -> str:
    """Canonical text representation used for both indexing and querying."""
    parts = [conn.name]
    if conn.title:
        parts.append(conn.title)
    if conn.company:
        parts.append(f"at {conn.company}")
    return " · ".join(parts)


async def embed_and_attach_connections(db: AsyncSession, connections: list[Connection]) -> None:
    """
    Batch-embed a list of newly-imported Connection rows and store the vectors.
    Best-effort: called at end of import; failures are logged, not raised.
    """
    if not connections:
        return
    texts = [_connection_text(c) for c in connections]
    vectors = await embed_texts(texts)
    for conn, vector in zip(connections, vectors, strict=True):
        conn.embedding = vector
    await db.flush()


async def search_connections(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    query: str,
    top_k: int = 10,
) -> list[Connection]:
    """
    Embeds the natural-language `query` and returns the top_k connections
    ordered by cosine similarity. Connections without embeddings (edge case:
    import before this feature was added) are excluded automatically.
    """
    query_vector = await embed_text(query)

    stmt = (
        select(Connection)
        .where(Connection.user_id == user_id, Connection.embedding.is_not(None))
        .order_by(Connection.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
