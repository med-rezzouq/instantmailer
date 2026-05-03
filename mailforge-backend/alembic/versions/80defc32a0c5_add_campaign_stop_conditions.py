"""add campaign stop conditions

Revision ID: 80defc32a0c5
Revises:
Create Date: 2026-05-03 15:37:22.058861
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80defc32a0c5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("campaigns", sa.Column("max_bounces", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("max_complaints", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("max_unsubscribes", sa.Integer(), nullable=True))

    op.add_column("campaigns", sa.Column("stopped_by_condition", sa.Boolean(), nullable=True))
    op.execute(
        "UPDATE campaigns SET stopped_by_condition = false WHERE stopped_by_condition IS NULL"
    )
    op.alter_column("campaigns", "stopped_by_condition", nullable=False)

    op.add_column("campaigns", sa.Column("stop_reason", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaigns", "stop_reason")
    op.drop_column("campaigns", "stopped_by_condition")
    op.drop_column("campaigns", "max_unsubscribes")
    op.drop_column("campaigns", "max_complaints")
    op.drop_column("campaigns", "max_bounces")