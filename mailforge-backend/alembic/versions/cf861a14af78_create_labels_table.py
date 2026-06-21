"""create labels table

Revision ID: cf861a14af78
Revises: 204aefed40b6
Create Date: 2026-06-20 19:36:30.895339
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cf861a14af78"
down_revision: Union[str, Sequence[str], None] = "204aefed40b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_labels_id"), "labels", ["id"], unique=False)
    op.create_index(op.f("ix_labels_name"), "labels", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_labels_name"), table_name="labels")
    op.drop_index(op.f("ix_labels_id"), table_name="labels")
    op.drop_table("labels")