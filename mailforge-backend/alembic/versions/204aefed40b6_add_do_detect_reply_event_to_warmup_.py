"""add do_detect_reply_event to warmup_tasks

Revision ID: 204aefed40b6
Revises: 81836844b68b
Create Date: 2026-06-20 19:11:26.747288
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "204aefed40b6"
down_revision: Union[str, Sequence[str], None] = "81836844b68b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "warmup_tasks",
        sa.Column(
            "do_detect_reply_event",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.execute(
        """
        UPDATE warmup_tasks
        SET do_detect_reply_event = false
        WHERE do_detect_reply_event IS NULL
        """
    )

    op.alter_column(
        "warmup_tasks",
        "do_detect_reply_event",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("warmup_tasks", "do_detect_reply_event")