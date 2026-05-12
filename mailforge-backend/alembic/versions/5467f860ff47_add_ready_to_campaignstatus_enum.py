"""add ready to campaignstatus enum

Revision ID: <new_revision_id>
Revises: a8e494f121ea
Create Date: 2026-05-10
"""

from typing import Sequence, Union

from alembic import op

revision: str = "<new_revision_id>"
down_revision: Union[str, Sequence[str], None] = "a8e494f121ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE campaignstatus ADD VALUE IF NOT EXISTS 'ready';")


def downgrade() -> None:
    # Optional: you can leave this empty; removing enum values is non-trivial
    pass