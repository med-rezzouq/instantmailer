"""add group_id to contacts

Revision ID: 3c83953ad4eb
Revises: ff79f752c8e8
Create Date: 2026-05-28 13:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c83953ad4eb"
down_revision: Union[str, Sequence[str], None] = "ff79f752c8e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add group_id FK to contacts and backfill."""
    # 1) Add nullable column first
    op.add_column(
        "contacts",
        sa.Column("group_id", sa.Integer, nullable=True),
    )

    # 2) Backfill existing rows with default value 1
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE contacts
            SET group_id = 1
            WHERE group_id IS NULL
            """
        )
    )

    # 3) Add FK constraint
    op.create_foreign_key(
        "fk_contacts_group_id_contact_groups",
        "contacts",
        "contact_groups",
        ["group_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 4) Make column NOT NULL
    op.alter_column("contacts", "group_id", nullable=False)


def downgrade() -> None:
    """Downgrade schema: drop group_id FK and column."""
    op.drop_constraint(
        "fk_contacts_group_id_contact_groups",
        "contacts",
        type_="foreignkey",
    )
    op.drop_column("contacts", "group_id")