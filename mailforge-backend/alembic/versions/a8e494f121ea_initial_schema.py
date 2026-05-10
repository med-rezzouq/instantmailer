"""initial schema

Revision ID: a8e494f121ea
Revises:
Create Date: 2026-05-09 02:50:14.013556
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a8e494f121ea"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # campaign_steps: nullable additions are safe
    op.add_column(
        "campaign_steps",
        sa.Column("wait_after_contact_reply_value", sa.Integer(), nullable=True),
    )
    op.add_column(
        "campaign_steps",
        sa.Column(
            "wait_after_contact_reply_unit",
            sa.Enum("seconds", "minutes", "hours", "days", name="delayunit"),
            nullable=True,
        ),
    )

    # campaigns: existing rows require server defaults first
    op.add_column(
        "campaigns",
        sa.Column(
            "general_warmup_delay_value",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "general_warmup_delay_unit",
            sa.Enum("seconds", "minutes", "hours", name="warmupdelayunit"),
            nullable=False,
            server_default="minutes",
        ),
    )

    # optional: remove defaults after backfilling existing rows
    op.alter_column("campaigns", "general_warmup_delay_value", server_default=None)
    op.alter_column("campaigns", "general_warmup_delay_unit", server_default=None)


def downgrade() -> None:
    op.drop_column("campaigns", "general_warmup_delay_unit")
    op.drop_column("campaigns", "general_warmup_delay_value")
    op.drop_column("campaign_steps", "wait_after_contact_reply_unit")
    op.drop_column("campaign_steps", "wait_after_contact_reply_value")