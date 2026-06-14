"""add warmup event status detail target value"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "PUT_NEW_REVISION_ID_HERE"
down_revision: Union[str, Sequence[str], None] = "1af34ada75dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "warmup_events",
        sa.Column("status", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "warmup_events",
        sa.Column("detail", sa.Text(), nullable=True),
    )

    op.add_column(
        "warmup_events",
        sa.Column("target_value", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("warmup_events", "target_value")
    op.drop_column("warmup_events", "detail")
    op.drop_column("warmup_events", "status")