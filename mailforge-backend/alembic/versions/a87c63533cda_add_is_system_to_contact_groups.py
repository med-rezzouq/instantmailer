"""add is_system to contact_groups

Revision ID: a87c63533cda
Revises: 41a8bc82e47a
Create Date: 2026-06-21 12:50:14.565258
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a87c63533cda"
down_revision: Union[str, Sequence[str], None] = "41a8bc82e47a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "contact_groups",
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_unique_constraint(
        "uq_contact_groups_user_name",
        "contact_groups",
        ["user_id", "name"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_contact_groups_user_name",
        "contact_groups",
        type_="unique",
    )

    op.drop_column("contact_groups", "is_system")