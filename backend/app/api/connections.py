import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.connection_search import search_connections

router = APIRouter(prefix="/connections", tags=["connections"])


class ConnectionRead(BaseModel):
    id: uuid.UUID
    name: str
    company: str | None
    title: str | None
    connected_at: datetime | None

    class Config:
        from_attributes = True


@router.get("/search", response_model=ApiResponse[list[ConnectionRead]])
async def semantic_search(
    q: str = Query(..., min_length=2, description="Natural-language search query"),
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Natural-language search over the user's connections using pgvector
    cosine similarity. Try queries like:
      - "machine learning engineers at FAANG"
      - "VCs in fintech"
      - "design leaders in Europe"
    """
    results = await search_connections(db, user_id=current_user.id, query=q, top_k=limit)
    return ApiResponse.ok([ConnectionRead.model_validate(c) for c in results])
