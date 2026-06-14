"""add runid to warmup_events

Revision ID: 4d5fd4e641ce
Revises: df9a4f039af0
Create Date: 2026-06-14 16:58:00.917337
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d5fd4e641ce"
down_revision: Union[str, Sequence[str], None] = "df9a4f039af0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "warmup_events",
        sa.Column("runid", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("warmup_events", "runid")