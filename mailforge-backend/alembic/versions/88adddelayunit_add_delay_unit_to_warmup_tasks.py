"""add delay_unit to warmup_tasks

Revision ID: 88adddelayunit
Revises: 72c3d4e5f6a7
Create Date: 2026-05-30 23:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "88adddelayunit"
down_revision: Union[str, None] = "72c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    warmup_delay_enum = sa.Enum(
        "seconds",
        "minutes",
        "hours",
        name="warmupdelayunit",
    )

    # Create enum type if not exists (safe if you rerun on dev)
    warmup_delay_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "warmup_tasks",
        sa.Column(
            "delay_unit",
            warmup_delay_enum,
            nullable=False,
            server_default="seconds",
        ),
    )


def downgrade() -> None:
    op.drop_column("warmup_tasks", "delay_unit")

    warmup_delay_enum = sa.Enum(
        "seconds",
        "minutes",
        "hours",
        name="warmupdelayunit",
    )
    warmup_delay_enum.drop(op.get_bind(), checkfirst=True)