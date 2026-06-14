"""make redirect_uri nullable on oauth_apps

Revision ID: a1b2c3d4e5f6
Revises: 9d8b7c6a5e4f
Create Date: 2026-06-06 23:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9d8b7c6a5e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "oauth_apps",
        "redirect_uri",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "oauth_apps",
        "redirect_uri",
        existing_type=sa.Text(),
        nullable=False,
    )