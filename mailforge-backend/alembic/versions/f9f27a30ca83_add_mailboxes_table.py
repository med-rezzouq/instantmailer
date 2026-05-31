"""add mailboxes table

Revision ID: f9f27a30ca83
Revises: 5f1a2b3c4d5e
Create Date: 2026-05-30 00:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9f27a30ca83"          # <- use the id Alembic generated
down_revision: Union[str, None] = "5f1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mailboxes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column(
            "warmup_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
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
        "ix_mailboxes_user_provider_email",
        "mailboxes",
        ["user_id", "provider", "email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_mailboxes_user_provider_email", table_name="mailboxes")
    op.drop_table("mailboxes")