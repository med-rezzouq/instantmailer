"""add tracking_domains table

Revision ID: 4a1b2c3d4e5f
Revises: 3c83953ad4eb
Create Date: 2026-05-28 18:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4a1b2c3d4e5f"
down_revision: Union[str, None] = "3c83953ad4eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracking_domains",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "campaign_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_tracking_domains_id",
        "tracking_domains",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tracking_domains_id", table_name="tracking_domains")
    op.drop_table("tracking_domains")