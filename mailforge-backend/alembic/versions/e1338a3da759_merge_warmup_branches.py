"""merge warmup branches

Revision ID: <merge_id>
Revises: 2a9e1d2f24b2, fc6eaad3c37e
Create Date: 2026-05-31 14:41:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "<merge_id>"
down_revision: Union[str, Sequence[str], None] = ("2a9e1d2f24b2", "fc6eaad3c37e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No schema changes; this revision just merges two heads.
    pass


def downgrade() -> None:
    # Usually left as a no-op as well.
    pass