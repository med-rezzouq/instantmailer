"""extend warmup_tasks and add warmup_task_mailboxes

Revision ID: 337172fb9b82
Revises: b878a0dea460
Create Date: 2026-05-31 13:16:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "337172fb9b82"
down_revision: Union[str, None] = "b878a0dea460"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) New boolean flags on warmup_tasks
    op.add_column(
        "warmup_tasks",
        sa.Column(
            "allowed_sender",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "warmup_tasks",
        sa.Column(
            "do_campaign_reply",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # 2) Join table for many-to-many between warmup_tasks and imap_mailboxes
    op.create_table(
        "warmup_task_mailboxes",
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
    )

    op.create_unique_constraint(
        "uq_warmup_task_mailboxes_task_mailbox",
        "warmup_task_mailboxes",
        ["warmup_task_id", "imap_mailbox_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_warmup_task_mailboxes_task_mailbox",
        "warmup_task_mailboxes",
        type_="unique",
    )
    op.drop_table("warmup_task_mailboxes")

    op.drop_column("warmup_tasks", "do_campaign_reply")
    op.drop_column("warmup_tasks", "allowed_sender")