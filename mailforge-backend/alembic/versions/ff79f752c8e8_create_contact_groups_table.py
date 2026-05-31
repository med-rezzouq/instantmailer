"""create contact_groups table

Revision ID: ff79f752c8e8
Revises: c1ce25d918d4
Create Date: 2026-05-28 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff79f752c8e8"
down_revision: Union[str, Sequence[str], None] = "c1ce25d918d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create contact_groups and seed default."""
    op.create_table(
        "contact_groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    # Optional: seed a global Default group = 1 for user 1 (adjust if needed)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO contact_groups (id, name, user_id)
            VALUES (:id, :name, :user_id)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": 1, "name": "Default", "user_id": 1},
    )


def downgrade() -> None:
    """Downgrade schema: drop contact_groups."""
    op.drop_table("contact_groups")