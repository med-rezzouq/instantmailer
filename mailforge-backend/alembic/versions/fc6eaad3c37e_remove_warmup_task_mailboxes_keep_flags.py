"""remove warmup_task_mailboxes keep flags

Revision ID: fc6eaad3c37e
Revises: 337172fb9b82
Create Date: 2026-05-31 14:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fc6eaad3c37e"
down_revision: Union[str, None] = "337172fb9b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraint and table if they still exist.
    # Order: drop constraint, then table.
    try:
        op.drop_constraint(
            "uq_warmup_task_mailboxes_task_mailbox",
            "warmup_task_mailboxes",
            type_="unique",
        )
    except Exception:
        # In case constraint is already gone in this DB
        pass

    try:
        op.drop_table("warmup_task_mailboxes")
    except Exception:
        # In case table is already gone
        pass

    # IMPORTANT: do NOT drop allowed_sender or do_campaign_reply here.
    # They are already added by 337172fb9b82 and used by the model/schemas.


def downgrade() -> None:
    # Recreate warmup_task_mailboxes table and its unique constraint
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