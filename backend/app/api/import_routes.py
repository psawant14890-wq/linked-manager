import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.connection import Connection
from app.models.import_log import ImportLog
from app.models.message import Message
from app.models.post import Post
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.import_schema import ImportFileResult, ImportSummary
from app.services.connection_search import embed_and_attach_connections
from app.services.embeddings import embed_and_attach
from app.services.linkedin_parser import parse_upload

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/import", tags=["import"])


@router.post("", response_model=ApiResponse[ImportSummary])
async def import_linkedin_export(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not any(file.filename.lower().endswith(ext) for ext in settings.ALLOWED_UPLOAD_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}",
        )

    raw_bytes = await file.read()
    if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds max upload size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
        )

    parse_results = parse_upload(file.filename, raw_bytes)

    file_results: list[ImportFileResult] = []
    new_posts: list[Post] = []
    new_connections: list[Connection] = []
    total_messages = 0
    total_posts = 0
    total_connections = 0

    for pr in parse_results:
        for pm in pr.messages:
            db.add(
                Message(
                    user_id=current_user.id,
                    sender_name=pm.sender_name,
                    content=pm.content,
                    received_at=pm.received_at,
                )
            )
            total_messages += 1

        for pp in pr.posts:
            post = Post(user_id=current_user.id, content=pp.content, posted_at=pp.posted_at)
            db.add(post)
            new_posts.append(post)
            total_posts += 1

        for pc in pr.connections:
            conn = Connection(
                user_id=current_user.id,
                name=pc.name,
                company=pc.company,
                title=pc.title,
                connected_at=pc.connected_at,
            )
            db.add(conn)
            new_connections.append(conn)
            total_connections += 1

        db.add(
            ImportLog(
                user_id=current_user.id,
                filename=pr.filename,
                status=pr.status,
                rows_imported=pr.rows_imported,
                errors=json.dumps(pr.errors) if pr.errors else None,
            )
        )
        file_results.append(
            ImportFileResult(
                filename=pr.filename,
                status=pr.status,
                rows_imported=pr.rows_imported,
                errors=pr.errors,
            )
        )

    await db.flush()

    # Embed posts for style-matching RAG -- best-effort
    try:
        await embed_and_attach(db, new_posts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding posts failed, continuing: %s", exc)

    # Embed connections for semantic search -- best-effort
    try:
        await embed_and_attach_connections(db, new_connections)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding connections failed, continuing: %s", exc)

    await db.commit()

    return ApiResponse.ok(
        ImportSummary(
            files=file_results,
            total_messages_imported=total_messages,
            total_posts_imported=total_posts,
            total_connections_imported=total_connections,
        )
    )
