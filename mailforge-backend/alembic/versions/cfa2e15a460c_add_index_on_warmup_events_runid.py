"""add index on warmup_events.runid

Revision ID: cfa2e15a460c
Revises: 4d5fd4e641ce
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "cfa2e15a460c"
down_revision: Union[str, Sequence[str], None] = "4d5fd4e641ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_warmup_events_runid"),
        "warmup_events",
        ["runid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_warmup_events_runid"),
        table_name="warmup_events",
    )