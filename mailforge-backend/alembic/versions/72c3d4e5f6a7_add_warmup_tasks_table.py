"""add warmup_tasks table

Revision ID: 72c3d4e5f6a7
Revises: 61b2c3d4e5f6
Create Date: 2026-05-30 23:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "72c3d4e5f6a7"          # <- keep Alembic's generated id
down_revision: Union[str, None] = "61b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "warmup_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("imap_mailbox_id", sa.Integer(), nullable=False),

        sa.Column("name", sa.String(length=255), nullable=False),

        sa.Column(
            "do_move_to_inbox",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "do_open",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "do_add_to_favorites",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "do_add_to_contacts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "do_reply",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("reply_message", sa.String(length=2000), nullable=True),

        sa.Column(
            "delay_seconds",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_warmup_tasks_user_mailbox",
        "warmup_tasks",
        ["user_id", "imap_mailbox_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_warmup_tasks_user_mailbox", table_name="warmup_tasks")
    op.drop_table("warmup_tasks")