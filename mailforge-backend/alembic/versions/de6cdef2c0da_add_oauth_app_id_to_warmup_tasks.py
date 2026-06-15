"""add oauth_app_id to warmup_tasks

Revision ID: de6cdef2c0da
Revises: cfa2e15a460c
Create Date: 2026-06-15 17:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "de6cdef2c0da"
down_revision: Union[str, Sequence[str], None] = "cfa2e15a460c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "warmup_tasks",
        sa.Column("oauth_app_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_warmup_tasks_oauth_app_id_oauth_apps",
        "warmup_tasks",
        "oauth_apps",
        ["oauth_app_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_warmup_tasks_oauth_app_id_oauth_apps",
        "warmup_tasks",
        type_="foreignkey",
    )

    op.drop_column("warmup_tasks", "oauth_app_id")