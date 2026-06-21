"""add group_id to campaigns

Revision ID: 41a8bc82e47a
Revises: 4e9368347742
Create Date: 2026-06-21 01:16:03.410322
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "41a8bc82e47a"
down_revision: Union[str, Sequence[str], None] = "4e9368347742"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("group_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_campaigns_group_id",
        "campaigns",
        ["group_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_campaigns_group_id_contact_groups",
        "campaigns",
        "contact_groups",
        ["group_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_campaigns_group_id_contact_groups",
        "campaigns",
        type_="foreignkey",
    )
    op.drop_index("ix_campaigns_group_id", table_name="campaigns")
    op.drop_column("campaigns", "group_id")