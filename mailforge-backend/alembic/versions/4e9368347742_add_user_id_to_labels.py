"""add user_id to labels

Revision ID: 4e9368347742
Revises: 576889b68c71
Create Date: 2026-06-20 23:40:28.181811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4e9368347742"
down_revision: Union[str, Sequence[str], None] = "576889b68c71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "labels",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        op.f("ix_labels_user_id"),
        "labels",
        ["user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_labels_user_id_users",
        "labels",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_labels_user_id_users", "labels", type_="foreignkey")
    op.drop_index(op.f("ix_labels_user_id"), table_name="labels")
    op.drop_column("labels", "user_id")