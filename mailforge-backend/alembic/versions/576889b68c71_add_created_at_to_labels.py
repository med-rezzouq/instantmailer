"""add created_at to labels

Revision ID: 576889b68c71
Revises: cf861a14af78
Create Date: 2026-06-20 19:39:32.929372
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "576889b68c71"
down_revision: Union[str, Sequence[str], None] = "cf861a14af78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "labels",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_column("labels", "created_at")