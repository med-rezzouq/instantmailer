"""add is_system to contacts

Revision ID: 357d62141f15
Revises: a87c63533cda
Create Date: 2026-06-21 13:26:44.743359
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "357d62141f15"
down_revision: Union[str, Sequence[str], None] = "a87c63533cda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "contacts",
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("contacts", "is_system")