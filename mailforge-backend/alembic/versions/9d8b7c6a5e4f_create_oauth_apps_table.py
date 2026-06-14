"""create oauth_apps table

Revision ID: 9d8b7c6a5e4f
Revises: e1338a3da759
Create Date: 2026-06-06 21:50:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d8b7c6a5e4f"
down_revision: Union[str, None] = "e1338a3da759"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oauth_apps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("client_secret", sa.Text(), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_oauth_apps_id"), "oauth_apps", ["id"], unique=False)
    op.create_index(op.f("ix_oauth_apps_user_id"), "oauth_apps", ["user_id"], unique=False)
    op.create_index(op.f("ix_oauth_apps_provider"), "oauth_apps", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_oauth_apps_provider"), table_name="oauth_apps")
    op.drop_index(op.f("ix_oauth_apps_user_id"), table_name="oauth_apps")
    op.drop_index(op.f("ix_oauth_apps_id"), table_name="oauth_apps")
    op.drop_table("oauth_apps")