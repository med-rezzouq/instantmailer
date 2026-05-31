"""add campaign_trackings table and opens/clicks counters

Revision ID: 5f1a2b3c4d5e
Revises: 4a1b2c3d4e5f   # or 3c83953ad4eb if you skip the previous tracking_domains migration
Create Date: 2026-05-29 00:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f1a2b3c4d5e"
down_revision: Union[str, None] = "4a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) campaign_trackings table
    op.create_table(
        "campaign_trackings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            sa.Integer(),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("address_ip", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("browser", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_campaign_trackings_id",
        "campaign_trackings",
        ["id"],
        unique=False,
    )

    # 2) opens/clicks on campaigns (default 0)
    op.add_column(
        "campaigns",
        sa.Column(
            "opens",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "clicks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "clicks")
    op.drop_column("campaigns", "opens")
    op.drop_index("ix_campaign_trackings_id", table_name="campaign_trackings")
    op.drop_table("campaign_trackings")