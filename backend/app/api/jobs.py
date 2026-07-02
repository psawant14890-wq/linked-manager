import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.job_opportunity import JobOpportunity, JobStatus
from app.models.message import Message, MessageCategory
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.job_extractor import extract_job_opportunity

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobRead(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    sender_name: str | None = None
    company: str | None
    role_title: str | None
    seniority: str | None
    location: str | None
    remote_policy: str | None
    salary_range: str | None
    status: str
    notes: str | None
    extracted_at: datetime

    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    status: JobStatus


class JobNotesUpdate(BaseModel):
    notes: str


@router.post("/extract/{message_id}", response_model=ApiResponse[JobRead])
async def extract_from_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run GPT-4o extraction on a recruiter message and persist the result as a
    JobOpportunity row. Idempotent -- re-running returns the existing row
    (updated in place) rather than creating a duplicate.
    """
    msg_result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == current_user.id)
    )
    message = msg_result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if message.category != MessageCategory.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job extraction is only available for messages classified as 'recruiter'",
        )

    extraction = await extract_job_opportunity(sender_name=message.sender_name, content=message.content)

    if extraction is None or not extraction.is_genuine:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract a genuine job opportunity from this message",
        )

    # Upsert: update if already exists, insert if not
    existing_result = await db.execute(
        select(JobOpportunity).where(JobOpportunity.message_id == message_id)
    )
    job = existing_result.scalar_one_or_none()

    if job:
        job.company = extraction.company
        job.role_title = extraction.role_title
        job.seniority = extraction.seniority
        job.location = extraction.location
        job.remote_policy = extraction.remote_policy
        job.salary_range = extraction.salary_range
    else:
        job = JobOpportunity(
            user_id=current_user.id,
            message_id=message_id,
            company=extraction.company,
            role_title=extraction.role_title,
            seniority=extraction.seniority,
            location=extraction.location,
            remote_policy=extraction.remote_policy,
            salary_range=extraction.salary_range,
            status=JobStatus.NEW.value,
        )
        db.add(job)

    await db.commit()
    await db.refresh(job)

    read = JobRead.model_validate(job)
    read.sender_name = message.sender_name
    return ApiResponse.ok(read)


@router.get("", response_model=ApiResponse[list[JobRead]])
async def list_jobs(
    job_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobOpportunity).where(JobOpportunity.user_id == current_user.id)
    if job_status:
        stmt = stmt.where(JobOpportunity.status == job_status)
    stmt = stmt.order_by(JobOpportunity.extracted_at.desc())

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    reads = []
    for job in jobs:
        msg_res = await db.execute(select(Message).where(Message.id == job.message_id))
        msg = msg_res.scalar_one_or_none()
        r = JobRead.model_validate(job)
        r.sender_name = msg.sender_name if msg else None
        reads.append(r)

    return ApiResponse.ok(reads)


@router.patch("/{job_id}/status", response_model=ApiResponse[JobRead])
async def update_job_status(
    job_id: uuid.UUID,
    payload: JobStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobOpportunity).where(JobOpportunity.id == job_id, JobOpportunity.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.status = payload.status.value
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return ApiResponse.ok(JobRead.model_validate(job))


@router.patch("/{job_id}/notes", response_model=ApiResponse[JobRead])
async def update_job_notes(
    job_id: uuid.UUID,
    payload: JobNotesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobOpportunity).where(JobOpportunity.id == job_id, JobOpportunity.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.notes = payload.notes
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return ApiResponse.ok(JobRead.model_validate(job))
