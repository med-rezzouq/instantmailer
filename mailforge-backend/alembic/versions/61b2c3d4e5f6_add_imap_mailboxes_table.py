"""add imap_mailboxes table

Revision ID: 61b2c3d4e5f6
Revises: f9f27a30ca83
Create Date: 2026-05-30 22:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "61b2c3d4e5f6"
down_revision: Union[str, None] = "f9f27a30ca83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "imap_mailboxes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),

        sa.Column("imap_host", sa.String(length=255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"),
        sa.Column(
            "imap_ssl",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column("smtp_host", sa.String(length=255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column(
            "smtp_tls",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),

        sa.Column(
            "warmup_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_imap_mailboxes_user_email",
        "imap_mailboxes",
        ["user_id", "email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_imap_mailboxes_user_email", table_name="imap_mailboxes")
    op.drop_table("imap_mailboxes")