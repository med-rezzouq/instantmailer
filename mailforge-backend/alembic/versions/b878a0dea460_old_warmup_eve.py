"""create warmup_events table

Revision ID: b878a0dea460
Revises: 88adddelayunit
Create Date: 2026-05-31 12:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b878a0dea460"
down_revision: Union[str, None] = "88adddelayunit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    warmup_action_enum = sa.Enum(
        "open",
        "move_to_inbox",
        "add_to_favorites",
        "add_to_contacts",
        "reply",
        name="warmupaction",
    )

    op.create_table(
        "warmup_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "warmup_task_id",
            sa.Integer,
            sa.ForeignKey("warmup_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mailbox_id",
            sa.Integer,
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

    warmup_action_enum = sa.Enum(
        "open",
        "move_to_inbox",
        "add_to_favorites",
        "add_to_contacts",
        "reply",
        name="warmupaction",
    )
    warmup_action_enum.drop(op.get_bind(), checkfirst=True)