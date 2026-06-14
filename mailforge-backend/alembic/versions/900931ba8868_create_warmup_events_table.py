"""create warmup_events table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "900931ba8868"
down_revision: Union[str, None] = "46de9c4b377b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'warmupaction'
            ) THEN
                CREATE TYPE warmupaction AS ENUM (
                    'open',
                    'move_to_inbox',
                    'add_to_favorites',
                    'add_to_contacts',
                    'reply'
                );
            END IF;
        END
        $$;
        """
    )

    warmup_action_enum = postgresql.ENUM(
        "open",
        "move_to_inbox",
        "add_to_favorites",
        "add_to_contacts",
        "reply",
        name="warmupaction",
        create_type=False,
    )

    op.create_table(
        "warmup_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "warmup_task_id",
            sa.Integer(),
            sa.ForeignKey("warmup_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mailbox_id",
            sa.Integer(),
            sa.ForeignKey("mailboxes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", warmup_action_enum, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_index(
        "ix_warmup_events_task_created_at",
        "warmup_events",
        ["warmup_task_id", "created_at"],
    )
    op.create_index(
        "ix_warmup_events_mailbox_created_at",
        "warmup_events",
        ["mailbox_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_warmup_events_mailbox_created_at", table_name="warmup_events")
    op.drop_index("ix_warmup_events_task_created_at", table_name="warmup_events")
    op.drop_table("warmup_events")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'warmupaction'
            ) THEN
                DROP TYPE warmupaction;
            END IF;
        END
        $$;
        """
    )