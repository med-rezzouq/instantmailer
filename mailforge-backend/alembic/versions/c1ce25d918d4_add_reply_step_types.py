"""add reply step types

Revision ID: c1ce25d918d4
Revises: 01a476bae945
Create Date: 2026-05-17 21:04:33.705075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1ce25d918d4'
down_revision: Union[str, Sequence[str], None] = '01a476bae945'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.execute("ALTER TYPE steptype ADD VALUE IF NOT EXISTS 'reply'")
    op.execute("ALTER TYPE steptype ADD VALUE IF NOT EXISTS 'post_reply_followup'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
