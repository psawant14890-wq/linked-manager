"""add job opportunities, connection embeddings, message follow-up fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384  # matches 0001 -- see note there


def upgrade() -> None:
    # --- Feature: follow-up flagging (messages table) ---
    op.add_column("messages", sa.Column("is_actioned", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("messages", sa.Column("actioned_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_messages_is_actioned", "messages", ["is_actioned"])

    # --- Feature: connection semantic search (connections table) ---
    op.add_column("connections", sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True))
    op.execute(
        "CREATE INDEX ix_connections_embedding_cosine ON connections "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )

    # --- Feature: job opportunity tracker ---
    op.create_table(
        "job_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("role_title", sa.String(255), nullable=True),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote_policy", sa.String(50), nullable=True),
        sa.Column("salary_range", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_opportunities_user_id", "job_opportunities", ["user_id"])
    op.create_index("ix_job_opportunities_message_id", "job_opportunities", ["message_id"], unique=True)
    op.create_index("ix_job_opportunities_status", "job_opportunities", ["status"])


def downgrade() -> None:
    op.drop_table("job_opportunities")
    op.execute("DROP INDEX IF EXISTS ix_connections_embedding_cosine")
    op.drop_column("connections", "embedding")
    op.drop_index("ix_messages_is_actioned", table_name="messages")
    op.drop_column("messages", "actioned_at")
    op.drop_column("messages", "is_actioned")
