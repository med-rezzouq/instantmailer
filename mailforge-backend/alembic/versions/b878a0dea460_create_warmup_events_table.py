"""create warmup_events table

Revision ID: b878a0dea460
Revises: 88adddelayunit
Create Date: 2026-05-31 12:58:00.000000
"""

from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
import enum


# revision identifiers, used by Alembic.
revision: str = "b878a0dea460"
down_revision: Union[str, None] = "88adddelayunit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class WarmupAction(enum.Enum):
    open = "open"
    move_to_inbox = "move_to_inbox"
    add_to_favorites = "add_to_favorites"
    add_to_contacts = "add_to_contacts"
    reply = "reply"


def upgrade() -> None:
    warmup_action_enum = sa.Enum(
        "open",
        "move_to_inbox",
        "add_to_favorites",
        "add_to_contacts",
        "reply",
        name="warmupaction",
    )

    # REMOVE this line entirely:
    # warmup_action_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "warmup_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "warmup_task_id",
            sa.Integer,
            sa.ForeignKey("warmup_tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "imap_mailbox_id",
            sa.Integer,
            sa.ForeignKey("imap_mailboxes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("action", warmup_action_enum, nullable=False),
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
        ["imap_mailbox_id", "created_at"],
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