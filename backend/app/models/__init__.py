"""
Import every model module here so SQLAlchemy's mapper registry sees all
classes and Alembic autogenerate picks up the full schema.
"""

from app.models.connection import Connection
from app.models.draft import GeneratedDraft
from app.models.import_log import ImportLog
from app.models.job_opportunity import JobOpportunity, JobStatus
from app.models.message import Message, MessageCategory
from app.models.post import Post
from app.models.report import WeeklyReport
from app.models.user import User

__all__ = [
    "User",
    "Message",
    "MessageCategory",
    "Post",
    "Connection",
    "GeneratedDraft",
    "WeeklyReport",
    "ImportLog",
    "JobOpportunity",
    "JobStatus",
]
