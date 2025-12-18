"""create meetings and outbox_events

Revision ID: 110a984160ab
Revises: 
Create Date: 2025-12-18 16:41:31.674596

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '110a984160ab'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "meetings",
        sa.Column(
            "meeting_id", 
            postgresql.UUID(as_uuid=True),
            primary_key=True, 
            server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False
        ),
        sa.Column(
            "stats",
            sa.Text(),
            nullable=False,
            server_default="created"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        )
    )
    op.create_index(
        "ix_meetings_tenant_id",
        "meetings",
        ["tenant_id"]
    )
    op.create_table(
        "outbox_events",
        sa.Column(
            "outbox_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "event_type",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "aggregate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "publish_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["aggregate_id"],
            ["meetings.meeting_id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_outbox_events_unpublished",
        "outbox_events",
        ["published_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")

    op.drop_index("ix_meetings_tenant_id", table_name="meetings")
    op.drop_table("meetings")