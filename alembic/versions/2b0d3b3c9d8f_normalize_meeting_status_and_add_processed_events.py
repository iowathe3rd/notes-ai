"""normalize meeting status and add processed_events

Revision ID: 2b0d3b3c9d8f
Revises: 110a984160ab
Create Date: 2025-12-18

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2b0d3b3c9d8f"
down_revision: str | None = "110a984160ab"
branch_labels: str | None = None
depends_on: str | None = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Fix legacy typo: `meetings.stats` -> `meetings.status`
    meeting_cols = _column_names("meetings")
    if "stats" in meeting_cols and "status" not in meeting_cols:
        op.alter_column("meetings", "stats", new_column_name="status")

    # 2) Ensure enum type exists
    meeting_status_enum = postgresql.ENUM(
        "created",
        "queued",
        "processing",
        "done",
        "failed",
        name="meeting_status",
    )
    meeting_status_enum.create(bind, checkfirst=True)

    # 3) Cast `meetings.status` to enum if it is still text
    meeting_cols = _column_names("meetings")
    if "status" in meeting_cols:
        # We can't reliably introspect existing types across all backends here,
        # but in local dev this column started as TEXT. Casting again is safe only
        # if the column is TEXT, so guard via information_schema.
        current_type = bind.execute(
            sa.text(
                """
                select data_type, udt_name
                from information_schema.columns
                where table_schema = 'public'
                  and table_name = 'meetings'
                  and column_name = 'status'
                """
            )
        ).one()

        data_type, udt_name = current_type[0], current_type[1]
        is_text = data_type == "text"
        is_enum = data_type == "USER-DEFINED" and udt_name == "meeting_status"

        if is_text:
            # Postgres can't always cast the existing TEXT default to an ENUM
            # automatically, so drop it first, cast, then set the default again.
            op.execute(sa.text("alter table meetings alter column status drop default"))
            op.execute(
                sa.text(
                    "alter table meetings alter column status "
                    "type meeting_status using status::meeting_status"
                )
            )
            op.execute(
                sa.text(
                    "alter table meetings alter column status "
                    "set default 'created'::meeting_status"
                )
            )
        elif is_enum:
            # Ensure default is set consistently.
            op.alter_column(
                "meetings",
                "status",
                server_default=sa.text("'created'::meeting_status"),
            )

    # 4) Add processed_events table for consumer idempotency
    op.create_table(
        "processed_events",
        sa.Column("consumer_name", sa.Text(), nullable=False),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("consumer_name", "event_id"),
    )


def downgrade() -> None:
    op.drop_table("processed_events")

    # keep enum and column name changes in place; downgrading these safely is
    # non-trivial and not required for local MVP.
