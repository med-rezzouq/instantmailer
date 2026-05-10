"""add max_followups to campaigns

Revision ID: <new_revision_id>
Revises: a8e494f121ea
Create Date: 2026-05-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "<new_revision_id>"
down_revision: Union[str, Sequence[str], None] = "a8e494f121ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("max_followups", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "max_followups")