"""add max_mailboxes to oauth_apps

Revision ID: 81836844b68b
Revises: ff1a59958170
Create Date: 2026-06-17 15:12:35.221514
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "81836844b68b"
down_revision: Union[str, Sequence[str], None] = "ff1a59958170"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "oauth_apps",
        sa.Column("max_mailboxes", sa.Integer(), nullable=True),
    )

    op.execute(
        "UPDATE oauth_apps SET max_mailboxes = 2 WHERE max_mailboxes IS NULL"
    )

    op.alter_column(
        "oauth_apps",
        "max_mailboxes",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("oauth_apps", "max_mailboxes")