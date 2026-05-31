"""use mailbox_ids json and sender email for warmup_tasks

Revision ID: 2a9e1d2f24b2
Revises: 337172fb9b82
Create Date: 2026-05-31 14:31:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2a9e1d2f24b2"
down_revision: Union[str, None] = "337172fb9b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add mailbox_ids JSONB with empty list default
    op.add_column(
        "warmup_tasks",
        sa.Column(
            "mailbox_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # 2) Migrate old imap_mailbox_id into mailbox_ids for existing rows
    #    Each row becomes mailbox_ids = [imap_mailbox_id]
    op.execute(
        """
        UPDATE warmup_tasks
        SET mailbox_ids = CASE
            WHEN imap_mailbox_id IS NOT NULL
            THEN jsonb_build_array(imap_mailbox_id)
            ELSE '[]'::jsonb
        END
        """
    )

    # 3) Drop foreign key + imap_mailbox_id column if they still exist
    try:
        op.drop_constraint(
            "warmup_tasks_imap_mailbox_id_fkey",
            "warmup_tasks",
            type_="foreignkey",
        )
    except Exception:
        # If FK name differs or already dropped, ignore
        pass

    try:
        op.drop_column("warmup_tasks", "imap_mailbox_id")
    except Exception:
        # If column already dropped, ignore
        pass

    # 4) Change allowed_sender from boolean to text (email string), nullable
    #    Easiest is drop + re-add, keeping the column name.
    with op.batch_alter_table("warmup_tasks") as batch_op:
        try:
            batch_op.drop_column("allowed_sender")
        except Exception:
            pass

        batch_op.add_column(
            sa.Column("allowed_sender", sa.String(length=255), nullable=True)
        )


def downgrade() -> None:
    # 1) Recreate imap_mailbox_id column and FK (nullable, then fill from first id)
    op.add_column(
        "warmup_tasks",
        sa.Column("imap_mailbox_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "warmup_tasks_imap_mailbox_id_fkey",
        "warmup_tasks",
        "imap_mailboxes",
        ["imap_mailbox_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2) Migrate back: take first mailbox id from mailbox_ids array
    op.execute(
        """
        UPDATE warmup_tasks
        SET imap_mailbox_id = (mailbox_ids->>0)::integer
        WHERE jsonb_typeof(mailbox_ids) = 'array'
          AND jsonb_array_length(mailbox_ids) > 0
        """
    )

    # 3) Drop mailbox_ids column
    op.drop_column("warmup_tasks", "mailbox_ids")

    # 4) Change allowed_sender back to boolean NOT NULL DEFAULT false
    with op.batch_alter_table("warmup_tasks") as batch_op:
        try:
            batch_op.drop_column("allowed_sender")
        except Exception:
            pass
        batch_op.add_column(
            sa.Column(
                "allowed_sender",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )